"""Display labels for parser category keys.

Used by the GUI to render section headers ("Великие Руны (7)") above
each block of entries. Built-in *filters* live in :mod:`er_randomizer.filters`;
user-saved filters live in :mod:`er_randomizer.user_presets`.

The legacy ``PRESETS`` mapping that previously lived here is kept as a
re-export (built from the same data) for backwards-compatibility with
external consumers — for example a script that imports
``from er_randomizer import PRESETS``.
"""

from __future__ import annotations

from er_randomizer.filters import BUILTIN_FILTERS, DEFAULT_FILTER

CATEGORY_LABELS: dict[str, str] = {
    "great_runes": "Великие Руны",
    "remembrances": "Воспоминания",
    "key_item_hints": "Подсказки ключевых предметов",
    "bell_bearing_hints": "Подсказки колокольчиков",
    "core_mechanics_hints": "Подсказки основных механик",
    "quest_item_hints": "Подсказки квестовых предметов",
    "boss_placements": "Размещения боссов",
    "miniboss_placements": "Размещения мини-боссов",
    "basic_placements": "Размещения обычных врагов",
    "gesture_placements": "Размещения жестов",
    "level_bgm_placements": "Размещения BGM",
    "starting_gifts": "Стартовые подарки",
    "spoilers": "Спойлеры",
}

# Backwards-compat re-export. New code should use BUILTIN_FILTERS directly.
DEFAULT_PRESET = DEFAULT_FILTER
PRESETS: dict[str, list[str]] = {f.name: list(f.keys) for f in BUILTIN_FILTERS}
