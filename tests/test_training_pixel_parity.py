"""Render the production C++ UI, not an independently drawn firmware mock."""
from scripts import build, build_tdisplay
from scripts.verify_training_pixels import ROOT, verify, sim_frame
from scripts.practice_renderer import GREEN, PANEL


def test_training_cpp_matches_approved_simulator_pixels(tmp_path):
    sim = tmp_path / "sim"
    data = tmp_path / "data"
    include = tmp_path / "include"
    build.main(profile_name="tdisplay", output_dir=sim)
    build_tdisplay.build(ROOT, sim, data, include / "generated")
    assert verify(sim, tmp_path / "comparison", data, include)
    import io
    import subprocess
    from PIL import Image, ImageChops
    from core.pet import Pet
    from scripts.practice_session import PracticeSession
    from scripts.practice_renderer import render_practice
    from scripts.verify_training_pixels import quantized
    binary = tmp_path / "comparison" / "training-pixels"
    for lang in ("ES", "EN"):
        pet = Pet()
        pet.complete_hatch("rookie", entropy=42)
        pet.language = lang
        pet.techniques.training = 3
        pet.techniques.bond = 55
        pet.techniques.mastery = [12, 20, 30]
        for state in (7, 8):
            for technique in range(3):
                for cursor in range(4 if state == 7 else 3):
                    session = PracticeSession(pet, lambda _: True, training=True)
                    session.page = "tech" if state == 7 else "detail"
                    session.tech, session.index = technique, cursor
                    raw = subprocess.check_output([str(binary), str(data), str(state), lang,
                                                   str(technique), str(cursor), "0", "1600", "80", "30"])
                    actual = Image.open(io.BytesIO(raw)).convert("RGB")
                    expected = quantized(render_practice(sim, session, 1600))
                    assert ImageChops.difference(actual, expected).getbbox() is None
        for training, equipped in ((0, [0, 2]), (3, [0, 1]), (3, [2])):
            pet.techniques.training = training
            pet.techniques.equipped = equipped
            for cursor in range(4):
                for ms in (0, 700, 1600):
                    session = PracticeSession(pet, lambda _: True, training=True)
                    session.index = cursor
                    raw = subprocess.check_output([str(binary), str(data), "7", lang,
                                                   "0", str(cursor), "0", str(ms), "80", "30",
                                                   str(training), str(sum(1 << i for i in equipped))])
                    actual = Image.open(io.BytesIO(raw)).convert("RGB")
                    expected = quantized(render_practice(sim, session, ms))
                    assert ImageChops.difference(actual, expected).getbbox() is None
    for language in ("ES", "EN"):
        active = sim_frame(sim, 2, language, 0, 0, 1, 5000, 80, 30)
        # Only the main timer bar remains; the old under-pet bar is gone.
        assert active.getpixel((70, 103)) == GREEN
        assert active.getpixel((4, 84)) != GREEN
        result = sim_frame(sim, 4, language, 0, 0, 1, 10000, 80, 30)
        for x in (69, 121, 159, 199, 238):
            assert result.getpixel((x, 53)) == PANEL
