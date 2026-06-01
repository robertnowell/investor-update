"""Ingest widely: run every AVAILABLE adapter for a month -> one merged digest (JSON to stdout).

Usage:  python3 compile.py 2026-05

Never hard-fails on a single source: a missing credential -> "skipped"; a runtime error ->
"skipped" with the error. The point is to gather whatever signal exists, then crystallize it
downstream (see reference/good-update.md). Financials are entered by the founder, not here.
"""
import sys
import json
import calendar
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL / "adapters"))
from _contract import discover, AdapterUnavailable  # noqa: E402


def month_bounds(ym: str):
    y, m = (int(x) for x in ym.split("-"))
    last = calendar.monthrange(y, m)[1]
    return f"{y:04d}-{m:02d}-01", f"{y:04d}-{m:02d}-{last:02d}"


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: compile.py YYYY-MM")
    ym = sys.argv[1]
    start, end = month_bounds(ym)
    digest = {"month": ym, "window": [start, end], "sources": {}, "skipped": []}
    for cls in discover(SKILL / "adapters"):
        if not cls.available():
            digest["skipped"].append({"source": cls.name, "reason": "not configured", "hint": cls.setup_hint()})
            continue
        try:
            digest["sources"][cls.name] = cls().fetch(start, end)
        except AdapterUnavailable as e:
            digest["skipped"].append({"source": cls.name, "reason": "unavailable", "detail": str(e)})
        except Exception as e:  # one bad source never sinks the run
            digest["skipped"].append({"source": cls.name, "reason": "error", "detail": str(e)})
    print(json.dumps(digest, indent=2))


if __name__ == "__main__":
    main()
