#!/usr/bin/env python3
"""Sends 10 test messages (questions, orders, complaints, spam) to the n8n
webhook and checks the reply, the table row and the manager alert.

Usage:  python3 test_run.py [--url http://127.0.0.1:5678/webhook/support-inbox]
                            [--data-dir ./data] [--expect-classifier rules|ai]
Writes only to the demo data folder (data/), never to client systems.
"""
import argparse, csv, json, pathlib, sys, time, urllib.error, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent

CASES = [
    # id, channel, name, message, expected category, expected FAQ id (questions only)
    ("q1", "email", "Anna", "Hi, how long does delivery to Munich usually take?", "question", "shipping_time"),
    ("q2", "form", "Tom", "Can I return a jacket I bought last week? What's the process?", "question", "returns"),
    ("q3", "chat", "Jonas", "Hallo, kann ich mit PayPal bezahlen?", "question", "payment_methods"),
    ("o1", "email", "Maria", "Hi, I'd like to order 2 pairs of the Trail Pro boots in size 43, black.", "order", None),
    ("o2", "form", "Luca", "Please send me a quote for 15 units of the Summit backpack for our hiking club.", "order", None),
    ("o3", "chat", "Lena", "Guten Tag, ich möchte die Regenjacke in Größe M bestellen.", "order", None),
    ("c1", "email", "Peter", "My tent arrived damaged and the zipper is broken. This is unacceptable, I want a refund now!", "complaint", None),
    ("c2", "email", "Sofia", "Order #4471 still hasn't arrived after 3 weeks and no one answers my emails. Really disappointed.", "complaint", None),
    ("s1", "form", "SEO Pro", "Boost your store to the FIRST PAGE OF GOOGLE!!! Cheap SEO backlinks, click here: bit.ly/rank1", "spam", None),
    ("s2", "email", "Prize Team", "Congratulations, you have won a $5000 prize! Claim your crypto reward now at https://win-now.xyz", "spam", None),
]


def post(url, payload, wait_s=40):
    """POST JSON; retries 404 for a while because n8n registers webhooks a few seconds after start."""
    deadline = time.time() + wait_s
    while True:
        req = urllib.request.Request(url, data=json.dumps(payload).encode(), method="POST",
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.status, json.loads(r.read().decode() or "{}")
        except urllib.error.HTTPError as e:
            if e.code != 404 or time.time() > deadline:
                raise
            time.sleep(2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:5678/webhook/support-inbox")
    ap.add_argument("--data-dir", default=str(ROOT / "data"))
    ap.add_argument("--expect-classifier", choices=["rules", "ai", "any"], default="any")
    ap.add_argument("--delay", type=float, default=0.0, help="pause between messages (for screen recording)")
    a = ap.parse_args()
    data = pathlib.Path(a.data_dir)
    passed, rows = 0, []

    for cid, channel, name, msg, exp_cat, exp_faq in CASES:
        errors = []
        payload = {"test_id": cid, "channel": channel, "name": name,
                   "email": f"{name.split()[0].lower()}@example.com", "message": msg}
        try:
            status, res = post(a.url, payload)
        except Exception as e:  # noqa: BLE001
            status, res = 0, {}
            errors.append(f"request failed: {e}")
        if status and status != 200:
            errors.append(f"HTTP {status}")
        cat, tid = res.get("category"), res.get("ticket_id")
        if res:
            if cat != exp_cat:
                errors.append(f"category {cat!r} != {exp_cat!r}")
            if exp_faq and res.get("faq_id") != exp_faq:
                errors.append(f"faq {res.get('faq_id')!r} != {exp_faq!r}")
            want_esc = exp_cat == "complaint"
            if res.get("escalated") != want_esc:
                errors.append(f"escalated={res.get('escalated')} expected {want_esc}")
            reply = res.get("reply") or ""
            if exp_cat == "spam" and reply:
                errors.append("spam got a reply")
            if exp_cat != "spam" and ("AI assistant" not in reply or len(reply) < 80):
                errors.append("reply missing or without AI disclosure")
            clf = res.get("classifier", "")
            if a.expect_classifier == "rules" and clf != "rules":
                errors.append(f"classifier {clf!r}, expected rules")
            if a.expect_classifier == "ai" and not clf.startswith("ai:"):
                errors.append(f"classifier {clf!r}, expected ai")
            # table row
            time.sleep(0.2)
            with open(data / "tickets.csv", newline="", encoding="utf-8") as f:
                row = next((r for r in csv.DictReader(f) if r["ticket_id"] == tid), None)
            if not row:
                errors.append("no row in tickets.csv")
            elif row["category"] != exp_cat:
                errors.append(f"table category {row['category']!r}")
            # manager alert
            alerts_file = data / "manager_alerts.jsonl"
            alerted = alerts_file.exists() and any(
                json.loads(l).get("ticket_id") == tid for l in alerts_file.read_text().splitlines() if l.strip())
            if alerted != want_esc:
                errors.append(f"manager alert sent={alerted}, expected {want_esc}")
        ok = not errors
        passed += ok
        rows.append((cid, exp_cat, cat or "-", res.get("classifier", "-"), "PASS" if ok else "FAIL", "; ".join(errors)))
        if a.delay:
            time.sleep(a.delay)

    print(f"{'id':<4} {'expected':<10} {'got':<10} {'classifier':<26} result")
    for r in rows:
        print(f"{r[0]:<4} {r[1]:<10} {r[2]:<10} {r[3]:<26} {r[4]}  {r[5]}")
    print(f"\n{passed}/{len(CASES)} passed")
    sys.exit(0 if passed == len(CASES) else 1)


if __name__ == "__main__":
    main()
