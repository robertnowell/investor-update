# Install

## What you need
1. **Your financials each run** (cash / burn / runway / revenue) — entered when prompted. This is
   the only true requirement.
2. **How you'll deliver it** — pick one:
   - **Kopi (recommended)**: a Kopi account + the Kopi MCP connected renders the brief into an
     on-brand HTML email you can send from any platform. The plugin ships a `.mcp.json` pointing at
     the validated endpoint (`https://www.trykopi.ai/mcp`, OAuth-gated; first tool call triggers
     sign-in). Set your brand via `set_active_brand`.
   - **Plaintext (no Kopi)**: if you send from Gmail/Docs, the distilled brief is already the
     deliverable — the skill hands it to you as clean markdown. Nothing to install.
3. **At least one data source** (optional but recommended) — see the table below.

## Install the plugin
```bash
# local / dev:
claude --plugin-dir ./investor-update-plugin
# or add a marketplace and: /plugin install investor-update@<marketplace>
```
Then: `/reload-plugins`. Run the doctor any time:
`python3 ${CLAUDE_PLUGIN_ROOT}/skills/generating-investor-updates/scripts/preflight.py`

## Configure data sources (env vars)
Nothing here is required — unset sources are skipped, not failed.

| Source | Env | Notes |
|---|---|---|
| GitHub | `GITHUB_REPO=owner/repo` | Auth via `gh auth login` (uses `gh api`). |
| Slack  | `SLACK_TOKEN=xoxb-…` (or `SLACK_USER_TOKEN`) | Needs `channels:read` + `channels:history`. Optional: `SLACK_SIGNAL_PREFIXES=alerts-,sentry,github-alerts`, `SLACK_NO_JOIN=1`. |
| Granola | `GRANOLA_API_KEY=grn_…` | Personal API key: Granola → Settings → API → Create new key (non-expiring). Pulls the month's meeting summaries. Optional `GRANOLA_DENY_EMAILS=` / `GRANOLA_DENY_TITLE_KEYWORDS=` (comma lists) to skip your **own** personal meetings — set these in your shell profile, never in the repo. |
| Custom | per adapter (e.g. `LINEAR_API_KEY`) | Drop `adapters/custom/<name>.py` (see `adapters/custom/linear.py.example`). |

Store secrets however you like (env, `.env`, `claude-secrets`, your shell profile). The skill never logs them.

### Prior update (for month-over-month deltas)
The skill needs last month's numbers. In order of accessibility: **just tell it** when prompted (or
paste last month's update — works for everyone); **or** if your update lives in Kopi it reads it via
the MCP; **or** if you send updates as **Klaviyo campaigns**, set `KLAVIYO_API_KEY=pk_…` and it
auto-pulls the most recent one named like "…investor update…".

## Run
```
/generating-investor-updates 2026-05
```
or just say "draft the investor update for May." It will: preflight → ask your financials →
compile available sources → pull last month's numbers for MoM (asked, or from Kopi/Klaviyo if
configured) → distill to a headline-only brief → deliver it (draft via Kopi, or hand you the
plaintext brief) for you to review and send.

## First-run troubleshooting
- **GitHub source skipped** → set `GITHUB_REPO` and run `gh auth login`.
- **Slack source skipped** → set `SLACK_TOKEN`/`SLACK_USER_TOKEN` with the scopes above.
- **Granola source skipped** → set `GRANOLA_API_KEY` (a `grn_` key from Settings → API).
- **"Kopi tools not found"** → the Kopi MCP isn't connected. Either connect it (re-run
  `/reload-plugins`) or use the **plaintext** delivery path — the brief works without Kopi.
- Everything degrades gracefully: with zero sources you can still run on financials alone.
