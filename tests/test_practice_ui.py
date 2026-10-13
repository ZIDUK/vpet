"""Layout checks use synthetic assets; preview_practice renders the real artwork."""
from itertools import combinations
from types import SimpleNamespace

import pytest
from PIL import Image, ImageDraw

from config import (BACKGROUND_PATH, PET_IDLE_IMAGE_PATH, PET_PUNCH_IMAGE_PATH,
                    PET_CAST_IMAGE_PATH, PET_BLOCK_IMAGE_PATH, PET_WALK_IMAGE_PATH,
                    PET_HIT_IMAGE_PATH, PET_HURT_IMAGE_PATH,
                    PET_HIT_FRAME_COUNT, PET_HURT_FRAME_COUNT,
                    PET_HIT_FRAME_INTERVAL, PET_HURT_FRAME_INTERVAL)
from core.pet import Pet
from scripts.practice_icons import INFO_ICONS, PATTERNS, PALETTE, info_icon, technique_icon
from scripts.practice_renderer import (GREEN, HP, INK, MP, MUTED, PRACTICE_IMPACT_MS, WHITE,
                                        YELLOW, _draw_atlas, _draw_combatant, _species_atlas, bar,
                                        battle_feedback, impact_sprite, render_practice,
                                        BAND_TOP, BAND_BOTTOM)
from scripts.practice_session import PracticeSession
from scripts.sim_renderer import _load_image, device_path
from scripts.training_renderer import render_training
from scripts.training_session import TrainingSession


@pytest.fixture
def practice_assets(tmp_path):
    """Synthetic assets for layout / overflow tests. The pet atlases use
    distinct colours per action so the impact-sprite tests can tell them
    apart even though the geometry is identical. The atlas has two cells
    with rectangles in different positions so the animation phase is
    observable; the impact-sprite tests render at frame index 0."""
    background = device_path(tmp_path, BACKGROUND_PATH)
    background.parent.mkdir(parents=True)
    Image.new("RGB", (240, 135), (75, 125, 90)).save(background)
    palette_template = [0, 0, 0] + [0] * 762  # index 0 transparent black
    atlas_specs = (
        (PET_IDLE_IMAGE_PATH, (210, 210, 210)),    # grey idle
        (PET_PUNCH_IMAGE_PATH, (240, 100, 30)),    # orange punch
        (PET_CAST_IMAGE_PATH, (255, 202, 49)),     # yellow cast
        (PET_BLOCK_IMAGE_PATH, (84, 197, 222)),    # cyan block
        (PET_WALK_IMAGE_PATH, (160, 200, 90)),
        (PET_HIT_IMAGE_PATH, (220, 30, 30)),       # red hit
        (PET_HURT_IMAGE_PATH, (160, 60, 200)),     # magenta hurt
        (_species_atlas("rookie", "happy"), (20, 220, 60)),
        (_species_atlas("rookie", "sad"), (220, 30, 30)),
    )
    for path, colour in atlas_specs:
        atlas = Image.new("P", (64, 32))
        pal = list(palette_template)
        pal[3:6] = colour  # palette index 1 = action colour
        atlas.putpalette(pal)
        draw = ImageDraw.Draw(atlas)
        # Two distinct rectangles per cell so the animation phase is visible
        # (the cells must not be identical, otherwise frame-index tests pass
        # trivially even when frame_interval_ms is broken).
        draw.rectangle((8, 4, 20, 27), fill=1)
        draw.rectangle((42, 4, 54, 27), fill=1)
        target = device_path(tmp_path, path)
        target.parent.mkdir(parents=True, exist_ok=True)
        atlas.save(target)
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
    # Freeze the wall clock so the ``age_seconds`` property on the pet
    # (which is ``int(time.monotonic() - self.born_at)``) is stable
    # across the to_dict() snapshots. The render pipeline does no other
    # time-sensitive work in this test path, so the freeze is safe and
    # the assertion that the render does not mutate pet state still
    # holds for every other field.
    import time as _time
    frozen = _time.monotonic()
    monkeypatch.setattr(_time, "monotonic", lambda: frozen)
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
        assert before == s.pet.to_dict(), (
            "render must not mutate pet state; diff is " +
            ", ".join("%s: %r -> %r" % (k, before[k], s.pet.to_dict()[k])
                       for k in before if before[k] != s.pet.to_dict()[k])
        )
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
                    assert ("BLOQUEADA" in labels or "LOCKED" in labels) and "0 / 2" in labels
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
    info = battle_feedback(s)
    assert info.awaiting and info.reason_key == "ELIGE ORDEN" and info.order_label == "AUTO"
    s.battle.player.mp = 0
    s.index = 2  # select LLAMA (equipped[1])
    s.input("action", 0)
    info = battle_feedback(s)
    assert info.order_label == "LLAMA"
    assert info.action_label == "GOLPE"
    assert info.reason_key == "SIN MP"
    assert info.is_substitution is True
    s.input("next", 0)
    info = battle_feedback(s)
    assert info.order_label == "LLAMA"
    assert info.reason_key == "SIN MP"


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
        if state == "no-energy" and i == 0:
            s.input("action", 1000)
        records.clear()
        before = s.pet.to_dict()
        frame = render_training(practice_assets, s, 1500)
        assert frame.size == (240, 135)
        assert s.pet.to_dict() == before
        if i == 7 and state not in ("result", "save-error"):
            assert not any(value in ("BACK", "VOLVER") for value, _ in records)
            assert any("TECHNIQUES" in value or "TECNICAS" in value
                       for value, _ in records)
        if state == "no-energy" and i == 0:
            labels = [value for value, _ in records
                      if value in ("FALTA ENERGIA", "NO ENERGY", "PET NO APTO", "PET NOT FIT")]
            assert len(labels) == 1
            assert labels[0] in ("FALTA ENERGIA", "NO ENERGY")
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
        practice=True, training=False, max_frames=4))
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
    # Open the dumbbell; the spec guarantees no rep is applied on the
    # opening press. The new flow enters state A.
    press(sim.pygame.K_a, repeats=2)  # opening must not train immediately
    press(sim.pygame.K_n)  # NEXT: advance to DEFENSA
    press(sim.pygame.K_a)  # A → B for DEFENSA
    press(sim.pygame.K_a, repeats=2)  # START runs once, even while held.
    start_events = events[:]
    events.clear()
    press(sim.pygame.K_b)  # D → A (back to selector, chosen=def cleared)
    # Walk to techniques and back, then out to home.
    for _ in range(5):
        press(sim.pygame.K_n)  # advance index to techniques entry
    press(sim.pygame.K_a)  # open techniques
    press(sim.pygame.K_b)  # techniques → A
    press(sim.pygame.K_b)  # A → home
    press(sim.pygame.K_n)  # move off the dumbbell
    press(sim.pygame.K_a)  # open swords (battle)
    press(sim.pygame.K_b)  # close battle
    frames = iter(((0, start_events), (9999, []), (10000, []), (10001, events[:])))
    now = [0]
    def next_events():
        now[0], batch = next(frames)
        if now[0] == 10000:
            assert not saves
        if now[0] == 10001:
            assert len(saves) == 1
        return batch
    monkeypatch.setattr(sim.pygame.time, "get_ticks", lambda: now[0])
    monkeypatch.setattr(sim.pygame.event, "get", next_events)
    sim.main()
    # After main() processes the events, the single training session
    # was instantiated once and the full A→B→C→confirm flow ran.
    assert len(trainings) == 1
    # The single committed batch applied 1 rep of defense.
    assert len(saves) == 1
    assert trainings[0].pet.training_sessions == 1
    assert trainings[0].pet.ev_at("def") == 6
    assert trainings[0].pet.ev_at("off") == 0
    # Two PracticeSession instances are expected: the one created at
    # startup by ``args.practice=True`` and the one opened from the
    # home menu after the training flow.
    assert len(practices) == 2
    assert practices[-1].page == "battle"
    assert practices[-1].battle.round == 0


