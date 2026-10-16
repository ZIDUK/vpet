"""Real source-sheet bounds must survive the runtime atlas pipeline."""
from PIL import Image
from scripts import build


def test_emotion_viewports_keep_every_selected_frame(monkeypatch, tmp_path):
    original = build._build_firemon_atlas
    checked = []

    def inspect(source, rows, expected_frames, viewport, output_size,
                frame_indices=None, tile_size=64, columns=5, frame_size=204):
        if source.name in ("firemon-happy.png", "firemon-sad.png"):
            with Image.open(source) as sheet:
                background = sheet.getpixel((0, 0))
                mask = sheet.point([0 if i == background else 255 for i in range(256)], mode="L")
                for index in frame_indices:
                    x, y = index % columns * frame_size, index // columns * frame_size
                    bounds = mask.crop((x, y, x + frame_size, y + frame_size)).getbbox()
                    assert viewport[0] <= bounds[0] and viewport[1] <= bounds[1]
                    assert viewport[2] >= bounds[2] and viewport[3] >= bounds[3], (source.name, index, bounds, viewport)
            checked.append(source.name)
        return original(source, rows, expected_frames, viewport, output_size,
                        frame_indices, tile_size, columns, frame_size)

    monkeypatch.setattr(build, "_build_firemon_atlas", inspect)
    build.main(profile_name="tdisplay", output_dir=tmp_path / "build")
    assert set(checked) == {"firemon-happy.png", "firemon-sad.png"}
    from core.pet import Pet
    from scripts.practice_session import PracticeSession
    from scripts.practice_renderer import render_practice, _draw_atlas, _species_atlas, PANEL
    from scripts.sim_renderer import _load_image
    _load_image.cache_clear()
    for language in ("ES", "EN"):
        pet = Pet(species="rookie", state="live")
        pet.language = language
        session = PracticeSession(pet, lambda _: True)
        session.battle.round = 10
        session.awarded = True
        for result, action in (("VICTORIA", "happy"), ("DERROTA", "sad")):
            session.battle.result = result
            for index in range(15):
                ms = index * 100
                image = render_practice(tmp_path / "build", session, ms)
                expected = Image.new("RGB", (48, 48), PANEL)
                _draw_atlas(expected, tmp_path / "build", _species_atlas("rookie", action),
                            0, 0, 48, ms)
                assert image.crop((174, 57, 222, 105)).tobytes() == expected.tobytes()
