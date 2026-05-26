"""Tiny JSON-on-disk store at `~/.er_randomizer.json`.

Both the theme and the user-presets module share this file, so we
centralise read/write here. All errors are swallowed: a corrupted disk
or an unreadable file is never worth crashing the GUI for.
"""

from __future__ import annotations

import contextlib
import json
from pathlib import Path

CONFIG_PATH = Path.home() / ".er_randomizer.json"


def read_config() -> dict[str, object]:
    """Return the parsed JSON config, or `{}` if the file is missing /
    unreadable / not a JSON object.
    """

    try:
        raw = CONFIG_PATH.read_text(encoding="utf-8")
    except OSError:
        return {}
    try:
        data = json.loads(raw)
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def update_config(**values: object) -> None:
    """Merge `values` into the on-disk config. Missing files are created;
    write errors are silently ignored.
    """

    existing = read_config()
    existing.update(values)
    with contextlib.suppress(OSError):
        CONFIG_PATH.write_text(
            json.dumps(existing, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