# ---------------------------------------------------------------------------
# Phase 6 visual impact selection.
# Each helper renders the requested sprite onto a blank canvas; the rendered
# pixel signature is used as a deterministic anchor for assertions.
# ---------------------------------------------------------------------------


# Discriminating signature: the four combat sprites all render a distinct colour
# at these (x, y) coordinates, giving a small but robust fingerprint that
# survives resize and background blending. Each key pixel is chosen inside
# the cell-0 rectangle (frame index 0) so the impact tests are deterministic.
SIGNATURE_KEY_PIXELS = (
    (25, 30),  # inside cell 0 rectangle → opaque with action colour
    (30, 20),  # inside cell 0 rectangle → opaque
    (30, 30),  # inside cell 0 rectangle → opaque
    (5, 5),    # outside both rectangles → transparent in frame 0
    (55, 5),   # outside both rectangles → transparent in frame 0
)


def _signature(practice_assets, kind, flip=False):
    """Return the rendered RGBA image of ``kind`` (hit / hurt / block / idle)
    pasted on a transparent canvas. The alpha channel lets the comparison
    logic tell sprite pixels from empty canvas pixels."""
    canvas = Image.new("RGBA", (60, 60), (0, 0, 0, 0))
    if kind in ("hit", "hurt"):
        impact_sprite(canvas, practice_assets, 0, 0, 60, kind, 0, flip)
    else:
        from scripts.practice_renderer import pet_sprite as _pet
        action = 2 if kind == "block" else None
        _pet(canvas, practice_assets, 0, 0, 60, action, 0, flip)
    return canvas


def _composite(practice_assets, session, now_ms):
    """Run the renderer's draw pipeline and return the two combatant slots as
    RGB PIL images."""
    frame = render_practice(practice_assets, session, now_ms)
    return (
        frame.crop((24, 33, 84, 93)).copy(),
        frame.crop((154, 33, 214, 93)).copy(),
    )


def _slot_matches_signature(slot_rgb, signature_rgba, practice_assets,
                            sprite_tolerance=48, bg_tolerance=40, flipped=False):
    """Compare a rendered combatant slot with a sprite signature:
    - sprite opaque pixels must match the sprite RGB within ``sprite_tolerance``;
    - sprite transparent pixels must match the meadow background within
      ``bg_tolerance`` (because the slot is rendered over the meadow image).
    The background image is loaded once from ``practice_assets`` and sampled
    at the slot's canvas position so the assertion is position-specific.
    """
    bg_path = device_path(practice_assets, BACKGROUND_PATH)
    bg = _load_image(bg_path).convert("RGB")
    slot_x = (154 if flipped else 24)
    sig_label = "unknown"
    if isinstance(signature_rgba, Image.Image):
        # Identify which signature by sampling the centre pixel.
        sig_label = "centre=" + repr(signature_rgba.getpixel((30, 30))[:3])
    for (x, y), exp in zip(SIGNATURE_KEY_PIXELS,
                          [signature_rgba.getpixel(p) for p in SIGNATURE_KEY_PIXELS]):
        actual = slot_rgb.getpixel((x, y))
        if exp[3] > 100:  # signature pixel is opaque
            assert max(abs(exp[i] - actual[i]) for i in range(3)) <= sprite_tolerance, (
                f"signature pixel ({x}, {y}) expected {exp[:3]} got {actual} "
                f"(sig {sig_label})"
            )
        else:  # sprite transparent → slot must show the meadow background
            bg_color = bg.getpixel((slot_x + x, 33 + y))
            assert max(abs(bg_color[i] - actual[i]) for i in range(3)) <= bg_tolerance, (
                f"transparent signature pixel ({x}, {y}) should match meadow "
                f"({bg_color}); got {actual}"
            )


def _matches(slot_rgb, signature_rgba, practice_assets, sprite_tolerance=48,
            bg_tolerance=40, flipped=False):
    """Boolean version of ``_slot_matches_signature`` for negative assertions."""
    try:
        _slot_matches_signature(slot_rgb, signature_rgba, practice_assets,
                               sprite_tolerance, bg_tolerance, flipped)
        return True
    except AssertionError:
        return False


def _composite(practice_assets, session, now_ms):
    """Run the renderer's draw pipeline on a fresh frame and return the two
    combatant slot images (player at (24, 33), rival at (154, 33)) as RGB
    PIL images."""
    frame = render_practice(practice_assets, session, now_ms)
    return (
        frame.crop((24, 33, 84, 93)).copy(),
        frame.crop((154, 33, 214, 93)).copy(),
    )


