"""Light & dark theme palettes plus a tiny config-file helper to persist
the user's choice between sessions.

Both themes are tuned so that the Text-widget tag styles (item name,
labels, values, headers) stay legible without re-defining them per theme:
we just swap colours at runtime via `SpoilerViewerApp._apply_theme`.
"""

from __future__ import annotations

from dataclasses import dataclass

from er_randomizer.config import read_config, update_config


@dataclass(frozen=True)
class Theme:
    """Resolved colour palette for a single theme."""

    name: str
    bg: str
    panel: str
    panel_alt: str
    border: str
    text: str
    muted: str
    accent: str
    accent_fg: str
    name_fg: str
    value_fg: str
    label_fg: str
    bullet_fg: str
    header_bg: str
    header_fg: str
    button_bg: str
    button_fg: str
    button_active_bg: str
    entry_bg: str
    entry_fg: str
    results_bg: str
    scrollbar_trough: str
    scrollbar_bg: str
    cap_fg: str  # colour of the "и ещё N..." footer.


LIGHT_THEME = Theme(
    name="light",
    bg="#eef0f3",
    panel="#ffffff",
    panel_alt="#f4f6f9",
    border="#c4cad6",
    text="#1f2733",
    muted="#6c7785",
    accent="#2f80ed",
    accent_fg="#ffffff",
    name_fg="#1f2733",
    value_fg="#3a4250",
    label_fg="#7886a0",
    bullet_fg="#2f80ed",
    header_bg="#2f80ed",
    header_fg="#ffffff",
    button_bg="#e6eaf1",
    button_fg="#1f2733",
    button_active_bg="#d4dae4",
    entry_bg="#ffffff",
    entry_fg="#1f2733",
    results_bg="#fbfcfe",
    scrollbar_trough="#e6eaf1",
    scrollbar_bg="#a8b1c0",
    cap_fg="#6c7785",
)


DARK_THEME = Theme(
    # Tuned for clear hierarchy on a dark background:
    # window bg < panel < panel_alt < entry, with a saturated accent that
    # pops against all of them so headers / checked states / focused
    # entries are obviously distinct.
    name="dark",
    bg="#13151c",            # window bg (darkest)
    panel="#1d2029",         # outer frames
    panel_alt="#262a36",     # inner frames (left categories, toolbars)
    border="#3a4055",        # frame separators
    text="#eef1f7",
    muted="#9aa3b8",         # bumped from #8b91a3 for legibility
    accent="#5b9cf6",
    accent_fg="#0c0f15",
    name_fg="#ffffff",       # max contrast for primary item names
    value_fg="#dde2ee",      # bumped so values aren't washed out
    label_fg="#9aa3b8",
    bullet_fg="#7eb6ff",
    header_bg="#5b9cf6",     # full-width accent strip — sections pop
    header_fg="#0c0f15",
    button_bg="#2b3142",
    button_fg="#eef1f7",
    button_active_bg="#3a4259",
    entry_bg="#2b3142",
    entry_fg="#ffffff",
    results_bg="#181b23",    # slightly darker than panel for contrast
    scrollbar_trough="#1d2029",
    scrollbar_bg="#465070",
    cap_fg="#9aa3b8",
)


THEMES: dict[str, Theme] = {LIGHT_THEME.name: LIGHT_THEME, DARK_THEME.name: DARK_THEME}


def load_preferred_theme(default: str = "dark") -> Theme:
    """Read the saved theme name from the user-config file, fall back gracefully."""

    name = read_config().get("theme")
    if isinstance(name, str) and name in THEMES:
        return THEMES[name]
    return THEMES.get(default, DARK_THEME)


def save_preferred_theme(theme: Theme) -> None:
    """Persist the user's choice. Errors are swallowed: bad disks shouldn't crash UI."""

    update_config(theme=theme.name)


def toggle(theme: Theme) -> Theme:
    return DARK_THEME if theme.name == LIGHT_THEME.name else LIGHT_THEME
