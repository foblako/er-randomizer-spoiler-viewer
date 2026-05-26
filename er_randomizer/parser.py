"""Parser for Elden Ring Randomizer spoiler logs.

The parser is section-driven: the log is split by `-- <section>` headers and
each section is parsed by a dedicated handler. Unknown sections are ignored.

The hint sections (key items / bell bearings / core mechanics / quest items)
provide a short `Item: In <region>` index. Right after parsing those, we
enrich each hint with the full record from the `-- Spoilers:` section so
consumers see *where exactly* an item lies, *how* to obtain it and *what*
it replaces — not just the region.

Several kinds of noise are stripped from raw fields before they reach the
GUI: enemy database IDs (``(#1042380850)``) embedded in placement names,
``(scaling X->Y)`` tails on replacement locations. They are not useful to
a human reader and — worse — IDs become part of preset fingerprints when
left in, polluting the user's saved data.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class HintEntry:
    """A single short location hint, e.g. `Godrick's Great Rune: In Limgrave`.

    Used internally during parsing as a fallback when a hint has no matching
    entry in the `-- Spoilers:` section. Public hint-derived categories on
    `SpoilerLog` always expose `SpoilerEntry` instances.
    """

    name: str
    location: str

    def as_text(self) -> str:
        return f"{self.name}: {self.location}"


@dataclass
class PlacementEntry:
    """A `Replacing X in A: Y from B` entry from boss/miniboss/basic placements."""

    original: str
    original_location: str
    replacement: str
    replacement_location: str
    raw: str

    def as_text(self) -> str:
        return self.raw


@dataclass
class ReplaceEntry:
    """A `Replacing X: Y` entry from gesture / BGM sections."""

    original: str
    replacement: str

    def as_text(self) -> str:
        return f"{self.original} → {self.replacement}"


@dataclass
class SpoilerEntry:
    """A full item-spoiler line, possibly with a `(cost: N)` tail and/or `Replaces X`."""

    item: str
    location: str
    description: str
    replaces: str | None
    cost: int | None
    raw: str

    def as_text(self) -> str:
        return self.raw


@dataclass
class SpoilerLog:
    """Parsed contents of a spoiler log."""

    great_runes: list[SpoilerEntry] = field(default_factory=list)
    remembrances: list[SpoilerEntry] = field(default_factory=list)
    key_item_hints: list[SpoilerEntry] = field(default_factory=list)
    bell_bearing_hints: list[SpoilerEntry] = field(default_factory=list)
    core_mechanics_hints: list[SpoilerEntry] = field(default_factory=list)
    quest_item_hints: list[SpoilerEntry] = field(default_factory=list)
    boss_placements: list[PlacementEntry] = field(default_factory=list)
    miniboss_placements: list[PlacementEntry] = field(default_factory=list)
    basic_placements: list[PlacementEntry] = field(default_factory=list)
    gesture_placements: list[ReplaceEntry] = field(default_factory=list)
    level_bgm_placements: list[ReplaceEntry] = field(default_factory=list)
    starting_gifts: list[ReplaceEntry] = field(default_factory=list)
    spoilers: list[SpoilerEntry] = field(default_factory=list)

    CATEGORY_KEYS: tuple[str, ...] = (
        "great_runes",
        "remembrances",
        "key_item_hints",
        "bell_bearing_hints",
        "core_mechanics_hints",
        "quest_item_hints",
        "boss_placements",
        "miniboss_placements",
        "basic_placements",
        "gesture_placements",
        "level_bgm_placements",
        "starting_gifts",
        "spoilers",
    )

    def get(self, key: str) -> list:
        if key not in self.CATEGORY_KEYS:
            raise KeyError(f"unknown category: {key!r}")
        return getattr(self, key)

    def counts(self) -> dict[str, int]:
        return {k: len(self.get(k)) for k in self.CATEGORY_KEYS}

    def items_for(self, keys: Iterable[str]) -> list[tuple[str, object]]:
        out: list[tuple[str, object]] = []
        for k in keys:
            for entry in self.get(k):
                out.append((k, entry))
        return out


_SECTION_HEADERS: dict[str, str | None] = {
    "-- Hints for key items:": "key_items",
    "-- Hints for bell bearings:": "bell_bearings",
    "-- Hints for core mechanics:": "core_mechanics",
    "-- Hints for quest items:": "quest_items",
    "-- End of hints": None,
    "-- Spoilers:": "spoilers",
    "-- End of item spoilers": None,
    "-- Boss placements": "bosses",
    "-- Miniboss placements": "minibosses",
    "-- Basic placements": "basic",
    "-- Gesture placements": "gestures",
    "-- Level BGM placements": "bgm",
}

_PLACEMENT_RE = re.compile(
    r"^Replacing (?P<orig>.+?) in (?P<orig_loc>.+?): (?P<repl>.+?) from (?P<repl_loc>.+)$"
)
_REPLACE_RE = re.compile(r"^Replacing (?P<orig>.+?): (?P<repl>.+)$")
_STARTING_GIFT_RE = re.compile(
    r"^Replacing starting gift (?P<orig>.+?): (?P<repl>.+)$"
)
_COST_RE = re.compile(r"^\s+\(cost:\s*(\d+)\)\s*$")
# Matches `(#1234567890)` or ` (# 1234567890)` style IDs inserted by the
# randomizer next to enemy names. They are seed-stable per enemy but
# ugly in the UI and would otherwise become part of preset fingerprints.
_ID_NOISE_RE = re.compile(r"\s*\(#\s*\d+\)")
# Matches the trailing ``(scaling 3->1)`` tail on replacement locations.
_SCALING_NOISE_RE = re.compile(r"\s*\(scaling [^)]*\)\s*$")


def _strip_id(value: str) -> str:
    return _ID_NOISE_RE.sub("", value).strip()


def _strip_scaling(value: str) -> str:
    return _SCALING_NOISE_RE.sub("", value).strip()


class SpoilerParser:
    """Parses an Elden Ring Randomizer spoiler log into a `SpoilerLog`."""

    def parse_text(self, text: str) -> SpoilerLog:
        log = SpoilerLog()
        section: str | None = None
        last_spoiler: SpoilerEntry | None = None
        pending: dict[str, list[HintEntry]] = {
            "key_items": [],
            "bell_bearings": [],
            "core_mechanics": [],
            "quest_items": [],
        }
        # `Replacing starting gift X: Y` lines live between sections and
        # outside any `--` header in the real logs. Match them at the
        # top level rather than inside a virtual section.

        for raw_line in text.splitlines():
            line = raw_line.rstrip()
            stripped = line.strip()

            if stripped in _SECTION_HEADERS:
                section = _SECTION_HEADERS[stripped]
                last_spoiler = None
                continue
            if stripped.startswith("-- "):
                section = None
                last_spoiler = None
                continue

            if section == "spoilers":
                cost_match = _COST_RE.match(line)
                if cost_match and last_spoiler is not None:
                    last_spoiler.cost = int(cost_match.group(1))
                    continue

            if not stripped:
                continue

            # Starting-gift lines live between sections and don't have a
            # `--` header. Match them anywhere outside known sections.
            if section is None:
                gift = _parse_starting_gift_line(stripped)
                if gift is not None:
                    log.starting_gifts.append(gift)
                    continue

            if section in pending:
                hint = _parse_hint_line(stripped)
                if hint is not None:
                    pending[section].append(hint)
                continue

            if section == "spoilers":
                spoiler = _parse_spoiler_line(stripped)
                if spoiler is None:
                    continue
                log.spoilers.append(spoiler)
                last_spoiler = spoiler
                if "Remembrance" in spoiler.item:
                    log.remembrances.append(spoiler)
                continue

            if section in {"bosses", "minibosses", "basic"}:
                placement = _parse_placement_line(stripped)
                if placement is None:
                    continue
                if section == "bosses":
                    log.boss_placements.append(placement)
                elif section == "minibosses":
                    log.miniboss_placements.append(placement)
                else:
                    log.basic_placements.append(placement)
                continue

            if section in {"gestures", "bgm"}:
                replace = _parse_replace_line(stripped)
                if replace is None:
                    continue
                if section == "gestures":
                    log.gesture_placements.append(replace)
                else:
                    log.level_bgm_placements.append(replace)
                continue

        _resolve_hints(log, pending)
        _dedupe_quest_item_hints(log)
        return log

    def parse_file(self, path: str | Path) -> SpoilerLog:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
        return self.parse_text(text)


def _parse_hint_line(line: str) -> HintEntry | None:
    if ":" not in line:
        return None
    name, _, location = line.partition(":")
    name = name.strip()
    location = location.strip()
    if not name or not location:
        return None
    return HintEntry(name=name, location=location)


def _parse_placement_line(line: str) -> PlacementEntry | None:
    match = _PLACEMENT_RE.match(line)
    if not match:
        return None
    # Strip enemy IDs from names (they pollute fingerprints) and
    # `(scaling X->Y)` from the replacement-location tail (it's an
    # internal balancing detail that doesn't help a human reader).
    return PlacementEntry(
        original=_strip_id(match["orig"]),
        original_location=match["orig_loc"].strip(),
        replacement=_strip_id(match["repl"]),
        replacement_location=_strip_scaling(_strip_id(match["repl_loc"])),
        raw=line,
    )


def _parse_replace_line(line: str) -> ReplaceEntry | None:
    match = _REPLACE_RE.match(line)
    if not match:
        return None
    return ReplaceEntry(original=match["orig"].strip(), replacement=match["repl"].strip())


def _parse_starting_gift_line(line: str) -> ReplaceEntry | None:
    match = _STARTING_GIFT_RE.match(line)
    if not match:
        return None
    return ReplaceEntry(
        original=match["orig"].strip(), replacement=match["repl"].strip()
    )


def _parse_spoiler_line(line: str) -> SpoilerEntry | None:
    if " in " not in line or ":" not in line:
        return None
    head, _, tail = line.partition(":")
    if " in " not in head:
        return None
    item, _, location = head.rpartition(" in ")
    item = item.strip()
    location = location.strip()
    description = tail.strip()
    replaces: str | None = None
    if "Replaces " in description:
        before, _, rep = description.rpartition("Replaces ")
        before = before.rstrip(" .")
        rep = rep.rstrip(".").strip()
        description = before
        replaces = rep
    if not item or not location:
        return None
    return SpoilerEntry(
        item=item,
        location=location,
        description=description,
        replaces=replaces,
        cost=None,
        raw=line,
    )


def _resolve_hints(log: SpoilerLog, pending: dict[str, list[HintEntry]]) -> None:
    """Enrich hint entries with full data from the spoilers section.

    For each hint, find a matching `SpoilerEntry` (item + location) and use
    it. If no match exists, synthesize a minimal `SpoilerEntry` from the hint
    so the GUI/consumers see a uniform record type for every category.
    """
    by_item: dict[str, list[SpoilerEntry]] = {}
    for s in log.spoilers:
        by_item.setdefault(s.item, []).append(s)

    used: set[int] = set()
    for section, hints in pending.items():
        for hint in hints:
            target_loc = hint.location.removeprefix("In ").strip()
            match: SpoilerEntry | None = None
            for cand in by_item.get(hint.name, []):
                if id(cand) in used:
                    continue
                if cand.location == target_loc:
                    match = cand
                    used.add(id(cand))
                    break
            if match is None:
                # Fallback: build a minimal spoiler entry from the hint alone.
                match = SpoilerEntry(
                    item=hint.name,
                    location=target_loc or hint.location,
                    description="",
                    replaces=None,
                    cost=None,
                    raw=hint.as_text(),
                )

            if section == "key_items":
                if "Great Rune" in hint.name and "Restored" not in hint.name:
                    log.great_runes.append(match)
                else:
                    log.key_item_hints.append(match)
            elif section == "bell_bearings":
                log.bell_bearing_hints.append(match)
            elif section == "core_mechanics":
                log.core_mechanics_hints.append(match)
            elif section == "quest_items":
                log.quest_item_hints.append(match)


def _dedupe_quest_item_hints(log: SpoilerLog) -> None:
    seen: set[tuple[str, str]] = set()
    deduped: list[SpoilerEntry] = []
    for entry in log.quest_item_hints:
        key = (entry.item, entry.location)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(entry)
    log.quest_item_hints = deduped