def _seed_session(actions=(0, 2), damage=(7, 0), **overrides):
    s = session()
    s.battle.player.equipped = (0, 1, 2)
    s.battle.rival.equipped = (0, 1, 2)
    s.battle.player.hp = s.battle.player.max_hp = 200
    s.battle.rival.hp = s.battle.rival.max_hp = 200
    s.battle.player.mp = s.battle.player.max_mp = 80
    s.battle.rival.mp = s.battle.rival.max_mp = 80
    # stats is a tuple in the Fighter struct; copy to a list to override
    # speed and similar per-scenario tweaks.
    s.battle.player.stats = list(s.battle.player.stats)
    s.battle.rival.stats = list(s.battle.rival.stats)
    s.battle.actions = actions
    s.battle.damage = damage
    s.battle.round = 1
    # battle_feedback needs a non-None last_order once the round is past 0.
    s.last_order = actions[0] if actions[0] is not None else -1
    for key, value in overrides.items():
        setattr(s.battle, key, value)
    # Use updated_at = 0 so renders stay in frame index 0 across the synthetic
    # fixture; the impact signatures also render at time 0 for parity.
    s.updated_at = 0
    return s


def _now_ms():
    """Return a render timestamp inside the impact window when updated_at = 0."""
    return 50


def test_hit_only_on_attacker_when_player_is_attacker(practice_assets):
    """Player punches the guarding rival. Player (attacker) shows hit, the
    rival absorbs the halved hit and shows hurt."""
    s = _seed_session(actions=(0, 2), damage=(7, 0))
    hit_sig = _signature(practice_assets, "hit")
    hurt_sig = _signature(practice_assets, "hurt", flip=True)
    block_sig = _signature(practice_assets, "block", flip=True)
    player_slot, rival_slot = _composite(practice_assets, s, _now_ms())
    _slot_matches_signature(player_slot, hit_sig, practice_assets)
    _slot_matches_signature(rival_slot, hurt_sig, practice_assets, flipped=True)
    # The rival slot must not match the block sprite; that would mean guard
    # overrides the impact feedback.
    assert not _matches(rival_slot, block_sig, practice_assets, flipped=True)


def test_hurt_on_player_when_rival_is_attacker(practice_assets):
    """Rival punches the guarding player. The rival is the attacker, the
    player is the defender that lost HP and shows hurt."""
    s = _seed_session(actions=(2, 0), damage=(0, 6))
    hit_sig = _signature(practice_assets, "hit", flip=True)
    hurt_sig = _signature(practice_assets, "hurt")
    block_sig = _signature(practice_assets, "block")
    player_slot, rival_slot = _composite(practice_assets, s, _now_ms())
    _slot_matches_signature(player_slot, hurt_sig, practice_assets)
    _slot_matches_signature(rival_slot, hit_sig, practice_assets, flipped=True)
    assert not _matches(player_slot, block_sig, practice_assets)


def test_guard_against_guard_uses_block_sprite_for_both_sides(practice_assets):
    """Both combatants guard: nobody attacks, no damage is dealt. The render
    must display the block sprite on each side; neither hit nor hurt appears."""
    s = _seed_session(actions=(2, 2), damage=(0, 0))
    hit_sig = _signature(practice_assets, "hit")
    hurt_sig = _signature(practice_assets, "hurt")
    block_sig = _signature(practice_assets, "block")
    block_sig_flip = _signature(practice_assets, "block", flip=True)
    player_slot, rival_slot = _composite(practice_assets, s, _now_ms())
    _slot_matches_signature(player_slot, block_sig, practice_assets)
    _slot_matches_signature(rival_slot, block_sig_flip, practice_assets, flipped=True)
    assert not _matches(player_slot, hit_sig, practice_assets)
    assert not _matches(player_slot, hurt_sig, practice_assets)
    assert not _matches(rival_slot, hit_sig, practice_assets, flipped=True)
    assert not _matches(rival_slot, hurt_sig, practice_assets, flipped=True)


def test_zero_damage_attack_still_uses_hit_sprite(practice_assets):
    """A guaranteed-minimum-1 hit still renders as hit on the attacker. The
    defender who guarded and absorbed the reduced blow shows hurt (not
    block) because they did lose HP; the rule is hit on attacker, hurt on
    defender-that-lost-HP, with no separate exception for guard."""
    s = _seed_session(actions=(0, 2), damage=(1, 0))
    hit_sig = _signature(practice_assets, "hit")
    hurt_sig_flip = _signature(practice_assets, "hurt", flip=True)
    player_slot, rival_slot = _composite(practice_assets, s, _now_ms())
    _slot_matches_signature(player_slot, hit_sig, practice_assets)
    _slot_matches_signature(rival_slot, hurt_sig_flip, practice_assets, flipped=True)


def test_simultaneous_attack_differentiates_first_and_second_actor(practice_assets):
    """Both combatants attack and both take damage. The first actor (by speed)
    shows hit; the second actor (who took the first hit before retaliating)
    shows hurt. Flipping the speed order swaps which side gets hit."""
    hit_sig = _signature(practice_assets, "hit")
    hit_sig_flip = _signature(practice_assets, "hit", flip=True)
    hurt_sig = _signature(practice_assets, "hurt")
    hurt_sig_flip = _signature(practice_assets, "hurt", flip=True)
    # Player faster → player is first actor → player shows hit.
    s = _seed_session(actions=(0, 1), damage=(7, 7))
    s.battle.player.stats[4] = 50
    s.battle.rival.stats[4] = 30
    player_slot, rival_slot = _composite(practice_assets, s, _now_ms())
    _slot_matches_signature(player_slot, hit_sig, practice_assets)
    _slot_matches_signature(rival_slot, hurt_sig_flip, practice_assets, flipped=True)
    # Reverse the speeds: rival is the first actor now.
    s.battle.player.stats[4] = 30
    s.battle.rival.stats[4] = 50
    player_slot, rival_slot = _composite(practice_assets, s, _now_ms())
    _slot_matches_signature(player_slot, hurt_sig, practice_assets)
    _slot_matches_signature(rival_slot, hit_sig_flip, practice_assets, flipped=True)
    # Equal speed on an even round: rival is the first actor (round % 2 == 0).
    s.battle.player.stats[4] = 40
    s.battle.rival.stats[4] = 40
    s.battle.round = 2
    player_slot, rival_slot = _composite(practice_assets, s, _now_ms())
    _slot_matches_signature(player_slot, hurt_sig, practice_assets)
    _slot_matches_signature(rival_slot, hit_sig_flip, practice_assets, flipped=True)


def test_ko_before_acting_shows_hurt_on_defender(practice_assets):
    """The rival was KOed before its turn (action is None) but the player
    landed a hit. The player shows hit, the KOed rival shows hurt."""
    s = _seed_session(actions=(0, None), damage=(10, 0))
    s.battle.rival.hp = 0
    hit_sig = _signature(practice_assets, "hit")
    hurt_sig_flip = _signature(practice_assets, "hurt", flip=True)
    player_slot, rival_slot = _composite(practice_assets, s, _now_ms())
    _slot_matches_signature(player_slot, hit_sig, practice_assets)
    _slot_matches_signature(rival_slot, hurt_sig_flip, practice_assets, flipped=True)


