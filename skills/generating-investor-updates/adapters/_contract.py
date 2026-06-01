"""Adapter contract for investor-update data sources.

Each adapter answers, for one month, with the same tiny shape:

    {
      "source":    "github",
      "signal":    { "merged_prs": 59, "theme:Promotions": 31 },  # counts/deltas (quantitative)
      "narrative": ["Shipped citation engine", "Compliance footer for agent emails"]  # lines (qualitative)
    }

Opinionated about the SHAPE (signal + narrative); unopinionated about the tool.
To add a source (Linear, Sentry, Stripe, a Google Sheet...), drop a file in this
directory or in custom/ that subclasses Adapter. It is auto-discovered — no SKILL.md edits.

A source whose credentials are missing is SKIPPED, never fatal (graceful degradation).
"""
from __future__ import annotations
import os
import abc
import importlib.util
import inspect
from pathlib import Path


class AdapterUnavailable(Exception):
    """Raised by fetch() when a required credential/tool is missing at run time."""


class Adapter(abc.ABC):
    name: str = "adapter"
    # Env var names this source needs. If any is unset -> available() is False -> skipped.
    required_env: tuple[str, ...] = ()

    @classmethod
    def available(cls) -> bool:
        return all(os.environ.get(v) for v in cls.required_env)

    @classmethod
    def setup_hint(cls) -> str:
        return ("set " + " and ".join(cls.required_env)) if cls.required_env else "no setup needed"

    @abc.abstractmethod
    def fetch(self, start: str, end: str) -> dict:
        """Return {"source","signal","narrative"} for the month [start, end] (ISO yyyy-mm-dd)."""


def discover(adapters_dir: Path) -> list[type[Adapter]]:
    """Find every Adapter subclass in adapters_dir and adapters_dir/custom."""
    found: dict[str, type[Adapter]] = {}
    for d in (adapters_dir, adapters_dir / "custom"):
        if not d.exists():
            continue
        for f in sorted(d.glob("*.py")):
            if f.name.startswith("_"):
                continue
            spec = importlib.util.spec_from_file_location(f.stem, f)
            if not spec or not spec.loader:
                continue
            mod = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(mod)
            except Exception as e:  # a broken custom adapter must not break discovery
                print(f"warning: adapter {f.name} failed to import: {e}")
                continue
            for _, obj in inspect.getmembers(mod, inspect.isclass):
                if issubclass(obj, Adapter) and obj is not Adapter:
                    found[obj.name] = obj
    return list(found.values())
