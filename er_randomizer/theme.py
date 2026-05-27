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
    # TarnishedTool-inspired palette: near-black base, warm gold accent.
    name="dark",
    bg="#121212",
    panel="#1a1a1a",
    panel_alt="#252525",
    border="#333333",
    text="#eaeaea",
    muted="#888888",
    accent="#b37c07",
    accent_fg="#121212",
    name_fg="#ffffff",
    value_fg="#c8c8c8",
    label_fg="#888888",
    bullet_fg="#b37c07",
    header_bg="#92400e",
    header_fg="#eaeaea",
    button_bg="#252525",
    button_fg="#eaeaea",
    button_active_bg="#5a3d00",
    entry_bg="#252525",
    entry_fg="#eaeaea",
    results_bg="#0f0f0f",
    scrollbar_trough="#1a1a1a",
    scrollbar_bg="#92400e",
    cap_fg="#888888",
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