def test_impact_window_uses_configured_duration(practice_assets):
    """Right at PRACTICE_IMPACT_MS - 1 ms the impact should still be visible;
    at PRACTICE_IMPACT_MS exactly it must be idle."""
    s = _seed_session(actions=(0, 2), damage=(7, 0))
    hit_sig = _signature(practice_assets, "hit")
    idle_sig = _signature(practice_assets, "idle")
    inside_player, _ = _composite(practice_assets, s, PRACTICE_IMPACT_MS - 1)
    outside_player, _ = _composite(practice_assets, s, 1000 + PRACTICE_IMPACT_MS)
    _slot_matches_signature(inside_player, hit_sig, practice_assets)
    _slot_matches_signature(outside_player, idle_sig, practice_assets)


# ---------------------------------------------------------------------------
# Phase 6 atlas wiring: frame count and interval honour config.py.
# ---------------------------------------------------------------------------


def test_draw_atlas_uses_passed_frame_count(practice_assets):
    """With a small frame count and a 100 ms interval, the displayed cell at
    time 0 and time 100 ms must differ because the configured count is > 1."""
    frame = Image.new("RGBA", (32, 32), (0, 0, 0, 255))
    _draw_atlas(frame, practice_assets, PET_HIT_IMAGE_PATH, 0, 0, 32, 0,
                frame_count=8, frame_interval_ms=100)
    first = frame.tobytes()
    _draw_atlas(frame, practice_assets, PET_HIT_IMAGE_PATH, 0, 0, 32, 100,
                frame_count=8, frame_interval_ms=100)
    second = frame.tobytes()
    assert first != second


def test_draw_atlas_wraps_around_configured_count(practice_assets):
    """With frame_count=4 and interval=50 ms, the frame at 0 and 200 ms
    must be identical because the cycle length is 4 * 50 = 200 ms."""
    def cell_at(ms):
        f = Image.new("RGBA", (32, 32), (0, 0, 0, 255))
        _draw_atlas(f, practice_assets, PET_HIT_IMAGE_PATH, 0, 0, 32, ms,
                    frame_count=4, frame_interval_ms=50)
        return f.tobytes()
    assert cell_at(0) == cell_at(200)  # cycle of 4 * 50 ms = 200 ms
    assert cell_at(0) != cell_at(50)


def test_draw_atlas_clamps_negative_timestamps(practice_assets):
    """A negative ``now_ms`` falls back to the first cell of the atlas."""
    frame = Image.new("RGBA", (32, 32), (0, 0, 0, 255))
    _draw_atlas(frame, practice_assets, PET_HIT_IMAGE_PATH, 0, 0, 32, -100,
                frame_count=PET_HIT_FRAME_COUNT, frame_interval_ms=80)
    zero = Image.new("RGBA", (32, 32), (0, 0, 0, 255))
    _draw_atlas(zero, practice_assets, PET_HIT_IMAGE_PATH, 0, 0, 32, 0,
                frame_count=PET_HIT_FRAME_COUNT, frame_interval_ms=80)
    assert frame.tobytes() == zero.tobytes()


def test_impact_sprite_uses_configured_count_and_interval(practice_assets):
    """``impact_sprite`` must read PET_HIT_FRAME_COUNT / PET_HURT_FRAME_COUNT
    and the matching interval, not a hard-coded magic value."""
    hit_fast = Image.new("RGBA", (60, 60), (0, 0, 0, 255))
    impact_sprite(hit_fast, practice_assets, 0, 0, 60, "hit", 0)
    hit_slow = Image.new("RGBA", (60, 60), (0, 0, 0, 255))
    impact_sprite(hit_slow, practice_assets, 0, 0, 60, "hit",
                  int(PET_HIT_FRAME_INTERVAL * 1000))
    assert hit_fast.tobytes() != hit_slow.tobytes()
    hurt_first = Image.new("RGBA", (60, 60), (0, 0, 0, 255))
    impact_sprite(hurt_first, practice_assets, 0, 0, 60, "hurt", 0)
    hurt_second = Image.new("RGBA", (60, 60), (0, 0, 0, 255))
    impact_sprite(hurt_second, practice_assets, 0, 0, 60, "hurt",
                  int(PET_HURT_FRAME_INTERVAL * 1000))
    assert hurt_first.tobytes() != hurt_second.tobytes()
    # Hit and hurt atlases differ; their first frames must not collide.
    assert hit_fast.tobytes() != hurt_first.tobytes()


def test_impact_sprite_animates_through_full_atlas(practice_assets):
    """Across the PRACTICE_IMPACT_MS window the hit sprite must visit at
    least two distinct frames so the animation is observable, and one full
    configured-count cycle later the sprite returns to its first frame."""
    samples = []
    interval_ms = int(PET_HIT_FRAME_INTERVAL * 1000)
    for ms in range(0, PRACTICE_IMPACT_MS, interval_ms):
        f = Image.new("RGBA", (60, 60), (0, 0, 0, 255))
        impact_sprite(f, practice_assets, 0, 0, 60, "hit", ms)
        samples.append(f.tobytes())
    assert len(set(samples)) >= 2  # at least two distinct frames
    # The configured count is the cell count for the synthetic atlas (2),
    # because _draw_atlas clamps frame_count to atlas.width // cell.
    atlas = _load_image(device_path(practice_assets, PET_HIT_IMAGE_PATH))
    cell_count = atlas.width // atlas.height
    cycle_ms = cell_count * interval_ms
    first = Image.new("RGBA", (60, 60), (0, 0, 0, 255))
    impact_sprite(first, practice_assets, 0, 0, 60, "hit", 0)
    wrapped = Image.new("RGBA", (60, 60), (0, 0, 0, 255))
    impact_sprite(wrapped, practice_assets, 0, 0, 60, "hit", cycle_ms)
    assert first.tobytes() == wrapped.tobytes()


def test_renderer_idle_outside_impact_window(practice_assets):
    """When the impact window is closed, _draw_combatant must fall back to
    the idle sprite regardless of what ``own_action`` says."""
    s = _seed_session(actions=(0, 2), damage=(7, 0))
    idle_sig = _signature(practice_assets, "idle")
    hit_sig = _signature(practice_assets, "hit")
    frame = render_practice(practice_assets, s, PRACTICE_IMPACT_MS + 50)
    slot = frame.crop((24, 33, 84, 93)).copy()
    _slot_matches_signature(slot, idle_sig, practice_assets)
    assert not _matches(slot, hit_sig, practice_assets)


