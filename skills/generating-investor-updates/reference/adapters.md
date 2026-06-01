# Data adapters — bring your own source

The skill is opinionated about *what to look for*, not *which tool*. Every source — shipped or
yours — is an adapter that answers, for one month, with the same tiny shape.

## The contract
```python
{
  "source":    "github",
  "signal":    { "merged_prs": 59, "theme:Promotions": 31 },   # counts/deltas -> metrics
  "narrative": ["Shipped citation engine", "Compliance footer"] # raw lines -> crystallize to story
}
```
- **signal** = the quantitative layer (counts, deltas). Numbers that become metric/headline fuel.
- **narrative** = the qualitative layer (a few raw lines) the model distills into highlights.

## What to look for (opinionated signal taxonomy)
Aim to cover, from whatever tools you have:
- **Financials** — cash, burn, runway, revenue. (Entered by the founder, not an adapter.)
- **Shipped / product velocity** — GitHub, Linear, Jira, Height.
- **Growth** — analytics, Stripe, a #signups channel.
- **Reliability** — Sentry, PagerDuty, an alerts channel.
- **Wins & lowlights** — Slack, Notion, standups.

## Write an adapter (zero SKILL.md edits)
Drop a file in `adapters/` or `adapters/custom/` that subclasses `Adapter`:
```python
from _contract import Adapter, AdapterUnavailable   # adapters/custom/ -> parent.parent

class MyAdapter(Adapter):
    name = "mysource"
    required_env = ("MYSOURCE_TOKEN",)               # missing -> SKIPPED, never fatal
    def fetch(self, start, end):                      # ISO yyyy-mm-dd, inclusive
        ...
        return {"source": "mysource", "signal": {...}, "narrative": [...]}
```
`scripts/compile.py` auto-discovers it. Files starting with `_` or ending `.example` are ignored.
See `adapters/custom/linear.py.example` for a complete Linear adapter.

## Conventions
- A missing credential makes the source **unavailable** (skipped + reported), never an error.
- Raise `AdapterUnavailable("set X")` from `fetch()` if a credential/tool is missing at run time.
- Keep `narrative` short (a cap per source) — the diamond is tiny; ingest widely, crystallize hard.
- Shipped reference adapters: `github.py` (merged PRs → themes), `slack.py` (alerts → counts,
  human channels → narrative).
