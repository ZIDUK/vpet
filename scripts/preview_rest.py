"""Render the approved Rest/pause menus without loading a saved pet."""
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from PIL import Image
from core.pet import Pet
from core.options import OptionsSession, OPTION_PAUSE
from display_profiles import get_display_profile
from scripts.sim_renderer import render_frame


def main():
    output=ROOT/'out/rest-preview'
    output.mkdir(parents=True,exist_ok=True)
    sheet=Image.new('RGB',(960,270))
    for row,language in enumerate(('ES','EN')):
        for col,(panel,asleep,cold) in enumerate((('rest',False,False),('rest',True,False),
                                                ('options',False,False),('options',False,True))):
            pet=Pet(species='rookie',state='live')
            pet.language=language; pet.sleep.asleep=asleep; pet.cold=cold
            options=OptionsSession(); options.index=OPTION_PAUSE
            before=pet.to_dict()
            frame=render_frame(ROOT/'build-tdisplay',pet,menu_index=5 if panel=='rest' else 8,
                               panel_mode=panel,options_session=options,
                               profile=get_display_profile('tdisplay'))
            assert pet.to_dict()==before
            frame.save(output/('%s-%d-%s.png'%(panel,col,language)))
            sheet.paste(frame,(col*240,row*135))
    path=output/'overview.png'
    sheet.resize((1920,540),Image.Resampling.NEAREST).save(path)
    print(path)
    lighting=Image.new('RGB',(480,270))
    for row,hour in enumerate((12,22)):
        for col,asleep in enumerate((False,True)):
            pet=Pet(species='rookie',state='live'); pet.sleep.asleep=asleep
            frame=render_frame(ROOT/'build-tdisplay',pet,menu_index=5,
                               motion_state='sleep' if asleep else 'idle',
                               current_datetime=(2026,10,19,hour,0),
                               profile=get_display_profile('tdisplay'))
            frame.save(output/('home-%02d-%s.png'%(hour,'off' if asleep else 'on')))
            lighting.paste(frame,(col*240,row*135))
    path=output/'lighting.png'
    lighting.resize((1440,810),Image.Resampling.NEAREST).save(path)
    print(path)


if __name__=='__main__':
    main()
