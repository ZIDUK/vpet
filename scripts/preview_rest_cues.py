"""Preview approved rest explanations without opening a saved pet."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from PIL import Image, ImageDraw
from core.pet import Pet
from display_profiles import get_display_profile
from scripts.sim_renderer import render_frame


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'out/rest-cue-clarity')
    output = parser.parse_args().output
    output.mkdir(parents=True, exist_ok=True)
    cases = [
        ("ES", 0, 20, 12, 0), ("ES", 1, 20, 12, 76),
        ("ES", 2, 20, 12, 152), ("EN", 0, 20, 12, 76),
        ("ES", 1, 80, 22, 0), ("ES", 1, 20, 22, 76),
        ("EN", 1, 80, 22, 152), ("ES", 1, 32, 12, 76),
    ]
    sheet = Image.new("RGB", (960, 1240), (24, 32, 36))
    draw = ImageDraw.Draw(sheet)
    for index, (language, trait, energy, hour, x) in enumerate(cases):
        pet = Pet(species="rookie", state="live")
        pet.dna = (1, 2, 3, trait)
        pet.language = language
        pet.stats.update(h=80, e=energy, p=80)
        pet.sleep.bedtime = 1320
        pet.sleep.physical_tired = energy < 35
        before = pet.to_dict()
        frame = render_frame(ROOT / "build-tdisplay", pet, pet_x=x,
            current_datetime=(2026, 10, 22, hour, 0),
            profile=get_display_profile("tdisplay"))
        assert pet.to_dict() == before
        frame.save(output / ("rest-%d.png" % index))
        sx, sy = (index % 2) * 480, (index // 2) * 310
        draw.text((sx + 4, sy + 3), "%s / E %d / goal %d / %02d:00" %
                  (language, energy, 30 + trait * 5, hour), fill="white")
        sheet.paste(frame.resize((480, 270), Image.Resampling.NEAREST), (sx, sy + 20))
    path = output / "overview.png"
    sheet.save(path)
    print(path)


if __name__ == "__main__":
    main()
