"""GitHub adapter — merged PRs in the month, grouped into shipped themes.

Env:
  GITHUB_REPO   required, e.g. "owner/repo"
Auth: uses the `gh` CLI (run `gh auth login` once). Works with older gh via `gh api`.

Validated 2026-06-01: this pattern handles ~59 PRs/mo; titles are commonly prefix-tagged
(e.g. "[Promotions] ...") which makes clean theme buckets.
"""
import os
import re
import json
import collections
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _contract import Adapter, AdapterUnavailable


class GitHubAdapter(Adapter):
    name = "github"
    required_env = ("GITHUB_REPO",)

    def fetch(self, start: str, end: str) -> dict:
        repo = os.environ["GITHUB_REPO"]
        q = f"repo:{repo} is:pr is:merged merged:{start}..{end}"
        out = subprocess.run(
            ["gh", "api", "-X", "GET", "search/issues", "-f", f"q={q}", "-f", "per_page=100"],
            capture_output=True, text=True,
        )
        if out.returncode != 0:
            err = out.stderr.strip()
            if "gh auth" in err or "authentication" in err.lower():
                raise AdapterUnavailable("gh is not authenticated — run `gh auth login`")
            raise RuntimeError(err or "gh api search/issues failed")
        data = json.loads(out.stdout)
        items = data.get("items", [])
        themes: collections.Counter = collections.Counter()
        titles: list[str] = []
        for it in items:
            m = re.match(r"\s*\[([^\]]+)\]", it["title"])
            themes[m.group(1).strip() if m else "(untagged)"] += 1
            titles.append(it["title"].strip())
        signal = {"merged_prs": data.get("total_count", len(items))}
        signal.update({f"theme:{k}": v for k, v in themes.most_common()})
        return {"source": "github", "signal": signal, "narrative": titles[:60]}
