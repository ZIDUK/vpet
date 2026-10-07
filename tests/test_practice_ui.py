"""Layout checks use synthetic assets; preview_practice renders the real artwork."""
from itertools import combinations
from types import SimpleNamespace

import pytest
from PIL import Image, ImageDraw

from config import (BACKGROUND_PATH, PET_IDLE_IMAGE_PATH, PET_PUNCH_IMAGE_PATH,
                    PET_CAST_IMAGE_PATH, PET_BLOCK_IMAGE_PATH, PET_WALK_IMAGE_PATH)
from core.pet import Pet
from scripts.practice_icons import INFO_ICONS, PATTERNS, PALETTE, info_icon, technique_icon
from scripts.practice_renderer import HP, INK, bar, battle_feedback, render_practice
from scripts.practice_session import PracticeSession
from scripts.sim_renderer import device_path
from scripts.training_renderer import render_training
from scripts.training_session import TrainingSession


@pytest.fixture
def practice_assets(tmp_path):
    background = device_path(tmp_path, BACKGROUND_PATH)
    background.parent.mkdir(parents=True)
    Image.new("RGB", (240, 135), (75, 125, 90)).save(background)
    atlas = Image.new("P", (64, 32))
    atlas.putpalette([0, 0, 0, 240, 100, 30] + [0] * 762)
    ImageDraw.Draw(atlas).rectangle((8, 4, 20, 27), fill=1)
    ImageDraw.Draw(atlas).rectangle((42, 4, 54, 27), fill=1)
    for name in (PET_IDLE_IMAGE_PATH, PET_PUNCH_IMAGE_PATH, PET_CAST_IMAGE_PATH, PET_BLOCK_IMAGE_PATH, PET_WALK_IMAGE_PATH):
        path = device_path(tmp_path, name)
        path.parent.mkdir(parents=True, exist_ok=True)
        atlas.save(path)
    icons = tmp_path / "UIIcons"
    icons.mkdir()
    for name in ("Pedia", "Battle", "Back", "Training"):
        Image.new("RGB", (20, 20), (90, 140, 160)).save(icons / (name + ".bmp"))
    return tmp_path


def session(training=False, learned=False):
    pet = Pet()
    pet.complete_hatch("rookie", entropy=12345)
    if learned:
        pet.techniques.training = 255
        pet.techniques.mastery = [100] * 3
        pet.techniques.equipped = [0, 1]
    return PracticeSession(pet, lambda _: True, training=training)


@pytest.mark.parametrize("name", PATTERNS)
def test_icon_grid_transparency_and_lock(name):
    assert len(PATTERNS[name]) == 16
    assert all(len(row) == 16 and set(row) <= PALETTE.keys() for row in PATTERNS[name])
    icon = technique_icon(name)
    assert icon.size == (16, 16)
    assert icon.getpixel((0, 0))[3] == 0
    assert icon.tobytes() != technique_icon(name, locked=True).tobytes()


def test_explanatory_icon_catalog_covers_practice_labels():
    expected = {"hp", "mp", "attack", "defense", "speed", "mind", "bond",
                "power", "cost", "range", "mastery", "training", "lock"}
    assert expected <= INFO_ICONS.keys()
    for name in expected:
        icon = info_icon(name)
        assert icon.size == (16, 16)
        assert icon.getpixel((0, 0))[3] == 0


def test_bars_clamp_and_leave_zero_empty():
    frame = Image.new("RGB", (40, 10), INK)
    draw = ImageDraw.Draw(frame)
    bar(draw, 2, 2, 20, 0, 100, HP)
    assert not any(color == HP for _, color in frame.getcolors())
    bar(draw, 2, 2, 20, 120, 100, HP)
    assert frame.getpixel((21, 2)) == HP
    assert frame.getpixel((22, 2)) == INK


@pytest.mark.parametrize("learned", [False, True])
@pytest.mark.parametrize("training", [False, True])
def test_all_selections_fit_without_text_overlap(practice_assets, monkeypatch, learned, training):
    s = session(training=training, learned=learned)
    records = []
    real_text = ImageDraw.ImageDraw.text

    def checked_text(draw, xy, value, *args, **kwargs):
        box = draw.textbbox(xy, value, font=kwargs["font"])
        assert 0 <= box[0] < box[2] <= 240, (value, box)
        assert 0 <= box[1] < box[3] <= 135, (value, box)
        records.append((value, box))
        return real_text(draw, xy, value, *args, **kwargs)

    monkeypatch.setattr(ImageDraw.ImageDraw, "text", checked_text)

    def check():
        records.clear()
        before = s.pet.to_dict()
        frame = render_practice(practice_assets, s, 1700)
        assert frame.size == (240, 135)
        assert before == s.pet.to_dict()
        for (a, ra), (b, rb) in combinations(records, 2):
            overlap = min(ra[2], rb[2]) > max(ra[0], rb[0]) and min(ra[3], rb[3]) > max(ra[1], rb[1])
            assert not overlap, (a, b, ra, rb)
        return [r[0] for r in records]

    for page in (("tech", "detail") if training else ()):
        s.page = page
        for tech in range(3):
            s.tech = tech
            for i in range(len(s.choices())):
                s.index = i
                labels = check()
                if not learned and page == "tech" and i == 1:
                    assert "LLAMA" not in labels
                    assert "BLOQUEADA" in labels and "0 / 2" in labels
    if training:
        return
    for i in range(len(s.choices())):
        s.index = i
        check()
    # Three-digit maxima and changing HP/MP must not push HUD text offscreen.
    s.battle.player.hp = s.battle.player.max_hp = 238
    s.battle.player.mp = s.battle.player.max_mp = 109
    s.battle.rival.hp = s.battle.rival.max_hp = 238
    s.battle.rival.mp = s.battle.rival.max_mp = 109
    s.index = 1
    s.input("action", 1000)
    check()
    s.battle.player.mp = 0
    for i in range(len(s.choices())):
        s.index = i
        check()
    s.battle.result = "DERROTA"
    s.index = 0
    s.message = "ERROR AL GUARDAR"
    check()