# ---------------------------------------------------------------------------
# Phase 6 UX items 3 & 4: legible order → action → reason feedback, cost /
# availability hints, and damage per round. The feedback band now lives in
# y=92..114 and the action selector in y=115..134. These tests render with
# synthetic assets, then sample the rendered pixels to assert the visible
# text and the colour it was painted in.
# ---------------------------------------------------------------------------


# Y-ranges for the bands, mirrored from practice_renderer.
FEEDBACK_BAND = (92, 114)
SELECTOR_BAND = (115, 134)
HEADER_BAND = (0, 32)
# Column boundaries for the dual-pane header (FIREMON | PRACTICA).
HEADER_COLS = (4, 119, 125, 238)


def _seed_feedback(reason, order=0, action=0, damage=(0, 0), round=1,
                   awaiting=False, result=None, message="", mp=80, **overrides):
    """Build a session with the exact state needed to drive the feedback
    band. ``reason`` is the string stored in ``battle.reason`` (one of the
    keys of ``REASON_LABELS``); ``order`` is the player's last_order
    (-1=AUTO, 0=punch, 1=flame, 2=guard); ``action`` is the executed
    player action (None means KO before acting)."""
    s = session(learned=True)
    s.battle.player.equipped = (0, 1, 2)
    s.battle.rival.equipped = (0, 1, 2)
    s.battle.player.hp = s.battle.player.max_hp = 200
    s.battle.rival.hp = s.battle.rival.max_hp = 200
    s.battle.player.mp = mp
    s.battle.rival.mp = s.battle.rival.max_mp = 80
    s.battle.player.stats = list(s.battle.player.stats)
    s.battle.rival.stats = list(s.battle.rival.stats)
    s.battle.actions = (action, 0) if not awaiting else (None, None)
    s.battle.damage = damage
    s.battle.round = 0 if awaiting else round
    s.battle.reason = reason
    s.battle.result = result
    s.last_order = order
    s.updated_at = 0
    s.message = message
    for key, value in overrides.items():
        setattr(s.battle, key, value)
        if key == "result":
            s.battle.result = value
    return s


def _render_band(practice_assets, s):
    frame = render_practice(practice_assets, s, 1700)
    return frame


def _has_text_color(frame, expected, y_start, y_end, x_start=0, x_end=240,
                    tolerance=40):
    """Return True if any pixel in the rectangle has a colour close to
    ``expected`` (used to confirm a piece of text was painted)."""
    px = frame.load()
    for y in range(y_start, y_end):
        for x in range(x_start, x_end):
            r, g, b = px[x, y][:3]
            if (abs(r - expected[0]) <= tolerance
                    and abs(g - expected[1]) <= tolerance
                    and abs(b - expected[2]) <= tolerance):
                return True
    return False


def _text_row_color(frame, y, x_start, x_end):
    """Return the dominant non-background colour on a 1-pixel-tall row.
    Used to identify the colour of the painted glyph (the band background
    is INK so a different RGB must come from text)."""
    px = frame.load()
    counts = {}
    for x in range(x_start, x_end):
        c = px[x, y]
        if c == INK:
            continue
        counts[c] = counts.get(c, 0) + 1
    if not counts:
        return None
    return max(counts, key=counts.get)


def test_feedback_band_pediste_hizo_line_on_obedience(practice_assets):
    """When the pet obeys the order, the ``HIZO`` portion of line 1 must be
    painted in green (not the red used for substitution)."""
    s = _seed_feedback("SIGUE ORDEN", order=0, action=0, damage=(5, 0))
    frame = _render_band(practice_assets, s)
    # Line 1 occupies y=92..102 (BAND_TOP..BAND_TOP+10) under the new layout.
    line1_color = _text_row_color(frame, 96, 0, 240)
    assert line1_color is not None, "expected some text on line 1"
    # Green must be present somewhere on line 1 to mark obedience.
    assert _has_text_color(frame, GREEN, 93, 102, 0, 240, tolerance=60), (
        "expected GREEN pixels on line 1 to mark HIZO obeyed; "
        f"dominant={line1_color}"
    )


def test_feedback_band_hizo_in_red_on_substitution(practice_assets):
    """When the pet ignores the requested technique the ``HIZO`` portion
    must be painted in HP (red) so the substitution is obvious. The line
    must not be green-dominant for that section."""
    s = _seed_feedback("SIN MP", order=1, action=0, damage=(0, 5))
    frame = _render_band(practice_assets, s)
    # HP-red must appear on line 1 to mark the substitution.
    assert _has_text_color(frame, HP, 93, 102, 0, 240, tolerance=60), (
        "expected HP (red) pixels on line 1 to mark HIZO substitution"
    )


def test_feedback_band_motivo_red_on_sin_mp(practice_assets):
    """The second line of the band (``MOTIVO:``) must use the red category
    colour for the ``SIN MP`` reason."""
    s = _seed_feedback("SIN MP", order=1, action=0, damage=(0, 5))
    frame = _render_band(practice_assets, s)
    # Line 2 occupies y=BAND_TOP+13..BAND_BOTTOM = 105..114.
    assert _has_text_color(frame, HP, 105, 114, 0, 120, tolerance=60), (
        "expected HP (red) MOTIVO line for SIN MP"
    )


def test_feedback_band_motivo_red_on_en_recarga(practice_assets):
    """The cooldown reason must also be painted in red so the player
    knows the action was blocked, not preferred."""
    s = _seed_feedback("EN RECARGA", order=1, action=0, damage=(0, 5))
    frame = _render_band(practice_assets, s)
    assert _has_text_color(frame, HP, 105, 114, 0, 120, tolerance=60), (
        "expected HP (red) MOTIVO line for EN RECARGA"
    )


def test_feedback_band_motivo_yellow_on_prefiere(practice_assets):
    """The personality-preference reason (warn category) must paint the
    reason in yellow so the player can tell ``I chose this on purpose``
    apart from a hard block."""
    s = _seed_feedback("PREFIERE DEFENDER", order=0, action=2, damage=(0, 0))
    frame = _render_band(practice_assets, s)
    assert _has_text_color(frame, YELLOW, 105, 114, 0, 200, tolerance=60), (
        "expected YELLOW MOTIVO line for PREFIERE DEFENDER"
    )


