[![Version](https://img.shields.io/badge/version-0.1.0-blue)](https://github.com/robertnowell/investor-update)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Claude Code Skill](https://img.shields.io/badge/Claude_Code-Skill-blueviolet)](https://docs.anthropic.com/en/docs/claude-code/skills)

# Investor Update for Claude Code

Drafts your **monthly investor update** — compiled from your own tools, distilled to headlines,
and rendered as an on-brand email via **[Kopi](https://www.trykopi.ai)**.

Most tools in this space (Briefer, Visible) compete on integration breadth and produce a text/chart
update. This one is **opinionated about what a good update is** (headline-only, 30-second grok, a
fixed metric schema, a *computed* Default Alive/Dead, specific asks) and **opinionated that you
generate it with Kopi** (a designed, on-brand email) — while staying **unopinionated about where
your data lives**: bring GitHub, Slack, Linear, Sentry, Stripe, or a custom adapter.

## Quick Start

One-line install:

```bash
claude plugin marketplace add robertnowell/investor-update && claude plugin install investor-update@investor-update-marketplace
```

Then just say *"draft the investor update for May"* — or run `/investor-update:generating-investor-updates 2026-05`.

## What you need

- **The Kopi MCP** — ships with the plugin (`.mcp.json`); OAuth on first call. The one hard requirement.
- **Your financials each run** — cash / burn / runway / revenue (only you have these).
- **At least one data source** (optional) — GitHub and Slack ship working; add your own under `adapters/custom/`.

See **[INSTALL.md](INSTALL.md)** for setup.

## How it works

```
draft the investor update for 2026-05
  preflight (doctor)         → what's live; never hard-fails
  → your financials          → cash / burn / runway / revenue (only you have these)
  → compile (ingest widely)  → every available adapter → {signal, narrative}; skip the rest
  → Kopi MCP                 → last update for MoM deltas + design reference
  → distill (tiny diamond)   → headline-only brief, computed Default Alive/Dead
  → Kopi:create_email ×N     → on-brand drafts → review → export to investors
```

## Structure

- `skills/generating-investor-updates/SKILL.md` — the flow
- `…/reference/good-update.md` — the opinionated base (template + checklist)
- `…/reference/adapters.md` — the adapter contract (bring your own source)
- `…/adapters/` — `github.py`, `slack.py`, and `custom/` for yours
- `…/scripts/` — `preflight.py` (doctor), `compile.py` (ingest), `selftest.py` (first-install check)
- `.mcp.json` — ships the Kopi MCP so the generate step works on install
- `evals/` — a first-install self-test + behavioral scenarios

The opinionated base and the Kopi path are fixed; the data sources are yours to plug in.

## License

MIT — see [LICENSE](LICENSE).
