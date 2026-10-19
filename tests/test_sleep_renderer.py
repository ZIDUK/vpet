import io
import subprocess
from pathlib import Path

import pytest
from PIL import Image
from scripts import build, build_tdisplay
from scripts.tdisplay_assets import decode_vpa
from scripts.sim_renderer import render_frame
from display_profiles import get_display_profile
from core.pet import Pet

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT/'firmware/t-display/lib/vpet_core/src'
SPECIES = [(4,'baby','sparkmon'),(0,'rookie','firemon'),(1,'champion','flamemon'),(2,'ultimate','dragfiremon')]


@pytest.fixture(scope='module')
def sleep_pixels(tmp_path_factory):
    root = tmp_path_factory.mktemp('sleep-pixels')
    build.main(profile_name='tdisplay',output_dir=root/'sim')
    build_tdisplay.build(ROOT,sim_build=root/'sim',data_dir=root/'data',include_dir=root/'include')
    binary = root/'render'
    subprocess.run(['c++','-std=c++17','-O2','-I'+str(ROOT/'tests/asset_stubs'),
                    '-I'+str(ROOT/'firmware/t-display/include'),'-I'+str(CORE),
                    str(ROOT/'tests/sleep_pixels.cpp'),str(ROOT/'firmware/t-display/src/Renderer.cpp'),
                    str(ROOT/'firmware/t-display/src/AssetStore.cpp'),
                    *[str(CORE/'vpet'/(name+'.cpp')) for name in ('Motion','PetState','Nutrition')],
                    '-o',str(binary)],check=True,capture_output=True,text=True)
    return root,binary


@pytest.mark.parametrize('species,stage,name',SPECIES)
@pytest.mark.parametrize('mode,minute', [('tired',1080),('tired',720),('sleep',360),('sleep',1080)])
@pytest.mark.parametrize('index',[0,8,24])
def test_real_board_renderer_colors_feet_cadence_and_background_cache(sleep_pixels,species,stage,name,mode,minute,index):
    root,binary=sleep_pixels
    raw=subprocess.check_output([str(binary),str(root/'data'),str(species),mode,str(minute),str(index),'1'])
    actual=Image.open(io.BytesIO(raw)).convert('RGB')
    background='background_night' if minute>=1080 or minute<360 else 'background'
    expected=decode_vpa((root/'data/backgrounds'/(background+'.vpa')).read_bytes()).frames[0].convert('RGB')
    sprite=decode_vpa((root/'data/animations'/stage/(name+'_'+mode+'.vpa')).read_bytes())
    sleep_frame=index if index<=14 else 11+(index-15)%4
    frame=sprite.frames[index if mode=='tired' else sleep_frame]
    expected.paste(frame,(76+(88-frame.width)//2,43+88-frame.height),frame)
    assert actual.crop((0,24,240,135)).tobytes()==expected.crop((0,24,240,135)).tobytes()
    assert actual.getpixel((76,132))==expected.getpixel((76,132))


def test_simulator_dawn_does_not_wake_and_rendering_does_not_change_saved_routine(sleep_pixels):
    root,_=sleep_pixels
    pet=Pet(species='rookie',state='live')
    pet.sleep.start(20000*86400+23*3600,1)
    before=pet.sleep.encode()
    dawn=render_frame(root/'sim',pet,motion_state='sleep',current_datetime=(2026,10,18,6,0),
                      profile=get_display_profile('tdisplay'))
    day=Image.open(root/'sim/Background/background.bmp').convert('RGB')
    assert dawn.getpixel((4,30))==day.getpixel((4,30))
    assert pet.sleep.asleep and pet.sleep.encode()==before
