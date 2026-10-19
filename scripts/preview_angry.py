"""Render isolated Home mood examples without touching a saved pet."""
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from PIL import Image
from core.pet import Pet
from display_profiles import get_display_profile
from scripts.sim_renderer import render_frame


def main():
    output=ROOT/'out/angry-preview'
    output.mkdir(parents=True,exist_ok=True)
    species=('baby','rookie','champion','ultimate')
    sheet=Image.new('RGB',(960,405))
    for row,(mood,hunger) in enumerate(((80,80),(10,80),(30,10))):
        for col,name in enumerate(species):
            pet=Pet(species=name,state='live'); pet.stats.update(p=mood,h=hunger,e=80)
            before=pet.to_dict()
            frame=render_frame(ROOT/'build-tdisplay',pet,pet_x=76,now_ms=8*90,
                               current_datetime=(2026,10,19,12,0),
                               profile=get_display_profile('tdisplay'))
            assert pet.to_dict()==before
            frame.save(output/('%s-%d.png'%(name,row)))
            sheet.paste(frame,(col*240,row*135))
    path=output/'overview.png'
    sheet.resize((1920,810),Image.Resampling.NEAREST).save(path)
    print(path)


if __name__=='__main__':
    main()
