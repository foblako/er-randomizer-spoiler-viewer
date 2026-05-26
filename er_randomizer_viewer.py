#!/usr/bin/env python3
"""Backwards-compatible launcher.

Historically the project shipped a single `er_randomizer_viewer.py` script.
The implementation now lives inside the `er_randomizer` package; this file is
kept so that `python er_randomizer_viewer.py` keeps working.
"""

from er_randomizer.gui import run

if __name__ == "__main__":
    run()
