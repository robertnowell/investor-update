# Worked example (fictional)

A fictional seed-stage SaaS, "Northwind," to show the end-to-end flow. Numbers are illustrative.

## Inputs
- Financials (founder-entered): cash $410k · burn $28k/mo · runway ~15mo · revenue $2,100/mo
  ($1,800 SaaS), down from $3.4k last month.
- Compiled digest: GitHub = 47 merged PRs (themes: Onboarding 18, Billing 9, …); Slack signal =
  ~540 signup events, 90 deploy alerts; narrative from human channels.
- Prior update (via Kopi MCP `view_email`): last month's update → MoM source + design reference.

## The diamond (headline-only)
> 🚀 **Shipped self-serve onboarding** — signup → first value in <5 min (was ~2 days).
> 📈 **540 signups** (+22% MoM); first 3 paid conversions off the new flow.
> 🎯 **Next month:** 10 paying teams; instrument activation → paid funnel.
> 💰 **$410k cash · $28k burn · ~15mo runway · $2.1k rev ($1.8k SaaS)**
> 🙋 **Ask:** intros to seed-stage B2B founders drowning in [problem].

## Generated via Kopi
`Kopi:create_email` with `referenceEmailUrl` = the prior update, so Kopi keeps the investor-update
*layout* (financial row, headline cards, an Ask block) instead of a marketing one.

## Gotchas this surfaces (now in the guardrails)
- **Default Alive/Dead is computed.** At $2.1k revenue vs $28k burn, this is Default *Dead* — normal
  pre-seed; never stamp "Default Alive" to look good. (See `reference/good-update.md`.)
- **Subject drift.** A marketing-tuned brand may auto-generate a marketing subject with emoji; reset
  it to a clean investor subject ("Northwind — May 2026: $410k cash, ~15mo runway") before send.
- **Audience separation.** Send to investors only — never reuse the content for customer campaigns.

> The maintainer dogfoods this monthly on a real company; the real numbers stay private (this
> example is fictional on purpose).
