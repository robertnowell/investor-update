"""Doctor: report runtime deps, the Kopi MCP requirement, and which data sources are live.

Run:  python3 preflight.py

Design: NEVER hard-fail. A new user with nothing configured should still get a clear,
non-scary report and be able to run with just financials. Exit code is always 0.
"""
import sys
import shutil
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL / "adapters"))
from _contract import discover  # noqa: E402


def have(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def main():
    print("investor-update — preflight\n")

    print("Runtime:")
    for cmd, why in (("python3", "required"), ("gh", "for the github source"), ("node", "optional")):
        print(f"  {'OK ' if have(cmd) else '-- '} {cmd:8} ({why})")

    print("\nKopi MCP (REQUIRED to generate the email):")
    print("  -> ensure the 'Kopi' MCP is connected in your client (tools like Kopi:create_email).")
    print("     This skill cannot probe it from here; if drafting fails, connect Kopi first.")

    print("\nData sources (any combination; financials are entered by you each run):")
    adapters = discover(SKILL / "adapters")
    live = 0
    for cls in adapters:
        ok = cls.available()
        live += int(ok)
        suffix = "" if ok else f"   ({cls.setup_hint()})"
        print(f"  {'OK ' if ok else '-- '} {cls.name}{suffix}")

    print(f"\n{live}/{len(adapters)} data source(s) live.")
    if live == 0:
        print("Note: you can still run with just financials, but enable >=1 source for a richer digest.")
    sys.exit(0)


if __name__ == "__main__":
    main()