def test_feedback_reports_order_and_substitution():
    s = session(learned=True)
    assert battle_feedback(s)[0] == "ESPERANDO ORDEN"
    s.battle.player.mp = 0
    s.index = 2
    s.input("action", 0)
    assert battle_feedback(s) == ("PEDIDO LLAMA / USO GOLPE", "SIN MP")
    s.input("next", 0)
    assert battle_feedback(s) == ("PEDIDO LLAMA / USO GOLPE", "SIN MP")


def test_render_changes_with_animation_time(practice_assets):
    s = session()
    assert render_practice(practice_assets, s, 0).tobytes() != render_practice(practice_assets, s, 100).tobytes()


@pytest.mark.parametrize("state", ["preview", "result", "no-energy", "maximum", "save-error"])
def test_training_carousel_text_fits_and_render_is_read_only(practice_assets, monkeypatch, state):
    s = TrainingSession(session().pet, lambda _: state != "save-error")
    records = []
    real_text = ImageDraw.ImageDraw.text

    def checked_text(draw, xy, value, *args, **kwargs):
        box = draw.textbbox(xy, value, font=kwargs["font"])
        assert 0 <= box[0] < box[2] <= 240, (value, box)
        assert 0 <= box[1] < box[3] <= 135, (value, box)
        records.append((value, box))
        return real_text(draw, xy, value, *args, **kwargs)

    monkeypatch.setattr(ImageDraw.ImageDraw, "text", checked_text)
    for i in range(8):
        s.index, s.message, s.gain, s.updated_at = i, "", None, None
        s.pet.stats["e"] = 100
        if state == "no-energy":
            s.pet.stats["e"] = 0
        elif state == "maximum":
            s.pet.ev = {stat: 252 for stat in s.pet.ev}
        if state in ("result", "save-error") and i < 6:
            s.input("action", 1000)
        records.clear()
        before = s.pet.to_dict()
        assert render_training(practice_assets, s, 1500).size == (240, 135)
        assert s.pet.to_dict() == before
        for (a, ra), (b, rb) in combinations(records, 2):
            overlap = min(ra[2], rb[2]) > max(ra[0], rb[0]) and min(ra[3], rb[3]) > max(ra[1], rb[1])
            assert not overlap, (a, b, ra, rb)


def test_simulator_dumbbell_route_and_held_action_do_not_repeat(practice_assets, monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    from scripts import sim

    saves, practices, trainings = [], [], []

    def create_practice(pet, save):
        controller = PracticeSession(pet, save)
        practices.append(controller)
        return controller

    def create_training(pet, save):
        controller = TrainingSession(pet, save)
        trainings.append(controller)
        return controller

    monkeypatch.setattr(sim, "parse_args", lambda: SimpleNamespace(
        profile="tdisplay", scale=1, build_dir=str(practice_assets), record=None,
        practice=True, training=False, max_frames=1))
    monkeypatch.setattr(sim, "PracticeSession", create_practice)
    monkeypatch.setattr(sim, "TrainingSession", create_training)
    monkeypatch.setattr(sim.SimulatorServices, "load", lambda self, pet: False)
    monkeypatch.setattr(sim.SimulatorServices, "save", lambda self, pet: saves.append(pet.to_dict()) or True)
    events = []

    def press(key, repeats=1):
        events.extend(sim.pygame.event.Event(sim.pygame.KEYDOWN, key=key) for _ in range(repeats))
        events.append(sim.pygame.event.Event(sim.pygame.KEYUP, key=key))

    for _ in range(3):
        press(sim.pygame.K_n)
    press(sim.pygame.K_a, repeats=2)  # retreat must not reopen battle while held
    for _ in range(7):
        press(sim.pygame.K_n)  # wrap home selection to the dumbbell
    press(sim.pygame.K_a, repeats=2)  # opening must not also train attack
    press(sim.pygame.K_n)  # one press selects defense
    press(sim.pygame.K_a, repeats=2)  # train defense exactly once
    press(sim.pygame.K_b)
    press(sim.pygame.K_n)
    press(sim.pygame.K_a, repeats=2)  # opening swords must not also execute a round
    monkeypatch.setattr(sim.pygame.event, "get", lambda: events)
    sim.main()
    assert len(trainings) == 1 and trainings[0].index == 1
    assert len(saves) == 1
    assert trainings[0].pet.training_sessions == 1
    assert trainings[0].pet.ev_at("def") == 6
    assert trainings[0].pet.ev_at("off") == 0
    assert len(practices) == 2 and practices[-1].page == "battle"
    assert practices[-1].battle.round == 0
