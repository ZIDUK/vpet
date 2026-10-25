"""Real Training render parity and Status three-digit bounds after F2b."""
import io
from pathlib import Path
import subprocess

from PIL import Image, ImageChops, ImageDraw
import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def growth_art(tmp_path_factory):
    from scripts import build, build_tdisplay
    from scripts.verify_training_pixels import compile_renderer
    root = tmp_path_factory.mktemp("growth-ui")
    sim, data, include = root / "sim", root / "data", root / "include"
    build.main(profile_name="tdisplay", output_dir=sim)
    build_tdisplay.build(ROOT, sim, data, include / "generated")
    binary = root / "training"
    compile_renderer(binary, include)
    yield sim, data, binary, root
    gallery = Image.new("RGB", (1440, 870), "#ededed")
    draw = ImageDraw.Draw(gallery)
    for row, role in enumerate(("rookie", "champion", "ultimate")):
        for col, state in enumerate((0, 1, 4)):
            path = root / f"{role}-ES-{state}.png"
            if path.exists():
                draw.text((col*480,row*290),f"{role}: {state}",fill="black")
                with Image.open(path) as frame:
                    gallery.paste(frame.resize((480,270),Image.Resampling.NEAREST),(col*480,row*290+18))
    destination = ROOT / "out/growth-integration"
    destination.mkdir(parents=True,exist_ok=True)
    gallery.save(destination / "training-wide.png")


@pytest.mark.parametrize("role,species_id", [("rookie",0),("champion",1),("ultimate",2)])
@pytest.mark.parametrize("lang", ["ES","EN"])
@pytest.mark.parametrize("state", [0,1,4])
def test_wide_training_values_match_production_renderer(growth_art, role, species_id, lang, state):
    from core.pet import Pet
    from scripts.training_session import TrainingSession
    from scripts.training_renderer import render_training
    from scripts.verify_training_pixels import quantized
    sim,data,binary,root = growth_art
    pet = Pet()
    pet.complete_hatch(role,entropy=42)
    pet.restore_dna((0xab,0xcd,0xef,0x12))
    pet.restore_ev(dict(zip(("hp","mp","off","def","spd","brn"),(252,24,30,12,18,0))))
    pet.language = lang
    pet.stats.update(h=50,e=80,p=80,hp=80)
    pet.effort = 0
    session = TrainingSession(pet,lambda _:True)
    session.index = session._chosen_index = 3
    session._chosen_stat = "hp"
    session.state = {0:"select",1:"prepare",4:"result"}[state]
    session._focus = "start"
    if state == 4:
        session._result_snapshot = {"reps":0,"ev_added":0,"energy_charged":0,"effort_added":0}
        session._focus = "back"
    raw = subprocess.check_output([str(binary),str(data),str(state),lang,"3","0","0",
                                   "1600","80","252","3","3",str(species_id),"pixels"])
    actual = Image.open(io.BytesIO(raw)).convert("RGB")
    expected = quantized(render_training(sim,session,1600))
    assert ImageChops.difference(actual,expected).getbbox() is None
    actual.save(root / f"{role}-{lang}-{state}.png")


def test_status_320_fits_before_bar_and_does_not_mutate(growth_art, monkeypatch):
    from core.pet import Pet
    from display_profiles import get_display_profile
    from scripts.sim_renderer import render_frame
    sim,_,_,_ = growth_art
    pet = Pet(species="ultimate",state="live")
    pet.restore_dna((255,255,255,1))
    pet.restore_ev(dict.fromkeys(("hp","mp","off","def","spd","brn"),252))
    original = ImageDraw.ImageDraw.text
    captured = []

    def text(draw,xy,value,*args,**kwargs):
        if value == "320":
            captured.append(xy)
            box = draw.textbbox(xy,value,font=kwargs["font"])
            assert box[2] <= 199 and box[3]-box[1] <= 13
        return original(draw,xy,value,*args,**kwargs)

    monkeypatch.setattr(ImageDraw.ImageDraw,"text",text)
    before = pet.to_dict()
    frame = render_frame(sim,pet,panel_mode="status",panel_index=3,profile=get_display_profile("tdisplay"))
    assert len(captured) == 6 and pet.to_dict() == before
    target = ROOT / "out/growth-integration/status-320.png"
    target.parent.mkdir(parents=True,exist_ok=True)
    frame.resize((960,540),Image.Resampling.NEAREST).save(target)
