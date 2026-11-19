#!/usr/bin/env python3
"""Builds workflow.json from the Code-node sources in src/ (dev tool).
Clients only need workflow.json."""
import json, pathlib, uuid

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
js = lambda name: (SRC / f"{name}.js").read_text()
nid = lambda name: str(uuid.uuid5(uuid.NAMESPACE_URL, "n8n-support-agent/" + name))

KB = "={{ $env.SUPPORT_KB_FILE || '/data/knowledge_base/faq.json' }}"
DATA = "{{ $env.SUPPORT_DATA_DIR || '/data/output' }}"

def node(name, type_, ver, pos, params, **extra):
    n = {"parameters": params, "id": nid(name), "name": name, "type": type_,
         "typeVersion": ver, "position": pos}
    n.update(extra)
    return n

def code(name, pos, src, **extra):
    return node(name, "n8n-nodes-base.code", 2, pos, {"jsCode": js(src)}, **extra)

def if_node(name, pos, expr):
    return node(name, "n8n-nodes-base.if", 2.2, pos, {
        "conditions": {
            "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "loose", "version": 2},
            "conditions": [{"id": nid(name + "-c"), "leftValue": expr, "rightValue": "",
                            "operator": {"type": "boolean", "operation": "true", "singleValue": True}}],
            "combinator": "and"},
        "looseTypeValidation": True, "options": {}})

def sticky(name, pos, w, h, text, color=None):
    p = {"content": text, "height": h, "width": w}
    if color: p["color"] = color
    return node(name, "n8n-nodes-base.stickyNote", 1, pos, p)

Y = 320
nodes = [
    sticky("Note: overview", [-40, -40], 820, 210,
           "## AI Support Agent (demo)\n**Customer message -> AI triage -> FAQ answer -> log -> manager alert**\n\n"
           "1. Webhook receives email / form / chat message\n2. Claude classifies: question, order, complaint, spam\n"
           "   (no `ANTHROPIC_API_KEY` -> free rules classifier)\n3. Reply is built only from the FAQ file\n"
           "4. Every ticket is appended to the table (CSV stub for Google Sheets)\n5. Complaints & unanswered questions -> manager", 6),
    sticky("Note: AI", [960, 20], 600, 110,
           "### AI classification\nKey comes from the `ANTHROPIC_API_KEY` env variable - never stored in the workflow.\n"
           "If the key is missing or the API fails, the ticket goes to the **Rules classifier** (error output).", 4),
    sticky("Note: outputs", [2160, 20], 720, 110,
           "### Outputs (swap stubs for client tools)\n- **Append to tickets.csv** -> Google Sheets / Airtable / CRM\n"
           "- **Notify manager** -> Telegram / Slack / Gmail\n- **Respond to customer** -> reply via email / chat API", 5),

    node("Incoming message", "n8n-nodes-base.webhook", 2, [0, Y], {
        "httpMethod": "POST", "path": "support-inbox", "responseMode": "responseNode",
        "options": {"allowedOrigins": "*"}}, webhookId=nid("webhook")),
    code("Normalize message", [200, Y], "normalize"),
    node("Load knowledge base", "n8n-nodes-base.readWriteFile", 1, [400, Y], {"fileSelector": KB, "options": {}}),
    node("Parse FAQ file", "n8n-nodes-base.extractFromFile", 1, [600, Y], {
        "operation": "fromJson", "binaryPropertyName": "data", "options": {}}),
    if_node("AI key set?", [800, Y], "={{ !!$env.ANTHROPIC_API_KEY }}"),
    code("Build AI request", [1000, Y - 130], "ai_request"),
    node("Claude classify", "n8n-nodes-base.httpRequest", 4.2, [1200, Y - 130], {
        "method": "POST",
        "url": "={{ ($env.AI_BASE_URL || 'https://api.anthropic.com') + '/v1/messages' }}",
        "sendHeaders": True,
        "headerParameters": {"parameters": [
            {"name": "x-api-key", "value": "={{ $env.ANTHROPIC_API_KEY }}"},
            {"name": "anthropic-version", "value": "2023-06-01"}]},
        "sendBody": True, "specifyBody": "json",
        "jsonBody": "={{ JSON.stringify($json.request) }}",
        "options": {"timeout": 60000}}, onError="continueErrorOutput"),
    code("Parse AI answer", [1400, Y - 130], "ai_parse", onError="continueErrorOutput"),
    code("Rules classifier", [1300, Y + 130], "rules"),
    code("Build reply", [1600, Y], "reply"),
    code("Format table row", [1800, Y], "csv_row"),
    node("Append to tickets.csv", "n8n-nodes-base.readWriteFile", 1, [2000, Y], {
        "operation": "write", "fileName": "=" + DATA + "/tickets.csv",
        "dataPropertyName": "data", "options": {"append": True}}),
    if_node("Needs a human?", [2200, Y], "={{ $('Build reply').first().json.escalate }}"),
    code("Build manager alert", [2400, Y - 130], "alert"),
    node("Notify manager", "n8n-nodes-base.readWriteFile", 1, [2600, Y - 130], {
        "operation": "write", "fileName": "=" + DATA + "/manager_alerts.jsonl",
        "dataPropertyName": "data", "options": {"append": True}}),
    node("Respond to customer", "n8n-nodes-base.respondToWebhook", 1.1, [2800, Y], {
        "respondWith": "json",
        "responseBody": "={{ JSON.stringify($('Build reply').first().json.response) }}",
        "options": {}}),
]

def link(*targets):
    return [[{"node": t, "type": "main", "index": 0} for t in out] for out in targets]

connections = {
    "Incoming message": {"main": link(["Normalize message"])},
    "Normalize message": {"main": link(["Load knowledge base"])},
    "Load knowledge base": {"main": link(["Parse FAQ file"])},
    "Parse FAQ file": {"main": link(["AI key set?"])},
    "AI key set?": {"main": link(["Build AI request"], ["Rules classifier"])},
    "Build AI request": {"main": link(["Claude classify"])},
    "Claude classify": {"main": link(["Parse AI answer"], ["Rules classifier"])},
    "Parse AI answer": {"main": link(["Build reply"], ["Rules classifier"])},
    "Rules classifier": {"main": link(["Build reply"])},
    "Build reply": {"main": link(["Format table row"])},
    "Format table row": {"main": link(["Append to tickets.csv"])},
    "Append to tickets.csv": {"main": link(["Needs a human?"])},
    "Needs a human?": {"main": link(["Build manager alert"], ["Respond to customer"])},
    "Build manager alert": {"main": link(["Notify manager"])},
    "Notify manager": {"main": link(["Respond to customer"])},
}

wf = {
    "id": "SupportAgent0001",
    "name": "AI Support Agent - triage, FAQ reply, log, escalate",
    "nodes": nodes,
    "connections": connections,
    "settings": {"executionOrder": "v1", "saveDataSuccessExecution": "all", "saveManualExecutions": True},
    "pinData": {},
    "meta": {"templateCredsSetupCompleted": True},
    "tags": [],
}
(ROOT / "workflow.json").write_text(json.dumps(wf, indent=2, ensure_ascii=False) + "\n")
print("workflow.json written:", len(nodes), "nodes")
