# Install

## What you need
1. **A Kopi account + the Kopi MCP connected** — the one hard requirement (it's how the update is
   drafted). The plugin ships a `.mcp.json` pointing at the validated Kopi endpoint
   (`https://www.trykopi.ai/mcp`, OAuth-gated); the first tool call triggers OAuth sign-in.
   (Only change the URL if you run a self-hosted Kopi.)
2. **Your brand in Kopi** — resolved by name or created from your URL (`set_active_brand`).
3. **Your financials each run** (cash / burn / runway / revenue) — entered when prompted.
4. **At least one data source** (optional but recommended). GitHub and Slack ship working.

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
| Custom | per adapter (e.g. `LINEAR_API_KEY`) | Drop `adapters/custom/<name>.py` (see `adapters/custom/linear.py.example`). |

Store secrets however you like (env, `claude-secrets`, your shell profile). The skill never logs them.

## Run
```
/generating-investor-updates 2026-05
```
or just say "draft the investor update for May." It will: preflight → ask your financials →
compile available sources → pull last month's update from Kopi for MoM + design → distill to a
headline-only brief → draft a few angles via Kopi → hand you the draft URLs to review and export.

## First-run troubleshooting
- **"Kopi tools not found"** → the Kopi MCP isn't connected. Reconnect it; re-run `/reload-plugins`.
- **GitHub source skipped** → set `GITHUB_REPO` and run `gh auth login`.
- **Slack source skipped** → set `SLACK_TOKEN`/`SLACK_USER_TOKEN` with the scopes above.
- Everything except Kopi degrades gracefully: with zero sources you can still run on financials.
