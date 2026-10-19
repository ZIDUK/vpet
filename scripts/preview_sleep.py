#!/usr/bin/env python3
"""Contact sheet of the approved night/tired states at hardware resolution."""
import argparse
import io
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT),str(ROOT/'src')]
from PIL import Image, ImageDraw
from core.pet import Pet
from display_profiles import get_display_profile
from scripts.sim_renderer import render_frame


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--renderer',type=Path,help='Optional compiled tests/sleep_pixels.cpp renderer')
    parser.add_argument('--output',type=Path,default=ROOT/'out/night-sleep-preview.png')
    args = parser.parse_args()
    pets = [(4,'baby','Sparkmon'),(0,'rookie','Firemon'),(1,'champion','Flamemon'),(2,'ultimate','Dragfiremon')]
    cases = [('tired',1079,'17:59 - LOW ENERGY'),('tired',1380,'23:00 - BEDTIME'),('sleep',360,'06:00 - STILL ASLEEP')]
    sheet = Image.new('RGB',(1920,954),(20,24,25))
    draw = ImageDraw.Draw(sheet)
    for row,(mode,minute,label) in enumerate(cases):
        for col,(species,stage,name) in enumerate(pets):
            index=14 if mode=='sleep' else 8
            if args.renderer:
                raw = subprocess.check_output([str(args.renderer),str(ROOT/'firmware/t-display/data'),
                    str(species),mode,str(minute),str(index),'1'])
                frame = Image.open(io.BytesIO(raw)).convert('RGB')
            else:
                pet = Pet(species=stage,state='live'); pet.stats['e']=0
                if mode=='sleep': pet.sleep.start(20000*86400+23*3600,1)
                frame = render_frame(ROOT/'build-tdisplay',pet,menu_index=5,motion_state='idle' if mode=='tired' else mode,
                    current_datetime=(2026,10,18,minute//60,minute%60),profile=get_display_profile('tdisplay'),
                    sprite_frame=index,now_ms=720)
            x,y=col*480,row*318
            draw.text((x+12,y+10),name+' / '+label,fill=(232,236,230))
            sheet.paste(frame.resize((480,270),Image.Resampling.NEAREST),(x,y+40))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    sheet.save(args.output)
    print(args.output)


if __name__=='__main__':
    main()
