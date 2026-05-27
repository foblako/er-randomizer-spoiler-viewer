"""Pretty-printing helpers for parsed spoiler-log entries.

Each entry kind gets rendered into a small list of ``(tag, text)`` tuples.
The GUI feeds those into a ``tk.Text`` widget configured with matching tag
styles (bold item name, muted location, accent for replacements).

The rendering is intentionally label-light. Earlier the format was

::

    •  Godrick's Great Rune
          Где: Limgrave - Groveside Cave
          Как: Dropped by Beastman of Farum Azula
          Заменяет: Flamedrake Talisman

— readable but visually noisy: every entry repeated the same Russian
nouns. The new format drops the labels and lets typography (bold name,
dim location, arrow before "replaces") carry the meaning:

::

    Godrick's Great Rune
       Limgrave · Groveside Cave
       Beastman of Farum Azula  →  Flamedrake Talisman

Plain-text export keeps a slightly wordier shape so that copy-pasting
into chats / notes still reads naturally without colour.
"""

from __future__ import annotations

from collections.abc import Iterable

from er_randomizer.parser import PlacementEntry, ReplaceEntry, SpoilerEntry

# Tag names used by the GUI; keep in sync with `SpoilerViewerApp._configure_tags`.
TAG_NAME = "name"
TAG_LOCATION = "location"
TAG_DETAIL = "detail"
TAG_ARROW = "arrow"
TAG_PLAIN = "plain"
TAG_INDENT = "indent"

# Legacy aliases — kept for any external consumer that imported them.
TAG_BULLET = TAG_INDENT
TAG_LABEL = TAG_DETAIL
TAG_VALUE = TAG_DETAIL

_INDENT = "    "
_ARROW = "  →  "
_LOC_SEP = " · "


def format_entry(entry: object) -> list[tuple[str, str]]:
    """Render an entry as a list of (tag, text) chunks.

    Output always ends with a final newline plus a blank line so that
    consecutive entries breathe in the results panel. Empty fields are
    skipped — e.g. a hint with no spoiler match has no detail line.
    """

    if isinstance(entry, SpoilerEntry):
        return _format_spoiler(entry)
    if isinstance(entry, PlacementEntry):
        return _format_placement(entry)
    if isinstance(entry, ReplaceEntry):
        return _format_replace(entry)
    return [(TAG_NAME, str(entry)), (TAG_PLAIN, "\n\n")]


def entry_to_text(entry: object) -> str:
    """Plain-text rendering for clipboard / save-to-file.

    Uses Russian labels so the exported text is still self-explanatory
    without the typographic cues of the live GUI.
    """

    if isinstance(entry, SpoilerEntry):
        return _spoiler_to_text(entry)
    if isinstance(entry, PlacementEntry):
        return _placement_to_text(entry)
    if isinstance(entry, ReplaceEntry):
        return _replace_to_text(entry)
    return f"{entry}\n\n"


def entry_name(entry: object) -> str:
    """Return the human-readable primary identifier of an entry — the
    string we render in bold. For placement / replace entries that's the
    *replacement* (what you actually fight / see).
    """

    if isinstance(entry, SpoilerEntry):
        return entry.item
    if isinstance(entry, PlacementEntry):
        return entry.replacement
    if isinstance(entry, ReplaceEntry):
        return entry.replacement
    return str(entry)


def entry_location(entry: object) -> str:
    """Return the in-seed location where the entry resides.

    Used for the location line of the rendering only. *Not* part of the
    fingerprint — locations differ between seeds, so including them
    would prevent a filter built on one log from matching another.
    """

    if isinstance(entry, SpoilerEntry):
        return entry.location
    if isinstance(entry, PlacementEntry):
        return entry.original_location
    return ""


def entry_fingerprint(category: str, entry: object) -> tuple[str, str]:
    """Stable cross-seed identifier — ``(category, name)``.

    Crucially we *do not* include the location: the same Godrick's Great
    Rune lives in a different cave every seed, so location-bound
    fingerprints would make filters useless across logs.

    Side-effect: clicking any row representing item X toggles every
    occurrence of X in the same category. For multi-instance items
    (e.g. four Scorpion Charms) that's the right behaviour — "in my
    filter I want Scorpion Charm" is the natural reading; "only this
    *specific* Scorpion Charm out of four" was never a concrete user
    request.
    """

    return (category, entry_name(entry))


def entry_searchable(entry: object) -> str:
    """Flat lower-cased haystack for substring search."""

    if isinstance(entry, SpoilerEntry):
        parts = [entry.item, entry.location, entry.description, entry.replaces or ""]
        return " ".join(p for p in parts if p).lower()
    if isinstance(entry, PlacementEntry):
        return " ".join(
            [
                entry.original,
                entry.original_location,
                entry.replacement,
                entry.replacement_location,
            ]
        ).lower()
    if isinstance(entry, ReplaceEntry):
        return f"{entry.original} {entry.replacement}".lower()
    return str(entry).lower()


# ---- private renderers (GUI-tagged) --------------------------------------


