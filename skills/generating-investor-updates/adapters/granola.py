"""Granola adapter — the month's meeting notes, distilled to narrative lines.

Env:
  GRANOLA_API_KEY            required. A Granola *personal* API key (Settings > API >
                             Create new key), prefix `grn_`. Non-expiring. Scoped to the
                             account that created it — generate it under the account whose
                             notes you want, not a different workspace/login.
  GRANOLA_DENY_EMAILS        optional, comma list. Skip any note that has an attendee with
                             one of these emails (case-insensitive). For recurring personal
                             meetings (therapist, etc.) that share your calendar.
  GRANOLA_DENY_TITLE_KEYWORDS optional, comma list. Skip any note whose title contains one
                             of these substrings (case-insensitive).
  GRANOLA_MEETING_CAP        optional, max notes kept as narrative (default 60).

Auth is a static bearer key, so unlike the desktop app there is no token rotation to manage;
store GRANOLA_API_KEY in your secret manager and inject it when running compile.py.

The public API (https://public-api.granola.ai/v1) only returns notes that have a generated
AI summary; still-processing or never-summarized notes don't appear. Transcript is frequently
null, so we distill from `summary_markdown`, never the raw transcript.

This is an explicit skip list, NOT a content classifier: notes matching the denylist are
dropped BEFORE their summaries ever enter the digest, so a personal meeting never transits
into the brief. Everything that survives is ingested widely and crystallized downstream.

Validated 2026-07-06: `grn_` key against public-api.granola.ai; list endpoint is newest-first
with {notes, cursor, hasMore}; note detail carries summary_markdown + attendees[{name,email}].
"""
import os
import sys
import json
import time
import urllib.parse
import urllib.request
import urllib.error
import gzip
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _contract import Adapter, AdapterUnavailable

BASE = "https://public-api.granola.ai/v1"

# Personal-meeting denylist. Seed YOUR OWN exclusions via the env vars below —
# NEVER hardcode personal data (someone's email, a private meeting name) in this shared file.
# Recommended: export GRANOLA_DENY_EMAILS / GRANOLA_DENY_TITLE_KEYWORDS in your shell profile so
# recurring personal meetings are filtered on every run. These defaults stay empty on purpose.
DEFAULT_DENY_EMAILS: tuple[str, ...] = ()
DEFAULT_DENY_TITLE_KEYWORDS: tuple[str, ...] = ()


def _csv(name: str) -> tuple[str, ...]:
    return tuple(p.strip().lower() for p in os.environ.get(name, "").split(",") if p.strip())


class GranolaAdapter(Adapter):
    name = "granola"
    required_env = ("GRANOLA_API_KEY",)

    def _get(self, path: str) -> dict:
        req = urllib.request.Request(
            BASE + path,
            headers={
                "Authorization": "Bearer " + os.environ["GRANOLA_API_KEY"],
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "User-Agent": "investor-update-granola/1.0",
            },
        )
        for _ in range(5):
            try:
                raw = urllib.request.urlopen(req).read()
                if raw[:2] == b"\x1f\x8b":
                    raw = gzip.decompress(raw)
                return json.loads(raw)
            except urllib.error.HTTPError as e:
                if e.code == 429:  # 25 req / 5s burst, 5 req/s sustained
                    time.sleep(int(e.headers.get("Retry-After", "2")))
                    continue
                if e.code in (401, 403):
                    raise AdapterUnavailable(f"Granola auth failed ({e.code}) — check GRANOLA_API_KEY")
                raise
        raise RuntimeError("Granola API rate-limited after retries")

    def fetch(self, start: str, end: str) -> dict:
        deny_emails = set(DEFAULT_DENY_EMAILS) | set(_csv("GRANOLA_DENY_EMAILS"))
        deny_titles = tuple(DEFAULT_DENY_TITLE_KEYWORDS) + _csv("GRANOLA_DENY_TITLE_KEYWORDS")
        cap = int(os.environ.get("GRANOLA_MEETING_CAP", "60"))

        # List is newest-first; page until we're clearly past the window's start.
        ids: list[str] = []
        cursor = None
        for _ in range(50):
            page = self._get("/notes?limit=100" + (f"&cursor={urllib.parse.quote(cursor)}" if cursor else ""))
            notes = page.get("notes", [])
            if not notes:
                break
            stop = False
            for n in notes:
                day = (n.get("created_at") or "")[:10]
                if not day:
                    continue
                if day < start:
                    stop = True
                    break
                if day <= end:
                    ids.append(n["id"])
            cursor = page.get("cursor")
            if stop or not page.get("hasMore") or not cursor:
                break

        narrative: list[str] = []
        kept = skipped = 0
        for nid in ids:
            d = self._get(f"/notes/{urllib.parse.quote(nid)}")
            title = (d.get("title") or "").strip()
            tl = title.lower()
            emails = {
                (a.get("email") or "").lower()
                for a in (d.get("attendees") or [])
                if a.get("email")
            }
            if (deny_emails & emails) or any(k in tl for k in deny_titles):
                skipped += 1
                continue
            summary = (d.get("summary_markdown") or d.get("summary_text") or "").strip()
            if not summary and not title:
                continue
            block = f"{title}" + (f"\n{summary}" if summary else "")
            narrative.append(block.strip())
            kept += 1
            if kept >= cap:
                break
            time.sleep(0.2)  # stay well under 5 req/s sustained

        signal = {"meetings": kept}
        if skipped:
            signal["meetings_skipped_denylist"] = skipped
        return {"source": "granola", "signal": signal, "narrative": narrative}