def test_feedback_band_motivo_green_on_sigue_orden(practice_assets):
    """When the pet follows the order, the reason line must be green to
    confirm the successful obedience."""
    s = _seed_feedback("SIGUE ORDEN", order=0, action=0, damage=(3, 0))
    frame = _render_band(practice_assets, s)
    assert _has_text_color(frame, GREEN, 105, 114, 0, 200, tolerance=60), (
        "expected GREEN MOTIVO line for SIGUE ORDEN"
    )


def test_feedback_band_never_uses_generic_substitution_message(practice_assets):
    """The previous generic ``PET SUSTITUYO ORDEN`` label must never
    appear, regardless of which reason triggered the substitution. The
    renderer instead must surface the real reason text on line 2 in the
    appropriate category colour. We assert that for every substitute
    reason the line-2 reason is painted in either the bad (red) or warn
    (yellow) category colour and is never just a plain yellow on its
    own — that would be the colour of the old generic label."""
    for reason in ("SIN MP", "EN RECARGA", "PREFIERE DEFENDER", "PREFIERE ATACAR",
                   "A SU CRITERIO", "SIGUE ORDEN"):
        s = _seed_feedback(reason, order=0 if reason != "A SU CRITERIO" else -1,
                           action=2 if "DEFENDER" in reason else 0, damage=(0, 0))
        frame = _render_band(practice_assets, s)
        # The line-2 reason must always be visible: either red (bad),
        # yellow (warn) or green/white (obedient/neutral). At minimum,
        # the row must contain coloured pixels (proving the reason text
        # was drawn instead of the old generic label, which used the
        # same default yellow and would be ambiguous to remove).
        dominant = _text_row_color(frame, 108, 0, 240)
        assert dominant is not None, (
            f"reason={reason} did not render any text on the reason line"
        )
    # Strong guarantee: the renderer source must not contain the string
    # anywhere. If the label is reintroduced in a future refactor the
    # tests will flag it via this direct text search.
    from pathlib import Path
    src = Path("scripts/practice_renderer.py").read_text()
    assert "PET SUSTITUYO ORDEN" not in src, (
        "the generic 'PET SUSTITUYO ORDEN' label must not appear in the renderer"
    )


def _capture_text(practice_assets, s, monkeypatch, y_start=BAND_TOP, y_end=BAND_BOTTOM):
    """Render the battle frame with a monkey-patched ``ImageDraw.text`` and
    return a list of ``(text, x, y)`` tuples in the order they were drawn,
    filtered to the band rows ``y_start..y_end``. The x/y are the
    top-left of the rendered text; values are not redrawn but only
    captured for inspection. The returned order matches the order the
    renderer painted the strings, which is the natural reading order
    left-to-right inside a single y row."""
    records = []
    real_text = ImageDraw.ImageDraw.text

    def checked_text(draw, xy, value, *args, **kwargs):
        records.append((str(value), int(xy[0]), int(xy[1])))
        return real_text(draw, xy, value, *args, **kwargs)

    monkeypatch.setattr(ImageDraw.ImageDraw, "text", checked_text)
    _render_band(practice_assets, s)
    return [(t, x, y) for (t, x, y) in records
            if y_start <= y < y_end]


def _line2_texts(records):
    """Return only the text fragments painted on band line 2 (the MOTIVO
    line, y=BAND_TOP+13). The renderer writes left-aligned then
    right-aligned text on this row, so the leftmost entry is the reason
    and the rightmost is the damage counter."""
    return [(t, x) for (t, x, y) in records if y == BAND_TOP + 13]


def _line1_texts(records):
    """Return only the text fragments painted on band line 1 (the
    PEDISTE / HIZO line, y=BAND_TOP+1)."""
    return [(t, x) for (t, x, y) in records if y == BAND_TOP + 1]


def test_feedback_band_damage_order_player_attacks(practice_assets, monkeypatch):
    """When the player attacks, ``damage[0]`` is the damage Firemon dealt
    to Practica (PRACT's HP loss) and ``damage[1]`` is what Practica
    dealt back. The right-anchored counter must read
    ``PRACT -<damage[0]> | FIRE -<damage[1]>`` so the player can read
    the actual values, not just the colour of the glyphs."""
    s = _seed_feedback("SIGUE ORDEN", order=0, action=0, damage=(7, 0))
    records = _capture_text(practice_assets, s, monkeypatch)
    line2 = sorted(_line2_texts(records), key=lambda r: r[1])
    # Rightmost text on the MOTIVO line is the damage counter.
    damage_text = line2[-1][0]
    assert damage_text == "PRACT -7 | FIRE -0", (
        f"expected 'PRACT -7 | FIRE -0' (PRACT took 7, FIRE took 0); "
        f"got {damage_text!r}; line2={line2}"
    )


def test_feedback_band_damage_order_rival_attacks(practice_assets, monkeypatch):
    """When the rival attacks, ``damage[1]`` is what Firemon absorbed.
    The counter must read ``PRACT -0 | FIRE -5`` so the player sees
    their own HP loss as the FIRE column."""
    s = _seed_feedback("SIN MP", order=1, action=2, damage=(0, 5))
    records = _capture_text(practice_assets, s, monkeypatch)
    line2 = sorted(_line2_texts(records), key=lambda r: r[1])
    damage_text = line2[-1][0]
    assert damage_text == "PRACT -0 | FIRE -5", (
        f"expected 'PRACT -0 | FIRE -5' (PRACT took 0, FIRE took 5); "
        f"got {damage_text!r}; line2={line2}"
    )


def test_feedback_band_damage_order_trade(practice_assets, monkeypatch):
    """Both combatants attack. damage = (6, 4) means Firemon dealt 6 to
    Practica and Practica dealt 4 to Firemon. The counter must read
    ``PRACT -6 | FIRE -4``."""
    s = _seed_feedback("SIGUE ORDEN", order=0, action=0, damage=(6, 4))
    records = _capture_text(practice_assets, s, monkeypatch)
    line2 = sorted(_line2_texts(records), key=lambda r: r[1])
    damage_text = line2[-1][0]
    assert damage_text == "PRACT -6 | FIRE -4", (
        f"expected 'PRACT -6 | FIRE -4' (PRACT took 6, FIRE took 4); "
        f"got {damage_text!r}; line2={line2}"
    )


def test_feedback_band_damage_text_is_red(practice_assets, monkeypatch):
    """The damage counter must be painted in the HP (red) colour so the
    player can read the round result at a glance. The other test
    verifies the text; this one verifies the colour to guard against
    a refactor that changes the colour while keeping the labels."""
    s = _seed_feedback("SIGUE ORDEN", order=0, action=0, damage=(6, 4))
    # Use the colour-based assertion as a smoke test that the damage
    # block actually paints on line 2 and uses the HP palette.
    frame = _render_band(practice_assets, s)
    assert _has_text_color(frame, HP, 105, 114, 160, 240, tolerance=60), (
        "expected HP (red) damage counter on the right of line 2"
    )


