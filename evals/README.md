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
`expected_behavior`. Two groups:

*Wiring / degradation — does it work for a new user:*
- **happy-path** — full sources; checks headline-only output, MoM, computed Default Dead, no invented numbers.
- **zero-sources** — nothing configured; must degrade gracefully, not refuse.
- **kopi-missing** — the recommended dep absent; must offer the plaintext path, not fabricate an email.
- **byo-adapter-linear** — a different stack; custom adapter auto-discovered with no SKILL.md edits.

*Distillation quality — the part that actually fails (each supplies a fixed digest so the judge is deterministic):*
- **distill-signal-not-titles** — highlights must lead with the Granola business narrative, NOT GitHub PR-title jargon.
- **subject-not-marketing** — the subject stays investor-toned (metrics), never a marketing/emoji/"scaling fast" line.
- **audience-filter** — off-audience meetings (a credit pitch, an IP negotiation) are dropped even when they sound big.

Score each `expected_behavior` line pass/fail (LLM-judge or manual). A release ships only when all
seven pass on a clean `--plugin-dir` install. The distillation group encodes real dogfood bugs
(PR-title pattern-matching, marketing subject drift, an off-audience "credit pitch" surfaced as a win).

## 3. Live dogfood (the real signal)
The maintainer runs the skill on their own company every month (see
`skills/.../examples/kopi-may-2026.md`). That is the highest-fidelity eval: a real founder, real
numbers, a real send. Bugs found there (e.g. "Default Alive" miscomputed, subject drift) become
guardrails in `reference/good-update.md` and new lines in these scenarios.
