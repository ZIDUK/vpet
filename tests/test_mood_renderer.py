import io
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image
from core.cues import bubble_position, pet_cue
from core.pet import Pet
from core.status_card import STATUS_SPLIT_X
from display_profiles import get_display_profile
from scripts import build, build_tdisplay
from scripts.sim_renderer import render_frame
from scripts.tdisplay_assets import decode_vpa

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def mood_pixels(tmp_path_factory):
    root = tmp_path_factory.mktemp("mood-pixels")
    build.main(profile_name="tdisplay", output_dir=root/"sim")
    build_tdisplay.build(ROOT, root/"sim", root/"data", root/"include/generated")
    core = ROOT/"firmware/t-display/lib/vpet_core/src"
    binary = root/"render"
    subprocess.run([
        "c++", "-std=c++17", "-O1", "-ffunction-sections", "-fdata-sections",
        "-Wl,-dead_strip" if sys.platform == "darwin" else "-Wl,--gc-sections",
        "-I"+str(ROOT/"tests/asset_stubs"), "-I"+str(root/"include"),
        "-I"+str(ROOT/"firmware/t-display/include"), "-I"+str(core),
        str(ROOT/"tests/mood_pixels.cpp"),
        *[str(ROOT/"firmware/t-display/src"/(name+".cpp")) for name in ("Renderer","Panels","AssetStore")],
        *[str(core/"vpet"/(name+".cpp")) for name in ("Motion","PetState","Nutrition","Navigation","DateTimeMenu","Evolution")],
        "-o", str(binary)], check=True)
    return root, binary


def board(root, binary, mode, mood, x=76, panel="home"):
    return Image.open(io.BytesIO(subprocess.check_output([
        str(binary),str(root/"data"),mode,str(mood),str(x),panel]))).convert("RGB")


@pytest.mark.parametrize("mode,mood,name", [
    ("food",80,"food"),("food",30,"food_angry"),("rest",80,"rest"),
    ("rest",30,"rest_angry"),("hurt",10,"hurt"),("idle",30,"sad"),("idle",10,"angry")])
@pytest.mark.parametrize("x", [0,76,152])
def test_real_board_bubble_pixels_and_no_corner_badge(mood_pixels, mode, mood, name, x):
    root,binary=mood_pixels
    actual=board(root,binary,mode,mood,x)
    bubble=decode_vpa((root/"data/ui/mood"/(name+".vpa")).read_bytes()).frames[0]
    bx,by,flip=bubble_position(x,43,1)
    if flip: bubble=bubble.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    for y in range(bubble.height):
        for px in range(bubble.width):
            if bubble.getpixel((px,y))[3]:
                assert actual.getpixel((bx+px,by+y))==bubble.getpixel((px,y))[:3]
    background=decode_vpa((root/"data/backgrounds/background.vpa").read_bytes()).frames[0]
    assert actual.getpixel((237,132))==background.getpixel((237,132))[:3]
    pet=Pet(species="rookie",state="live")
    pet.stats.update(p=mood,h=10 if mode=="food" else 80,e=20 if mode=="rest" else 80)
    pet.injured=mode=="hurt"
    simulated=render_frame(root/"sim",pet,pet_x=x,current_datetime=(2026,10,18,12,0),
                           profile=get_display_profile("tdisplay"))
    bmp=Image.open(root/"sim/UIMood"/(name+".bmp"))
    if flip: bmp=bmp.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    rgb=bmp.convert("RGB")
    for y in range(28):
        for px in range(32):
            if bmp.getpixel((px,y)):
                assert simulated.getpixel((bx+px,by+y))==rgb.getpixel((px,y))


@pytest.mark.parametrize("mode", ["egg","dead","cold","away","sleep","eat","panel","idle"])
def test_real_board_does_not_show_bubbles_in_hidden_states(mood_pixels, mode):
    root,binary=mood_pixels
    actual=board(root,binary,mode,80)
    background=decode_vpa((root/"data/backgrounds/background.vpa").read_bytes()).frames[0]
    assert actual.getpixel((155,30))==background.getpixel((155,30))[:3]


@pytest.mark.parametrize("mood,face", [(80,"happy"),(60,"neutral"),(30,"sad"),(10,"angry")])
def test_status_real_board_and_simulator_use_same_face(mood_pixels,mood,face):
    root,binary=mood_pixels
    actual=board(root,binary,"idle",mood,panel="status")
    pet=Pet(species="rookie",state="live"); pet.stats.update(p=mood,h=80,e=80)
    assert pet_cue(pet)[1]==face
    simulated=render_frame(root/"sim",pet,panel_mode="status",profile=get_display_profile("tdisplay"))
    icon=decode_vpa((root/"data/ui/mood"/("face_"+face+".vpa")).read_bytes()).frames[0]
    # AssetStore's nearest sampling uses integer coordinates for the 20 -> 16 slot.
    bmp=Image.open(root/"sim/UIMood"/("face_"+face+".bmp")).resize((16,16),Image.Resampling.NEAREST)
    icon_x=STATUS_SPLIT_X+3
    for y in range(16):
        for x in range(16):
            sx,sy=x*20//16,y*20//16
            if icon.getpixel((sx,sy))[3]:
                assert actual.getpixel((icon_x+x,114+y))==icon.getpixel((sx,sy))[:3]
    rgb=bmp.convert("RGB")
    for y in range(16):
        for x in range(16):
            if bmp.getpixel((x,y)):
                assert simulated.getpixel((icon_x+x,114+y))==rgb.getpixel((x,y))


def test_simulator_status_visible_alias_hides_home_bubble(mood_pixels):
    root,_=mood_pixels
    pet=Pet(species="rookie",state="live"); pet.stats.update(p=10,h=0)
    args=dict(build_dir=root/"sim",pet=pet,profile=get_display_profile("tdisplay"))
    assert render_frame(**args,status_visible=True).tobytes()==render_frame(**args,panel_mode="status").tobytes()