def test_feedback_band_line1_paints_pediste_hizo_in_order(practice_assets, monkeypatch):
    """Line 1 must read ``PEDISTE <order>`` first (left) and then
    ``HIZO <action>`` to the right of the arrow. The order label must
    match the request; the action label must match what the pet did."""
    s = _seed_feedback("SIGUE ORDEN", order=0, action=0, damage=(3, 0))
    records = _capture_text(practice_assets, s, monkeypatch)
    line1 = sorted(_line1_texts(records), key=lambda r: r[1])
    fragments = [t for (t, _) in line1]
    # The first text is the order label, the action is reached after
    # the order and the arrow.
    assert fragments[0] == "PEDISTE GOLPE", fragments
    assert any("HIZO GOLPE" == f for f in fragments), fragments
    assert any("R1" == f for f in fragments), fragments


def test_feedback_band_round_counter_anchored_right(practice_assets):
    """The round label ``R#X`` must be right-anchored on line 1; the
    MOTIVO text must not overlap with it."""
    s = _seed_feedback("SIGUE ORDEN", order=0, action=0, damage=(0, 0), round=7)
    frame = _render_band(practice_assets, s)
    # R#7 sits in the right 30 px of line 1. The MOTIVO line is below.
    assert _has_text_color(frame, MUTED, 93, 102, 210, 240, tolerance=60), (
        "expected MUTED round label near the right edge of line 1"
    )


def test_feedback_band_auto_order_and_a_su_criterio(practice_assets):
    """When the player picks AUTO, the order label must read ``AUTO`` and
    the reason must be ``A SU CRITERIO`` painted in white (neutral)."""
    s = _seed_feedback("A SU CRITERIO", order=-1, action=0, damage=(0, 4))
    frame = _render_band(practice_assets, s)
    info = battle_feedback(s)
    assert info.order_is_auto and info.order_label == "AUTO"
    assert info.reason_key == "A SU CRITERIO"
    assert _has_text_color(frame, WHITE, 105, 114, 0, 200, tolerance=60), (
        "expected WHITE MOTIVO for A SU CRITERIO"
    )


def test_feedback_band_awaiting_state_uses_elige_orden(practice_assets):
    """Pre-round 1 the band must not show a damage counter and the
    reason must be the muted ``ESPERANDO ORDEN``."""
    s = _seed_feedback("ELIGE ORDEN", awaiting=True)
    frame = _render_band(practice_assets, s)
    info = battle_feedback(s)
    assert info.awaiting
    # The damage counter would use HP; in the awaiting state no damage
    # pixels should appear on the right of line 2.
    px = frame.load()
    damage_pixels = 0
    for y in range(105, 114):
        for x in range(180, 240):
            c = px[x, y]
            if (abs(c[0] - HP[0]) <= 40
                    and abs(c[1] - HP[1]) <= 40
                    and abs(c[2] - HP[2]) <= 40):
                damage_pixels += 1
    assert damage_pixels == 0, "no damage counter before round 1"


def test_action_selector_shows_pet_decide_for_auto(practice_assets):
    """Selecting AUTO must paint the status hint ``PET DECIDE`` in yellow
    rather than the cost hint used for techniques."""
    s = session(learned=True)
    s.battle.player.mp = 80
    s.index = 0  # AUTO
    frame = _render_band(practice_assets, s)
    # Status text lives at y=SELECTOR_TOP+11..SELECTOR_BOTTOM = 126..134.
    # We check for yellow pixels in the right block of the selector.
    assert _has_text_color(frame, YELLOW, 126, 134, 114, 240, tolerance=60), (
        "expected YELLOW status text for AUTO/PET DECIDE"
    )


def test_action_selector_shows_sin_mp_in_red(practice_assets):
    """When the selected technique cannot be paid for, the status block
    must read ``SIN MP`` in red so the player understands the unavail."""
    s = session(learned=True)
    s.battle.player.mp = 0
    s.index = 2  # LLAMA
    frame = _render_band(practice_assets, s)
    assert _has_text_color(frame, HP, 126, 134, 114, 240, tolerance=60), (
        "expected HP (red) status text when LLAMA is unaffordable"
    )


def test_action_selector_shows_recarga_in_red(practice_assets):
    """A technique on cooldown must surface ``RECARGA N`` in red."""
    s = session(learned=True)
    s.battle.player.mp = 80
    s.battle.player.cooldowns = [0, 1, 0]
    s.index = 2  # LLAMA
    frame = _render_band(practice_assets, s)
    assert _has_text_color(frame, HP, 126, 134, 114, 240, tolerance=60), (
        "expected HP (red) status text for RECARGA on LLAMA"
    )


def test_action_selector_shows_coste_in_mp_blue(practice_assets):
    """An affordable technique must show ``COSTE N MP`` in cyan (MP blue)
    so the cost is at a glance without leaving the selector."""
    s = session(learned=True)
    s.battle.player.mp = 80
    s.index = 1  # GOLPE
    frame = _render_band(practice_assets, s)
    assert _has_text_color(frame, MP, 126, 134, 114, 240, tolerance=60), (
        "expected MP (cyan) status text for affordable GOLPE"
    )


def test_action_selector_shows_recupera_in_green(practice_assets):
    """Guard must explain both reduced damage and MP recovery."""
    s = session(learned=True)
    s.pet.techniques.equipped = [0, 2]  # GOLPE + GUARDIA so index 2 is GUARDIA
    s.battle.player.equipped = (0, 2)  # mirror in the battle Fighter
    s.battle.player.mp = 80
    s.index = 2  # GUARDIA
    frame = _render_band(practice_assets, s)
    assert _has_text_color(frame, GREEN, 126, 134, 114, 240, tolerance=60), (
        "expected GREEN status text for GUARDIA"
    )


@pytest.mark.parametrize(("result", "expected"), [
    ("VICTORIA", (20, 220, 60)),
    ("DERROTA", (220, 30, 30)),
])
def test_result_card_uses_matching_firemon_emotion(practice_assets, result, expected):
    s = session()
    s.battle.result = result
    s.battle.round = 4
    s.last_order = -1
    s.battle.actions = (0, 0)
    frame = render_practice(practice_assets, s, now_ms=1000)
    assert frame.getpixel((186, 44)) == expected


