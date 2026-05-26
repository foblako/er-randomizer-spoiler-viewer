"""User-defined item presets persisted to ``~/.er_randomizer.json``.

A preset is a *list of fingerprints* — each fingerprint is a
``(category, name)`` pair identifying an item by category and bullet
name. Built up by the user across many searches in the GUI, saved as
a named bundle, recalled later as a single click. Stable across
spoiler logs because location (which differs per seed) is not part of
the key.

Storage format (under the ``"item_presets"`` key in the config)::

    {
        "Run #3 essentials": [
            ["great_runes", "Godrick's Great Rune"],
            ["spoilers",    "Scorpion Charm"],
            ...
        ],
        ...
    }

Two kinds of legacy data are migrated on load:

1. ``[category, name, location]`` 3-tuples from v0.4.0. Location is
   dropped because it's seed-specific and would prevent matching
   across logs.
2. Names containing enemy database IDs like
   ``"Bell Bearing Hunter (#1042380850)"`` from before the parser
   started stripping them. The ID tail is removed so the fingerprint
   matches entries produced by current parser versions.

Bad / malformed entries are silently dropped rather than raising; we
never want a corrupt config to wedge the GUI.
"""

from __future__ import annotations

import re

from er_randomizer.config import read_config, update_config

# Pre-cleanup pattern, kept private to user_presets so the parser remains
# the only "live" cleaner. Migrating saved data through the same pattern
# keeps cross-version fingerprints stable.
_LEGACY_ID_RE = re.compile(r"\s*\(#\s*\d+\)")

# Tuple form lives in code; on disk we serialise as a JSON list-of-lists
# (JSON has no native tuple). Round-trip is lossless.
Fingerprint = tuple[str, str]

# Visual marker prepended to user-preset names in the combobox.
USER_PREFIX = "★ "

_KEY = "item_presets"


def _coerce_fp(value: object) -> Fingerprint | None:
    """Normalise a single fingerprint from disk into ``(category, name)``.

    Accepts both the current 2-element form and the legacy 3-element
    form (where the third item was a location). Returns ``None`` if
    the shape is wrong. Strips legacy ``(#1234567890)`` ID tails from
    the name so old saves keep matching against the current parser.
    """

    if not isinstance(value, (list, tuple)):
        return None
    if len(value) not in (2, 3):
        return None
    if not all(isinstance(x, str) for x in value):
        return None
    cleaned_name = _LEGACY_ID_RE.sub("", value[1]).strip()
    if not cleaned_name:
        return None
    return (value[0], cleaned_name)


def _coerce_preset(value: object) -> list[Fingerprint] | None:
    """Take a raw value (from JSON or in-memory) and return a clean
    ``list[Fingerprint]`` with duplicates removed (legacy 3-tuples
    that differ only by location collapse into one). Returns ``None``
    if nothing usable was found so callers can drop the entry entirely.
    """

    if not isinstance(value, list):
        return None
    cleaned: list[Fingerprint] = []
    seen: set[Fingerprint] = set()
    for raw in value:
        fp = _coerce_fp(raw)
        if fp is None or fp in seen:
            continue
        seen.add(fp)
        cleaned.append(fp)
    return cleaned or None


def load_user_presets() -> dict[str, list[Fingerprint]]:
    """Read the user's item presets from disk. Returns ``{}`` if missing
    or malformed.
    """

    raw = read_config().get(_KEY)
    if not isinstance(raw, dict):
        return {}
    out: dict[str, list[Fingerprint]] = {}
    for name, value in raw.items():
        if not isinstance(name, str) or not name.strip():
            continue
        cleaned = _coerce_preset(value)
        if cleaned is not None:
            out[name] = cleaned
    return out


def save_user_preset(
    name: str, fingerprints: list[Fingerprint]
) -> dict[str, list[Fingerprint]]:
    """Add or overwrite a preset and persist the whole user-presets
    section. Raises :class:`ValueError` for empty names / empty selection.
    """

    name = name.strip()
    if not name:
        raise ValueError("Имя пресета не может быть пустым.")
    if not fingerprints:
        raise ValueError(
            "Сначала отметь хотя бы один предмет, потом сохраняй пресет."
        )

    presets = load_user_presets()
    # Normalise to tuples (in case the caller passed lists) and dedupe.
    seen: set[Fingerprint] = set()
    deduped: list[Fingerprint] = []
    for fp in fingerprints:
        norm = (fp[0], fp[1])
        if norm in seen:
            continue
        seen.add(norm)
        deduped.append(norm)
    presets[name] = deduped
    update_config(**{_KEY: {k: [list(fp) for fp in v] for k, v in presets.items()}})
    return presets


def delete_user_preset(name: str) -> dict[str, list[Fingerprint]]:
    """Remove a preset by name. No-op if it doesn't exist."""

    presets = load_user_presets()
    if name not in presets:
        return presets
    presets.pop(name)
    update_config(**{_KEY: {k: [list(fp) for fp in v] for k, v in presets.items()}})
    return presets
