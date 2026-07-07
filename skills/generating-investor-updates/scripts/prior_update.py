"""Fetch the prior investor update straight from Klaviyo (replaces the Kopi MCP read in step 3).

Usage:  python3 prior_update.py <MONTH>          # MONTH = YYYY-MM (the update being drafted)
Auth:   KLAVIYO_API_KEY (or KOPI_KLAVIYO_PRIVATE_KEY) in env — inject via claude-secrets.

Klaviyo is where the update was actually SENT, so it's the source of truth for both the prior
month's numbers (read from the email body) and the design/layout reference. Kopi still DRAFTS the
new email (step 5); this only supplies the prior one.

Finds the most recent campaign named like "Kopi AI Investor Update <Month> '<YY>" sent before the
target month (skipping clones/tests), then walks campaign -> campaign-message -> template to get
the HTML. Emits JSON: {name, send_time, campaign_id, klaviyo_url, html}. Emits {"status":"none"}
if no prior update exists (first-ever update) so the skill falls back to prompting for numbers.
"""
import os
import re
import sys
import json
import urllib.parse
import urllib.request
import urllib.error

REVISION = "2026-01-15"
NAME_RE = re.compile(r"investor update", re.I)
SKIP_RE = re.compile(r"clone|test|template", re.I)


def _key() -> str:
    return os.environ.get("KLAVIYO_API_KEY") or os.environ.get("KOPI_KLAVIYO_PRIVATE_KEY") or ""


def _get(path: str) -> dict:
    req = urllib.request.Request(
        "https://a.klaviyo.com/api/" + path,
        headers={"Authorization": "Klaviyo-API-Key " + _key(), "revision": REVISION, "accept": "application/json"},
    )
    try:
        return json.load(urllib.request.urlopen(req))
    except urllib.error.HTTPError as e:
        body = e.read()[:300].decode(errors="replace")
        raise SystemExit(json.dumps({"status": "error", "http": e.code, "body": body}))


def _campaign_html(cid: str) -> str:
    msgs = _get(f"campaigns/{cid}/campaign-messages/").get("data", [])
    if not msgs:
        return ""
    mid = msgs[0]["id"]
    inc = _get(f"campaign-messages/{urllib.parse.quote(mid)}/?include=template").get("included", [])
    tmpl = [i for i in inc if i.get("type") == "template"]
    return (tmpl[0]["attributes"].get("html") or "") if tmpl else ""


def main():
    if len(sys.argv) < 2:
        raise SystemExit(json.dumps({"status": "error", "body": "usage: prior_update.py YYYY-MM"}))
    if not _key():
        raise SystemExit(json.dumps({"status": "error", "body": "no KLAVIYO_API_KEY / KOPI_KLAVIYO_PRIVATE_KEY in env"}))
    cutoff = sys.argv[1][:7] + "-01"  # first day of the target month

    flt = urllib.parse.quote("equals(messages.channel,'email')")
    page = _get(f"campaigns/?filter={flt}&sort=-created_at&page%5Bsize%5D=50").get("data", [])
    for c in page:
        a = c.get("attributes", {})
        name = a.get("name", "")
        if not NAME_RE.search(name) or SKIP_RE.search(name):
            continue
        when = (a.get("send_time") or a.get("scheduled_at") or a.get("created_at") or "")[:10]
        if when and when >= cutoff:
            continue  # same-month or future; we want the PRIOR one
        html = _campaign_html(c["id"])
        print(json.dumps({
            "status": "ok",
            "name": name,
            "send_time": when,
            "campaign_id": c["id"],
            "klaviyo_url": f"https://www.klaviyo.com/campaign/{c['id']}/reports/overview",
            "html": html,
        }))
        return
    print(json.dumps({"status": "none", "reason": "no prior investor-update campaign before " + cutoff}))


if __name__ == "__main__":
    main()
