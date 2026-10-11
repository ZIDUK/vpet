#!/usr/bin/env python3
"""Capture the actual Training simulator with consistent, valid pet fixtures."""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from scripts.verify_training_pixels import sim_frame


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("build_dir", nargs="?", type=Path, default=ROOT / "build-tdisplay")
    parser.add_argument("--output", type=Path, default=ROOT / "out/training-preview")
    args = parser.parse_args()
    screens = [
        ("select", 0, 0, 0), ("prepare", 1, 0, 0),
        ("session_train", 2, 0, 2), ("session_finish", 2, 1, 2),
        ("confirm", 3, 0, 2), ("cancel", 6, 0, 2),
        ("result", 4, 0, 2), ("result_stats", 4, 1, 2),
        ("error", 5, 0, 2),
    ]
    for language in ("ES", "EN"):
        output = args.output / language
        output.mkdir(parents=True, exist_ok=True)
        for slug, state, secondary, reps in screens:
            frame = sim_frame(args.build_dir, state, language, 0, secondary, reps, 1600, 80, 30)
            frame.save(output / (slug + ".png"))
    print("Simulator previews:", args.output)
    print("For actual C++ pixel comparison: scripts/verify_training_pixels.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
