"""First-install self-test — "will this work for a brand-new user?"

Simulates a fresh user (no credentials), and checks the things that actually break a plugin on
someone else's machine. Run before publishing:  python3 scripts/selftest.py

Checks:
  1. SKILL.md frontmatter within limits (name <=64 lowercase/hyphen, description <=1024).
  2. preflight runs and exits 0 with NOTHING configured (no scary failure).
  3. compile runs with NOTHING configured -> valid JSON, all sources skipped, no crash.
  4. adapter discovery finds the shipped adapters and ignores .example files.
  5. portability lint: the PORTABLE files contain no author-machine leakage
     (absolute home paths, prod DB URLs, hardcoded brand IDs).
Exit code is nonzero if any check fails (CI-friendly).
"""
import os
import re
import sys
import json
import subprocess
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
fails: list[str] = []
def check(ok: bool, label: str, detail: str = ""):
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f" — {detail}" if detail and not ok else ""))
    if not ok:
        fails.append(label)

def run(args, env=None):
    e = {"PATH": os.environ.get("PATH", "")}  # deliberately minimal env = a fresh user
    if env:
        e.update(env)
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, env=e)

print("investor-update self-test (simulating a fresh user)\n")

# 1. frontmatter
fm = (SKILL / "SKILL.md").read_text().split("---")[1]
name = re.search(r"name:\s*(.+)", fm).group(1).strip()
desc = re.search(r"description:\s*(.+)", fm).group(1).strip()
check(len(name) <= 64 and re.fullmatch(r"[a-z0-9-]+", name) is not None, "frontmatter name valid", name)
check(0 < len(desc) <= 1024, "frontmatter description within 1024", f"{len(desc)} chars")

# 2. preflight, no creds
p = run([str(SKILL / "scripts" / "preflight.py")])
check(p.returncode == 0, "preflight exits 0 with nothing configured", p.stderr.strip())
check("0/2 data source" in p.stdout or "live" in p.stdout, "preflight reports source status", "")

# 3. compile, no creds
c = run([str(SKILL / "scripts" / "compile.py"), "2026-05"])
ok_json = False
try:
    d = json.loads(c.stdout)
    ok_json = isinstance(d.get("sources"), dict) and isinstance(d.get("skipped"), list)
except Exception as e:
    d = {}
    check(False, "compile emits valid JSON with nothing configured", str(e))
if ok_json:
    check(True, "compile emits valid JSON with nothing configured")
    check(d["sources"] == {} and len(d["skipped"]) >= 2,
          "all sources skipped (not crashed) when unconfigured", str(d.get("skipped")))

# 4. discovery
sys.path.insert(0, str(SKILL / "adapters"))
from _contract import discover  # noqa: E402
names = sorted(c.name for c in discover(SKILL / "adapters"))
check("github" in names and "slack" in names, "shipped adapters discovered", str(names))
check("linear" not in names, "*.example files are NOT loaded", str(names))

# 5. portability lint — only the files that must be portable
PORTABLE = [SKILL / "SKILL.md"] + \
           [f for f in (SKILL / "scripts").glob("*.py") if f.name != "selftest.py"] + \
           [f for f in (SKILL / "adapters").glob("*.py")]
LEAKS = {
    "absolute home path": re.compile(r"/Users/[a-z]+/"),
    "prod DB url env": re.compile(r"NEON_DB_URL"),
    "hardcoded brand id": re.compile(r"\b[A-Za-z0-9_-]{21}\b(?=.*brand)", re.I),
    # a real owner/repo baked in where a <owner/repo> placeholder belongs
    "hardcoded github repo": re.compile(r"GITHUB_REPO=(?!<|owner/repo\b)[\w.-]+/[\w.-]+"),
    # any real email address in shared code (example.* is fine; personal data must not ship)
    "personal email address": re.compile(r"[A-Za-z0-9._%+-]+@(?!example\.)[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
}
leak_hits = []
for f in PORTABLE:
    txt = f.read_text()
    for label, pat in LEAKS.items():
        if pat.search(txt):
            leak_hits.append(f"{f.name}: {label}")
check(not leak_hits, "no author-machine leakage in portable files", "; ".join(leak_hits))

print()
if fails:
    print(f"SELF-TEST FAILED: {len(fails)} check(s) — {', '.join(fails)}")
    sys.exit(1)
print("SELF-TEST PASSED — ready for a fresh install.")
