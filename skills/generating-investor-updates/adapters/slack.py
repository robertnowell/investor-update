"""Slack adapter — a month across public channels, split into two layers.

Env:
  SLACK_TOKEN            required (or SLACK_USER_TOKEN). Needs channels:read + channels:history.
  SLACK_SIGNAL_PREFIXES  optional, comma list. Channels matching -> counts only. Default below.
  SLACK_NO_JOIN          optional, "1" to skip auto-joining not-in-channel public channels.
  SLACK_NARRATIVE_CAP    optional, max lines kept per human channel (default 40).

"Ingest widely, crystallize to a tiny diamond": alert/bot channels become directional
COUNTS (e.g. 728 signups); human channels become NARRATIVE lines.

Validated 2026-06-01: bot/alert message payloads live in `attachments`, not `text` — read both.
"""
import os
import sys
import json
import time
import datetime
import calendar
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _contract import Adapter, AdapterUnavailable

DEFAULT_SIGNAL_PREFIXES = ("alerts-", "sentry", "github-alerts")


def _token() -> str:
    return os.environ.get("SLACK_TOKEN") or os.environ.get("SLACK_USER_TOKEN") or ""


class SlackAdapter(Adapter):
    name = "slack"
    # available() needs a token; we check both names here rather than via required_env.
    required_env = ()

    @classmethod
    def available(cls) -> bool:
        return bool(_token())

    @classmethod
    def setup_hint(cls) -> str:
        return "set SLACK_TOKEN (or SLACK_USER_TOKEN)"

    def _api(self, method: str, post: bool = False, **params):
        url = "https://slack.com/api/" + method
        headers = {"Authorization": "Bearer " + _token()}
        if post:
            data = urllib.parse.urlencode(params).encode()
            headers["Content-Type"] = "application/x-www-form-urlencoded"
            req = urllib.request.Request(url, data=data, headers=headers)
        else:
            req = urllib.request.Request(url + "?" + urllib.parse.urlencode(params), headers=headers)
        for _ in range(4):
            try:
                r = json.load(urllib.request.urlopen(req))
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    time.sleep(int(e.headers.get("Retry-After", "2"))); continue
                raise
            if r.get("error") == "ratelimited":
                time.sleep(2); continue
            return r
        return {"ok": False, "error": "ratelimited"}

    def fetch(self, start: str, end: str) -> dict:
        if not _token():
            raise AdapterUnavailable("no Slack token (SLACK_TOKEN / SLACK_USER_TOKEN)")
        y, m, d = (int(x) for x in start.split("-"))
        oldest = datetime.datetime(y, m, 1, tzinfo=datetime.timezone.utc).timestamp()
        nm = (datetime.datetime(y, m, 1) + datetime.timedelta(days=32)).replace(day=1)
        latest = nm.replace(tzinfo=datetime.timezone.utc).timestamp()

        prefixes = tuple(
            p for p in os.environ.get("SLACK_SIGNAL_PREFIXES", ",".join(DEFAULT_SIGNAL_PREFIXES)).split(",") if p
        )
        cap = int(os.environ.get("SLACK_NARRATIVE_CAP", "40"))
        no_join = bool(os.environ.get("SLACK_NO_JOIN"))

        auth = self._api("auth.test")
        if not auth.get("ok"):
            raise AdapterUnavailable(f"Slack auth failed: {auth.get('error')}")

        chans = self._api("conversations.list", types="public_channel", limit=1000,
                          exclude_archived="true").get("channels", [])
        signal: dict[str, int] = {}
        narrative: dict[str, list] = {}
        for c in chans:
            name = c["name"]
            is_signal = any(name.startswith(p) for p in prefixes)
            msgs, err = self._history(c["id"], oldest, latest, cap=0 if is_signal else cap, no_join=no_join)
            if msgs is None:
                continue
            if is_signal:
                if msgs:
                    signal[name] = len(msgs)
            else:
                lines = [t for t in (self._text(mm) for mm in msgs) if t][:cap]
                if lines:
                    narrative[name] = lines
        return {
            "source": "slack",
            "signal": dict(sorted(signal.items(), key=lambda kv: -kv[1])),
            "narrative": narrative,
        }

    def _text(self, mm: dict) -> str:
        t = (mm.get("text") or "").strip()
        for a in mm.get("attachments", []) or []:
            t += " " + (a.get("text") or a.get("fallback") or a.get("title") or "")
        return t.replace("\n", " ").strip()

    def _history(self, cid, oldest, latest, cap, no_join):
        msgs, cursor = [], None
        for _ in range(20):
            kw = dict(channel=cid, oldest=oldest, latest=latest, limit=200)
            if cursor:
                kw["cursor"] = cursor
            r = self._api("conversations.history", **kw)
            if r.get("error") == "not_in_channel":
                if no_join:
                    return None, "not_in_channel"
                self._api("conversations.join", post=True, channel=cid)
                r = self._api("conversations.history", **kw)
            if not r.get("ok"):
                return (msgs or None), r.get("error")
            msgs += r.get("messages", [])
            if cap and len(msgs) >= cap:
                return msgs[:cap], None
            cursor = r.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break
        return msgs, None
