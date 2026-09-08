#!/usr/bin/env python3
"""Render deterministic 240x135 panel snapshots for visual review."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).parent.parent
for path in (ROOT, ROOT / "src"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from core.options import OptionsSession
from core.pet import Pet, STATE_LIVE
from display_profiles import get_display_profile
from scripts.sim_renderer import render_frame


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-dir", default="build-tdisplay")
    parser.add_argument("--output", default="out/tdisplay-panels")
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    pet = Pet(species="rookie", state=STATE_LIVE)
    profile = get_display_profile("tdisplay")
    options = OptionsSession()
    for name, menu, panel, selected, session in (
        ("status", 0, "status", 0, None),
        ("inventory", 5, "inventory", 1, None),
        ("evolution", 6, "evolution", 0, None),
        ("options", 7, "options", 4, options),
    ):
        if session is not None:
            session.index = selected
        frame = render_frame(
            args.build_dir,
            pet,
            menu_index=menu,
            panel_mode=panel,
            panel_index=selected,
            options_session=session,
            profile=profile,
        )
        frame.save(output / f"{name}.png")
        print(output / f"{name}.png")


if __name__ == "__main__":
    main()
