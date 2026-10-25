#!/usr/bin/env python3
"""Render the production Evolution Detail panel and compare it with the simulator."""
import argparse
import io
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from PIL import Image, ImageChops, ImageDraw
from core.pet import Pet
from display_profiles import get_display_profile
from scripts import build, build_tdisplay
from scripts.sim_renderer import render_frame
from scripts.verify_training_pixels import quantized


def compile_renderer(binary, include):
    core = ROOT / "firmware/t-display/lib/vpet_core/src"
    subprocess.run([
        "c++", "-std=c++17", "-O1", "-ffunction-sections", "-fdata-sections",
        "-Wl,-dead_strip" if sys.platform == "darwin" else "-Wl,--gc-sections",
        "-I" + str(ROOT / "tests/asset_stubs"), "-I" + str(include),
        "-I" + str(ROOT / "firmware/t-display/include"), "-I" + str(core),
        str(ROOT / "tests/evolution_progress.cpp"),
        *[str(ROOT / "firmware/t-display/src" / (name + ".cpp")) for name in ("Panels", "AssetStore")],
        *[str(core / "vpet" / (name + ".cpp")) for name in ("PetState", "Nutrition", "Navigation", "DateTimeMenu", "Evolution")],
        "-o", str(binary),
    ], check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "out/evolution-progress")
    args = parser.parse_args()
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    sim, data, include = output / "sim", output / "data", output / "include"
    build.main(profile_name="tdisplay", output_dir=sim)
    build_tdisplay.build(ROOT, sim, data, include / "generated")
    binary = output / "render"
    compile_renderer(binary, include)
    cases = [(4, "baby", 1, 0, False, 36000), (0, "rookie", 2, 0, False, 46800),
             (0, "rookie", 2, 1, False, 46800), (1, "champion", 3, 0, False, 129600),
             (1, "champion", 3, 0, True, 129600), (2, "ultimate", 4, 0, True, 129600),
             (0, "rookie", 1, 0, False, 46800), (0, "rookie", 4, 0, False, 46800),
             (3, "egg", 0, 0, False, 0)]
    gallery = Image.new("RGB", (980, len(cases) * 154), "#e4e6e8")
    draw = ImageDraw.Draw(gallery)
    report = []
    for row, (species_id, species, selected, page, met, age) in enumerate(cases):
        for language in ("ES", "EN"):
            pet = Pet(species=species, state="live")
            pet.language = language
            pet.stats.update(h=80 if met else 40, e=70, p=60, hp=90)
            pet.stage_age_seconds, pet.weight = age, 10
            pet.battles_this_form = 15 if met else 14
            pet.battles_won, pet.battles_lost = (9, 6) if met else (8, 7)
            pet.care_mistakes = 1 if met else 2
            raw = subprocess.check_output([str(binary), str(data), str(species_id), str(selected),
                                           str(page), language, str(int(met)), str(age), "10", "pixels"])
            actual = Image.open(io.BytesIO(raw)).convert("RGB")
            expected = quantized(render_frame(sim, pet, menu_index=7, panel_mode="evolution_detail",
                                              panel_index=selected + 5 * page,
                                              profile=get_display_profile("tdisplay")))
            slug = "%02d-%s" % (row, language)
            for column, (kind, frame) in enumerate((("sim", expected), ("firmware", actual))):
                frame.save(output / (slug + "-" + kind + ".png"))
                x = ((0 if language == "ES" else 2) + column) * 245
                draw.text((x, row * 154), "%s %s %s p%d" % (language, kind, species, page + 1), fill="black")
                gallery.paste(frame, (x, row * 154 + 18))
            diff = ImageChops.difference(actual.crop((0, 24, 240, 135)), expected.crop((0, 24, 240, 135)))
            report.append(dict(case=slug, different_pixels=sum(pixel != (0, 0, 0) for pixel in diff.getdata()),
                               bounds=diff.getbbox()))
    gallery.save(output / "gallery.png")
    pages = Image.new("RGB", (960, 270))
    for page, slug in enumerate(("01-ES-firmware.png", "02-ES-firmware.png")):
        with Image.open(output / slug) as frame:
            pages.paste(frame.resize((480, 270), Image.Resampling.NEAREST), (page * 480, 0))
    pages.save(output / "firemon-pages.png")
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
