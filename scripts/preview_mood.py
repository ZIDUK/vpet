"""Capture needs and mood faces without opening or changing a saved pet."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from PIL import Image, ImageDraw
from core.pet import Pet
from display_profiles import get_display_profile
from scripts.sim_renderer import render_frame


def main():
    output = ROOT / "out/mood-bubbles-preview"
    output.mkdir(parents=True, exist_ok=True)
    sheet = Image.new("RGB", (720, 620), (24, 32, 36))
    labels = ImageDraw.Draw(sheet)
    cases = [("food",80),("food",30),("rest",80),("rest",30),
             ("hurt",10),("idle",30),("idle",10),("idle",80),
             ("status",80),("status",60),("status",30),("status",10)]
    for index, (mode, mood) in enumerate(cases):
        pet = Pet(species="rookie", state="live")
        pet.stats.update(h=10 if mode=="food" else 80,
                         e=20 if mode=="rest" else 80, p=mood)
        pet.injured = mode=="hurt"
        before = pet.to_dict()
        image = render_frame(ROOT/"build-tdisplay", pet, pet_x=76,
            current_datetime=(2026,10,18,12,0), profile=get_display_profile("tdisplay"),
            panel_mode="status" if mode=="status" else None)
        assert pet.to_dict()==before
        image.save(output/(mode+"-"+str(mood)+".png"))
        x,y=(index%3)*240,(index//3)*155
        sheet.paste(image,(x,y+20))
        labels.text((x+4,y+3),mode+" / mood "+str(mood),fill="white")
    path = output/"overview.png"
    sheet.resize((1440,1240),Image.Resampling.NEAREST).save(path)
    print(path)


if __name__ == "__main__":
    main()
