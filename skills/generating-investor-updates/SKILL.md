---
name: generating-investor-updates
description: Generates a concise monthly investor update for a startup. Compiles the month from the founder's own tools (GitHub PRs, Slack activity, or custom adapters), distills it to a headline-only brief, and drafts it as an on-brand email via the Kopi MCP. Use when the user says "investor update", "monthly update", "draft the investor update", or names a month to recap.
---

# Generating investor updates

Compile widely → crystallize to a tiny diamond → draft via Kopi. Opinionated about **what a good
update is** (`reference/good-update.md`) and that you **draft it with Kopi**; unopinionated about
where the data lives (any adapter under `adapters/`).

Read `reference/good-update.md` before distilling. To add or debug a data source, read
`reference/adapters.md`. Paths below use `${CLAUDE_PLUGIN_ROOT}`; the skill dir is
`${CLAUDE_PLUGIN_ROOT}/skills/generating-investor-updates`.

## 0. Preflight (first run)
Run the doctor — it reports deps + which sources are live and never hard-fails:
`python3 "${CLAUDE_PLUGIN_ROOT}/skills/generating-investor-updates/scripts/preflight.py"`
The **one hard requirement is the Kopi MCP** (tools like `Kopi:create_email`). If those tools
aren't available, stop and have the user connect Kopi (see INSTALL.md).

## 1. Inputs
- **Month** = `$ARGUMENTS` (e.g. `2026-05`); else default to the previous calendar month.
- **Financials** — only the founder has these. Prompt once for: cash in bank, monthly burn,
  runway (months), revenue (+ SaaS/service split), and any **asks**. Never invent; if a number
  is unknown carry `[confirm]` into the draft.

## 2. Compile (ingest widely)
`python3 "${CLAUDE_PLUGIN_ROOT}/skills/generating-investor-updates/scripts/compile.py" <MONTH>`
Runs every configured adapter; missing-credential sources are **skipped and reported, not failed**.
Output is `{ sources: {github,slack,...}, skipped: [...] }` — `signal` = counts/deltas,
`narrative` = raw lines. (Enable sources via env — see INSTALL.md.)

## 3. Prior update via the Kopi MCP (MoM + design reference)
- `Kopi:set_active_brand` — resolve the founder's brand by name or URL.
- `Kopi:get_context` → recent emails; `Kopi:view_email` the most recent **investor update** →
  read its numbers (for month-over-month deltas) and keep its URL as the **design reference**.
  Everything goes through the MCP — no database access.

## 4. Distill (the tiny diamond)
Per `reference/good-update.md`, write a concise **headline-only** founder-note brief:
a fixed metric row with MoM deltas, 2–3 highlights crystallized from the digest (e.g. GitHub
themes + a Slack signal count), an honest lowlight, this-month focus, and 1–3 **specific** asks.
**Compute Default Alive/Dead** from burn vs revenue — never assume it. 30-second read.

## 5. Draft via Kopi
For each angle the founder wants (a few is plenty), call `Kopi:create_email` with the brief and
`referenceEmailUrl` = the prior update (keeps the investor-update layout instead of a marketing
one). Generation is async (~5–10 min). Return the draft URLs + the inbox URL.

## 6. Review & hand off
Open each draft; verify every number traces to input, and that no offer/metric was invented.
The auto-subject may drift to a marketing line — reset it to a clean investor subject. Export to
the **investor list only**, never customer/campaign lists.

## Guardrails
- Every figure traces to founder input or the compiled digest; mark unknowns `[confirm]`.
- Same metric schema every month; never silently rename/drop (the top trust-killer).
- Default Alive/Dead is **computed**, not assumed (see `reference/good-update.md`).