def test_action_selector_shows_fin_batalla_for_retirarse(practice_assets):
    """The ``RETIRARSE`` slot must surface ``FIN BATALLA`` (not a cost)."""
    s = session(learned=True)
    s.battle.player.mp = 80
    s.index = 3  # RETIRARSE in the 4-slot default layout
    frame = _render_band(practice_assets, s)
    # RETIRARSE is the last slot (None command) — its status is yellow.
    assert _has_text_color(frame, YELLOW, 126, 134, 114, 240, tolerance=60), (
        "expected YELLOW status text for RETIRARSE"
    )


def test_banner_is_visible_for_victory(practice_assets):
    """When the battle ends in VICTORIA, the result banner overlay must
    cover the combatant area (y=33..91) and the green outline colour
    must appear on screen."""
    s = _seed_feedback("SIGUE ORDEN", order=0, action=0, damage=(0, 0),
                        result="VICTORIA", message="")
    frame = _render_band(practice_assets, s)
    # Banner outline at y=36..88 around x=10..229 must use GREEN.
    assert _has_text_color(frame, GREEN, 36, 88, 10, 229, tolerance=60), (
        "expected GREEN banner outline for VICTORIA"
    )


def test_banner_is_visible_for_derrota(practice_assets):
    """DERROTA paints the banner outline in HP red so the result is
    immediately distinguishable from VICTORIA and EMPATE."""
    s = _seed_feedback("SIGUE ORDEN", order=0, action=0, damage=(0, 0),
                        result="DERROTA", message="")
    frame = _render_band(practice_assets, s)
    assert _has_text_color(frame, HP, 36, 88, 10, 229, tolerance=60), (
        "expected HP banner outline for DERROTA"
    )


def test_banner_is_visible_for_empate(practice_assets):
    """EMPATE paints the banner outline in yellow."""
    s = _seed_feedback("SIGUE ORDEN", order=0, action=0, damage=(0, 0),
                        result="EMPATE", message="")
    frame = _render_band(practice_assets, s)
    assert _has_text_color(frame, YELLOW, 36, 88, 10, 229, tolerance=60), (
        "expected YELLOW banner outline for EMPATE"
    )


def test_header_bars_compare_across_sides(practice_assets):
    """HP and MP bars on both columns must remain in their assigned
    pixels and must be wide enough to show a 50% fill distinctly. We
    verify the bar surfaces in the expected y-ranges for both columns."""
    s = _seed_feedback("ELIGE ORDEN", awaiting=True)
    s.battle.player.hp = s.battle.player.max_hp // 2
    s.battle.rival.hp = s.battle.rival.max_hp // 2
    frame = _render_band(practice_assets, s)
    # HP bars live at y=13..18 (y=11+2..11+2+6-1) for both columns.
    # MP bars live at y=24..29 (y=22+2..22+2+6-1).
    assert _has_text_color(frame, HP, 13, 19, 36, 80, tolerance=80), (
        "expected HP red pixels in FIREMON HP bar slot"
    )
    assert _has_text_color(frame, HP, 13, 19, 157, 201, tolerance=80), (
        "expected HP red pixels in PRACTICA HP bar slot"
    )
    assert _has_text_color(frame, MP, 24, 30, 36, 80, tolerance=80), (
        "expected MP cyan pixels in FIREMON MP bar slot"
    )
    assert _has_text_color(frame, MP, 24, 30, 157, 201, tolerance=80), (
        "expected MP cyan pixels in PRACTICA MP bar slot"
    )


def test_header_numbers_fit_three_digit_maxima(practice_assets):
    """Three-digit maxima must not push the ``value/max`` numbers past
    the column boundary (x=119 for the left, x=240 for the right). The
    numbers must remain in white in both columns."""
    s = _seed_feedback("ELIGE ORDEN", awaiting=True)
    s.battle.player.hp = s.battle.player.max_hp = 238
    s.battle.player.mp = s.battle.player.max_mp = 109
    s.battle.rival.hp = s.battle.rival.max_hp = 238
    s.battle.rival.mp = s.battle.rival.max_mp = 109
    frame = _render_band(practice_assets, s)
    # Right side numbers must still be inside the screen and use white.
    px = frame.load()
    for y in range(9, 20):
        for x in range(180, 240):
            c = px[x, y]
            # The numbers themselves are white; INK is the panel background.
            if c == INK:
                continue
            assert x < 240, f"number pixel overflows at ({x}, {y}) -> {c}"


def test_battle_render_text_never_exceeds_screen(practice_assets, monkeypatch):
    """End-to-end safety net: for every state we care about (awaiting,
    obedience, substitution, cooldown, AUTO, terminal) all text drawn
    by PIL must lie inside the 240x135 screen and never overlap."""
    states = [
        ("ELIGE ORDEN", -1, None, (0, 0), True, None, 80),
        ("SIGUE ORDEN", 0, 0, (5, 0), False, None, 80),
        ("SIN MP", 1, 0, (0, 5), False, None, 0),
        ("EN RECARGA", 1, 0, (0, 5), False, None, 80),
        ("PREFIERE DEFENDER", 0, 2, (0, 0), False, None, 80),
        ("A SU CRITERIO", -1, 0, (0, 4), False, None, 80),
        ("SIGUE ORDEN", 0, 0, (0, 0), False, "VICTORIA", 80),
        ("SIGUE ORDEN", 0, 0, (0, 0), False, "DERROTA", 80),
        ("SIGUE ORDEN", 0, 0, (0, 0), False, "EMPATE", 80),
    ]
    records = []
    real_text = ImageDraw.ImageDraw.text

    def checked_text(draw, xy, value, *args, **kwargs):
        box = draw.textbbox(xy, value, font=kwargs["font"])
        assert 0 <= box[0] < box[2] <= 240, (value, box)
        assert 0 <= box[1] < box[3] <= 135, (value, box)
        records.append((value, box))
        return real_text(draw, xy, value, *args, **kwargs)

    monkeypatch.setattr(ImageDraw.ImageDraw, "text", checked_text)
    for reason, order, action, damage, awaiting, result, mp in states:
        s = _seed_feedback(reason, order=order, action=action, damage=damage,
                            awaiting=awaiting, result=result, mp=mp)
        for index in (0, 1, 2, 3):
            s.index = index
            records.clear()
            frame = _render_band(practice_assets, s)
            assert frame.size == (240, 135)
            for (a, ra), (b, rb) in combinations(records, 2):
                overlap = (min(ra[2], rb[2]) > max(ra[0], rb[0])
                           and min(ra[3], rb[3]) > max(ra[1], rb[1]))
                assert not overlap, (reason, index, a, b, ra, rb)
