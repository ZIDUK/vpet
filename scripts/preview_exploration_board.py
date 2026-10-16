#!/usr/bin/env python3
"""Render the production board Exploration view with the packaged VPA assets."""
import io
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]


def main():
    output = ROOT / "out/exploration-board"
    output.mkdir(parents=True, exist_ok=True)
    core = ROOT / "firmware/t-display/lib/vpet_core/src"
    binary = output / "pixels"
    subprocess.run(["c++", "-std=c++17", "-O2", "-I" + str(core),
                    "-I" + str(ROOT / "firmware/t-display/include"),
                    str(ROOT / "tests/exploration_pixels.cpp"),
                    str(core / "vpet/PetState.cpp"), str(core / "vpet/Nutrition.cpp"),
                    "-o", str(binary)], check=True)
    cases = [("routes", 0, 0, 0, 0), ("stats", 1, 1, 2, 0),
             ("prepare", 2, 1, 0, 0), ("trip", 3, 1, 0, 14400),
             ("return", 3, 1, 0, 28800), ("early", 4, 1, 1, 14400),
             ("saved", 5, 1, 0, 28800), ("clock", 6, 1, 0, 0)]
    gallery = Image.new("RGB", (4 * 244, 4 * 155), (245, 245, 245))
    draw = ImageDraw.Draw(gallery)
    for row, language in enumerate(("ES", "EN")):
        for i, (name, page, route, cursor, elapsed) in enumerate(cases):
            raw = subprocess.check_output([str(binary), str(ROOT / "firmware/t-display/data"),
                                           str(page), language, str(route), "0", str(cursor), str(elapsed), "0"])
            frame = Image.open(io.BytesIO(raw)).convert("RGB")
            frame.save(output / f"{name}-{language}.png")
            x, y = (i % 4) * 244, (row * 2 + i // 4) * 155
            draw.text((x, y), f"{language}: {name}", fill="black")
            gallery.paste(frame, (x, y + 16))
    gallery.save(output / "gallery.png")
    Image.open(output / "prepare-ES.png").resize((960, 540), Image.Resampling.NEAREST).save(output / "prepare-large.png")
    print(output / "gallery.png")


if __name__ == "__main__":
    main()
