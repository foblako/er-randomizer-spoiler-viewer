"""Elden Ring Randomizer spoiler-log toolkit."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from er_randomizer.filters import BUILTIN_FILTERS, BuiltinFilter
from er_randomizer.parser import SpoilerLog, SpoilerParser
from er_randomizer.presets import CATEGORY_LABELS, PRESETS

__all__ = [
    "BUILTIN_FILTERS",
    "BuiltinFilter",
    "CATEGORY_LABELS",
    "PRESETS",
    "SpoilerLog",
    "SpoilerParser",
]

# Single source of truth: pyproject.toml. The hard-coded literal that used
# to live here drifted out of sync with the project version more than once.
try:
    __version__ = version("er-randomizer-spoiler-viewer")
except PackageNotFoundError:  # running from a checkout without `pip install -e .`
    __version__ = "0.0.0+local"
