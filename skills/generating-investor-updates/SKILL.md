---
name: generating-investor-updates
description: Generates a concise monthly investor update for a startup. Compiles the month from the founder's own tools (GitHub PRs, Slack activity, or custom adapters), distills it to a headline-only brief, and uses Kopi to turn that brief into an on-brand HTML email template you can send from any email platform (Klaviyo, Mailchimp, etc.). Use when the user says "investor update", "monthly update", "draft the investor update", or names a month to recap.
---

# Generating investor updates

Compile widely → crystallize to a tiny diamond → deliver (draft via Kopi, or hand off as plaintext).
Opinionated about **what a good update is** (`reference/good-update.md`); unopinionated about where
the data lives (any adapter under `adapters/`) and how you send it (Kopi is the recommended default).

Read `reference/good-update.md` before distilling. To add or debug a data source, read
`reference/adapters.md`. Paths below use `${CLAUDE_PLUGIN_ROOT}`; the skill dir is
`${CLAUDE_PLUGIN_ROOT}/skills/generating-investor-updates`.

## 0. Preflight (first run)
Run the doctor — it reports deps + which sources are live and never hard-fails:
`python3 "${CLAUDE_PLUGIN_ROOT}/skills/generating-investor-updates/scripts/preflight.py"`
**What Kopi does (the payoff):** it turns the brief into an **on-brand HTML email
template you can send from any email platform** (Klaviyo, Mailchimp, etc.). It's the one hard
requirement — drafting needs a one-time Kopi sign-in. Everything up to the brief works without it;
if the `Kopi:` tools aren't available, tell the user to connect Kopi once (see INSTALL.md).

## 1. Inputs
- **Month** = `$ARGUMENTS` (e.g. `2026-05`); else default to the previous calendar month.
- **Financials** — only the founder has these. Prompt once for: cash in bank, monthly burn,
  runway (months), revenue (+ SaaS/service split), and any **asks**. Never invent; if a number
  is unknown carry `[confirm]` into the draft.

## 2. Compile (ingest widely)
```
python3 "${CLAUDE_PLUGIN_ROOT}/skills/generating-investor-updates/scripts/compile.py" <MONTH>
```
Runs every **configured** adapter; a source whose credential is missing is **skipped and reported,
not failed**. Configure sources via env (see INSTALL.md) — none is required:
- `github`  → `GITHUB_REPO=<owner/repo>` + `gh auth login`
- `slack`   → `SLACK_TOKEN` (or `SLACK_USER_TOKEN`), scopes `channels:read`,`channels:history`
- `granola` → `GRANOLA_API_KEY` (a `grn_` key); optional `GRANOLA_DENY_EMAILS` /
  `GRANOLA_DENY_TITLE_KEYWORDS` to skip your own personal meetings

Supply secrets **however you like** — a shell export, a `.env`, or a secret manager. On macOS with
`claude-secrets`, one convenient form (substitute your own repo + secret names):
```
GITHUB_REPO=<owner/repo> claude-secrets run \
  --inject GRANOLA_API_KEY=GRANOLA_API_KEY --inject SLACK_TOKEN=SLACK_TOKEN \
  -- python3 "${CLAUDE_PLUGIN_ROOT}/skills/generating-investor-updates/scripts/compile.py" <MONTH>
```
Output is `{ sources: {...}, skipped: [...] }` — `signal` = counts/deltas, `narrative` = raw lines.

## 3. Prior update (MoM deltas + a design reference)
You need last month's numbers to show month-over-month deltas, and ideally last month's layout as a
reference. Pick the **most accessible source that applies** — MoM always computes against the most
recent prior update:
- **Default — ask the founder** (works for everyone): request last month's headline figures (cash,
  burn, runway, MRR/revenue, customer count), or have them paste last month's update. No setup, no
  dependency. This is the fallback whenever the options below aren't configured.
- **If the update lives in Kopi**: `Kopi:set_active_brand` → `Kopi:view_email` the most recent
  investor update → read its numbers and keep its URL as the layout reference.
- **If it's sent as a Klaviyo campaign** (optional, needs `KLAVIYO_API_KEY`):
  ```
  KLAVIYO_API_KEY=<key> python3 "${CLAUDE_PLUGIN_ROOT}/skills/generating-investor-updates/scripts/prior_update.py" <MONTH>
  ```
  Returns `{name, send_time, klaviyo_url, html}` for the most recent campaign whose name contains
  "investor update", sent before `<MONTH>` (skips clones/tests). `{"status":"none"}` → fall back to
  asking the founder. Read the metrics from the `html` body; reuse the `html` as the layout reference.

## 4. Distill (the tiny diamond)
Per `reference/good-update.md`, write a concise **headline-only** founder-note brief:
a fixed metric row with MoM deltas, 2–3 highlights, an honest lowlight, this-month focus, and
1–3 **specific** asks. **Compute Default Alive/Dead** from burn vs revenue — never assume it.
30-second read.

**Highlights come from the Granola meeting summaries — that's where the business narrative lives.**
Read the `granola` source's `narrative` **bodies** (not the titles) and crystallize the customer /
revenue / product story from them. GitHub and Slack are **corroborating evidence only**: use them to
confirm a claimed ship actually landed ("did the thing we said we shipped actually ship?"), never as
the headline. PR titles and alert counts are internal fuel, not investor-legible highlights — a
reader (and the founder) will not know what "days_of_cover subscription split" means or care.

**Filter for THIS reader.** A substantive meeting can still be off-target for investors — an
Anthropic/vendor **credit pitch**, an IP or hiring **negotiation**, pure vendor **ops**. Distill the
story an investor needs and drop the rest, even when it sounds impressive. Biggest ≠ relevant.

## 5. Deliver
**Default (recommended) — draft via Kopi.** For each angle the founder wants (a few is plenty), call
`Kopi:create_email` with the brief; for layout, pass `referenceEmailUrl` = the prior update (a Kopi
draft URL if they have one), else steer with the prior update's `html` from step 3 so it keeps the
investor-update look (not a marketing one). Generation is async (~5–10 min); return the draft URLs +
the inbox URL. Kopi renders the brief into an on-brand HTML email sendable from any platform.

**Plaintext option (no Kopi).** If the founder sends from Gmail/Docs, the step-4 brief **is** the
deliverable — it's already headline-only. Hand it over as clean markdown/plaintext (metrics row +
short sections) and skip Kopi. Everything up to here works without Kopi.

## 6. Review & hand off
Verify every number traces to input and that no offer/metric was invented. **Subject line must stay
investor-toned** — if drafting via Kopi, its auto-subject often drifts to a marketing line (emoji,
"scaling fast"); reset it to a clean `{Company} — {Month}: {cash} cash · {runway}mo · {MRR} ({±}% MoM)`.
When sending, export to the **investor list only**, never customer/campaign lists.

## Guardrails
- Every figure traces to founder input or the compiled digest; mark unknowns `[confirm]`.
- Same metric schema every month; never silently rename/drop (the top trust-killer).
- Default Alive/Dead is **computed**, not assumed (see `reference/good-update.md`).
