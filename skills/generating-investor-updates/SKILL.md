---
name: generating-investor-updates
description: Generates a concise monthly investor update for a startup. Compiles the month from the founder's own tools (GitHub PRs, Slack activity, or custom adapters), distills it to a headline-only brief, and uses Kopi to turn that brief into an on-brand HTML email template you can send from any email platform (Klaviyo, Mailchimp, etc.). Use when the user says "investor update", "monthly update", "draft the investor update", or names a month to recap.
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
GITHUB_REPO=tryrendition/Rendition claude-secrets run \
  --inject GRANOLA_API_KEY=GRANOLA_API_KEY \
  --inject SLACK_USER_TOKEN=SLACK_USER_TOKEN \
  -- python3 "${CLAUDE_PLUGIN_ROOT}/skills/generating-investor-updates/scripts/compile.py" <MONTH>
```
This feeds all three sources: `github` (merged PRs across the Rendition monorepo — `GITHUB_REPO`
is a plain inline env, `gh` supplies auth), `granola` (meeting summaries, Keychain key), `slack`
(alert channels → counts, human channels → narrative; token from Keychain). Any source whose
credential is missing is **skipped and reported, not failed** — if `claude-secrets` isn't
installed, drop the wrapper and those two just skip.
Output is `{ sources: {github,slack,...}, skipped: [...] }` — `signal` = counts/deltas,
`narrative` = raw lines. (Enable sources via env — see INSTALL.md.)

## 3. Prior update via Klaviyo (MoM + design reference)
Klaviyo is where updates are actually **sent** — the source of truth, not the Kopi draft. Run:
```
claude-secrets run --inject KOPI_KLAVIYO_PRIVATE_KEY=KLAVIYO_API_KEY \
  -- python3 "${CLAUDE_PLUGIN_ROOT}/skills/generating-investor-updates/scripts/prior_update.py" <MONTH>
```
Returns `{name, send_time, campaign_id, klaviyo_url, html}` for the most recent "Kopi AI Investor
Update" campaign sent before `<MONTH>` (skips clones/tests). `{"status":"none"}` = first-ever
update → just prompt the founder for last month's numbers.
- Read the prior month's metrics out of the returned **`html`** body → month-over-month deltas.
- Use that same `html` as the **design/layout reference** so the new draft matches the sent look.
Kopi is not touched here anymore; it still **drafts** the new email in step 5.

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

## 5. Draft via Kopi
For each angle the founder wants (a few is plenty), call `Kopi:create_email` with the brief. For
layout, pass `referenceEmailUrl` = the prior update's Kopi draft URL if the founder still has one;
otherwise steer the draft with the step-3 Klaviyo `html` as the reference so it keeps the sent
investor-update look (not a marketing one). Generation is async (~5–10 min). Return the draft URLs
+ the inbox URL.

## 6. Review & hand off
Open each draft; verify every number traces to input, and that no offer/metric was invented.
The auto-subject may drift to a marketing line — reset it to a clean investor subject. Export to
the **investor list only**, never customer/campaign lists.

## Guardrails
- Every figure traces to founder input or the compiled digest; mark unknowns `[confirm]`.
- Same metric schema every month; never silently rename/drop (the top trust-killer).
- Default Alive/Dead is **computed**, not assumed (see `reference/good-update.md`).