def _normalise_location(loc: str) -> str:
    """Tidy up locations like "Limgrave - Groveside Cave" into
    "Limgrave · Groveside Cave" — the middle dot reads better than a
    hyphen and matches the typographic style of the rest of the line.
    """

    if not loc:
        return ""
    return loc.replace(" - ", _LOC_SEP)


def _format_spoiler(entry: SpoilerEntry) -> list[tuple[str, str]]:
    parts: list[tuple[str, str]] = [
        (TAG_NAME, entry.item),
        (TAG_PLAIN, "\n"),
    ]
    location = _normalise_location(entry.location)
    if location:
        parts.append((TAG_INDENT, _INDENT))
        parts.append((TAG_LOCATION, location))
        parts.append((TAG_PLAIN, "\n"))

    description = (entry.description or "").rstrip(" .")
    detail_pieces: list[tuple[str, str]] = []
    if description:
        detail_pieces.append((TAG_DETAIL, description))
    if entry.replaces:
        if detail_pieces:
            detail_pieces.append((TAG_ARROW, _ARROW))
        else:
            detail_pieces.append((TAG_ARROW, "→ "))
        detail_pieces.append((TAG_DETAIL, entry.replaces))
    if entry.cost is not None:
        if detail_pieces:
            detail_pieces.append((TAG_DETAIL, f"   ({entry.cost} рун)"))
        else:
            detail_pieces.append((TAG_DETAIL, f"{entry.cost} рун"))
    if detail_pieces:
        parts.append((TAG_INDENT, _INDENT))
        parts.extend(detail_pieces)
        parts.append((TAG_PLAIN, "\n"))

    parts.append((TAG_PLAIN, "\n"))
    return parts


def _format_placement(entry: PlacementEntry) -> list[tuple[str, str]]:
    """Render a boss/miniboss/basic placement.

    Main line: ``original  →  replacement`` — the direction of the swap
    is immediately obvious: vanilla boss on the left, seed boss on the
    right. The replacement (who you fight) is bold; the original is
    rendered in the detail/muted style so the eye lands on the new name
    first but the vanilla context is right there.
    """

    parts: list[tuple[str, str]] = []
    parts.append((TAG_NAME, entry.replacement))
    if entry.original:
        parts.append((TAG_ARROW, _ARROW))
        parts.append((TAG_DETAIL, entry.original))
    parts.append((TAG_PLAIN, "\n"))

    # Location line: slot location  ←  source location of the replacement.
    # The ← arrow (styled as accent) visually marks "the replacement came FROM here".
    location = _normalise_location(entry.original_location)
    repl_loc = _normalise_location(entry.replacement_location)
    if location or repl_loc:
        parts.append((TAG_INDENT, _INDENT))
        if location:
            parts.append((TAG_LOCATION, location))
        if location and repl_loc:
            parts.append((TAG_ARROW, "  ←  "))
        if repl_loc:
            parts.append((TAG_LOCATION, repl_loc))
        parts.append((TAG_PLAIN, "\n"))

    parts.append((TAG_PLAIN, "\n"))
    return parts


def _format_replace(entry: ReplaceEntry) -> list[tuple[str, str]]:
    """Render a gesture / BGM / starting-gift swap. Compact two-line block:
    bold replacement, then an indented "заменил {original}" line.
    """

    parts: list[tuple[str, str]] = [
        (TAG_NAME, entry.replacement),
        (TAG_PLAIN, "\n"),
    ]
    if entry.original:
        parts.append((TAG_INDENT, _INDENT))
        parts.append((TAG_DETAIL, "заменил "))
        parts.append((TAG_NAME, entry.original))
        parts.append((TAG_PLAIN, "\n"))
    parts.append((TAG_PLAIN, "\n"))
    return parts


# ---- private renderers (plain text export) -------------------------------


def _spoiler_to_text(entry: SpoilerEntry) -> str:
    lines = [entry.item]
    location = _normalise_location(entry.location)
    if location:
        lines.append(f"  Где: {location}")
    description = (entry.description or "").rstrip(" .")
    if description:
        lines.append(f"  Как: {description}")
    if entry.replaces:
        lines.append(f"  Заменяет: {entry.replaces}")
    if entry.cost is not None:
        lines.append(f"  Стоимость: {entry.cost}")
    return "\n".join(lines) + "\n\n"


def _placement_to_text(entry: PlacementEntry) -> str:
    if entry.original:
        lines = [f"{entry.replacement}  →  {entry.original}"]
    else:
        lines = [entry.replacement]
    location = _normalise_location(entry.original_location)
    repl_loc = _normalise_location(entry.replacement_location)
    if location and repl_loc:
        lines.append(f"  {location}  ←  {repl_loc}")
    elif location:
        lines.append(f"  {location}")
    elif repl_loc:
        lines.append(f"  {repl_loc}")
    return "\n".join(lines) + "\n\n"


def _replace_to_text(entry: ReplaceEntry) -> str:
    lines = [entry.replacement]
    if entry.original:
        lines.append(f"  Заменяет: {entry.original}")
    return "\n".join(lines) + "\n\n"


def iter_section_text(entries: Iterable[object]) -> str:
    """Concatenate plain text for a whole section (tests / CLI helpers)."""

    return "".join(entry_to_text(e) for e in entries)
