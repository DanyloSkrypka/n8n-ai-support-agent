#!/usr/bin/env python3
"""Local stand-in for the Claude Messages API, used only to test the AI branch
of the workflow without a real key or cost. Listens on 127.0.0.1:8799."""
import json, sys, pathlib
from http.server import BaseHTTPRequestHandler, HTTPServer
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from test_run import CASES  # noqa: E402

class H(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        assert self.headers.get("x-api-key"), "missing key header"
        text = body["messages"][0]["content"]
        cat, faq = "question", None
        for _, _, _, msg, c, f in CASES:
            if msg in text:
                cat, faq = c, f
        out = {"category": cat, "confidence": 0.93, "faq_id": faq, "summary": "mock"}
        resp = {"id": "msg_mock", "type": "message", "role": "assistant", "model": body["model"],
                "stop_reason": "end_turn",
                "content": [{"type": "thinking", "thinking": ""}, {"type": "text", "text": json.dumps(out)}]}
        data = json.dumps(resp).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)
    def log_message(self, *a): pass

HTTPServer(("127.0.0.1", 8799), H).serve_forever()
