# Evals — does it work for a new user?

Two layers. Run the static one in CI; run the behavioral one before any release and after
changing the flow.

## 1. Static self-test (automated, cheap)
Simulates a fresh user with nothing configured. CI gate.
```bash
python3 skills/generating-investor-updates/scripts/selftest.py
claude plugin validate .
```
Covers: frontmatter limits, preflight/compile graceful degradation, adapter discovery,
`.example` ignored, and a portability lint (no author-machine paths, prod DB URLs, or hardcoded
brand IDs in the portable files).

## 2. Behavioral scenarios (`scenarios.jsonl`)
Per Anthropic's eval-driven approach: drive a fresh Claude instance that has the plugin installed
(`claude --plugin-dir .`) through each scenario, then judge the transcript against
`expected_behavior`. Four scenarios target the things that break for new users:
- **happy-path** — full sources; checks headline-only output, MoM via MCP, computed Default Dead, no invented numbers.
- **zero-sources** — nothing configured; must degrade gracefully, not refuse.
- **kopi-missing** — the one hard dep absent; must stop cleanly and not fabricate an email.
- **byo-adapter-linear** — a different stack; custom adapter auto-discovered with no SKILL.md edits.

Score each `expected_behavior` line pass/fail (LLM-judge or manual). A release ships only when all
four pass on a clean `--plugin-dir` install.

## 3. Live dogfood (the real signal)
The maintainer runs the skill on their own company every month (see
`skills/.../examples/kopi-may-2026.md`). That is the highest-fidelity eval: a real founder, real
numbers, a real send. Bugs found there (e.g. "Default Alive" miscomputed, subject drift) become
guardrails in `reference/good-update.md` and new lines in these scenarios.
