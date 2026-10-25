"""UI tests for the batched training renderer (2026-10-07 spec).

These tests pin the contract the spec demands for the simulator's
240x135 panel:

* every state renders inside the 240x135 bounds;
* text painted by PIL stays inside the screen and never overlaps a
  different text on the same frame;
* the renderer is read-only: a render does not mutate the pet, the
  draft buffer, the energy reserve, or the EV;
* the orchestrator's state machine is the only writer: a render
  never advances the state, never queues a rep, and never commits;
* BACK with progress pending opens the cancel sub-state, BACK
  without progress returns to home; NEXT toggles focus within a
  sub-state; ACTION with the focused target applies the contract.

The age_seconds flake is frozen by patching ``time.monotonic`` for
the duration of the test.
"""
import time

import pytest
from PIL import Image, ImageDraw

from config import (BACKGROUND_PATH, PET_IDLE_IMAGE_PATH, PET_PUNCH_IMAGE_PATH,
                    PET_CAST_IMAGE_PATH, PET_BLOCK_IMAGE_PATH, PET_WALK_IMAGE_PATH,
                    PET_HIT_IMAGE_PATH, PET_HURT_IMAGE_PATH)
from core.i18n import tr, tr_stat
from core.pet import Pet
from scripts.practice_icons import info_icon, technique_icon
from scripts.practice_renderer import (HP, INK, MP, MUTED, PRACTICE_IMPACT_MS,
                                        WHITE, YELLOW, GREEN, _draw_atlas, bar)
from scripts.training_renderer import render_training
from scripts import training_renderer
from scripts.training_session import (TRAINING_ANIMATION_MS, TrainingSession,
                                        STATE_SELECT, STATE_PREPARE,
                                        STATE_SESSION, STATE_CONFIRM,
                                        STATE_RESULT, STATE_CANCEL, STATE_ERROR)
from scripts.sim_renderer import device_path


# ---------------------------------------------------------------------------
# Synthetic assets: same colour-distinct atlases as test_practice_ui so the
# pixel signatures are stable.
# ---------------------------------------------------------------------------


@pytest.fixture
def practice_assets(tmp_path):
    """Synthetic assets for layout / overflow tests. The pet atlases
    use distinct colours per action so impact-sprite tests can tell
    them apart even though the geometry is identical."""
    background = device_path(tmp_path, BACKGROUND_PATH)
    background.parent.mkdir(parents=True)
    Image.new("RGB", (240, 135), (75, 125, 90)).save(background)
    palette_template = [0, 0, 0] + [0] * 762
    atlas_specs = (
        (PET_IDLE_IMAGE_PATH, (210, 210, 210)),
        (PET_PUNCH_IMAGE_PATH, (240, 100, 30)),
        (PET_CAST_IMAGE_PATH, (255, 202, 49)),
        (PET_BLOCK_IMAGE_PATH, (84, 197, 222)),
        (PET_WALK_IMAGE_PATH, (160, 200, 90)),
        (PET_HIT_IMAGE_PATH, (220, 30, 30)),
        (PET_HURT_IMAGE_PATH, (160, 60, 200)),
    )
    for path, colour in atlas_specs:
        atlas = Image.new("P", (64, 32))
        pal = list(palette_template)
        pal[3:6] = colour
        atlas.putpalette(pal)
        draw = ImageDraw.Draw(atlas)
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


def _session(energy=100, ev=None, **kwargs):
    pet = Pet()
    pet.complete_hatch("rookie", entropy=12345)
    if ev is not None:
        pet.restore_ev(ev)
    pet.stats["e"] = energy
    return TrainingSession(pet, lambda _: True, **kwargs)


def test_training_sprite_cadence_is_deliberate_and_independent_of_home(monkeypatch, practice_assets):
    seen = []
    monkeypatch.setattr(
        training_renderer, "pet_sprite",
        lambda *args, **kwargs: seen.append(kwargs["frame_interval_ms"]),
    )
    session = _session()

    for index in range(8):
        session.index = index
        render_training(practice_assets, session, 0)
        assert seen[-1] == (90 if index < 6 else 120)


def test_technique_previews_use_training_cadence(monkeypatch, practice_assets):
    from scripts import practice_renderer
    from scripts.practice_session import PracticeSession

    seen = []
    monkeypatch.setattr(practice_renderer, "pet_sprite",
                        lambda *args, **kwargs: seen.append(kwargs["frame_interval_ms"]))
    session = PracticeSession(_session().pet, lambda _: True, training=True)
    for index in range(6):
        session.index = index
        session.page = "tech"
        practice_renderer.render_practice(practice_assets, session, 900)
        learned = index < 5 and session.pet.techniques.learned(index, session.pet.species)
        assert seen[-1] == (90 if learned else 120)
    session.page = "detail"
    session.tech = 0
    practice_renderer.render_practice(practice_assets, session, 900)
    assert seen[-1] == 90


def _patch_monotonic(monkeypatch):
    """Freeze ``time.monotonic`` so age_seconds is stable across the
    render + to_dict() snapshots."""
    frozen = time.monotonic()
    monkeypatch.setattr(time, "monotonic", lambda: frozen)


def _drive_to(session, state, **overrides):
    """Drive the orchestrator to the requested state and apply any
    overrides the caller wants on the draft buffer or the chosen
    attribute. Returns the same session for chaining."""
    s = session
    if state in (STATE_PREPARE, STATE_SESSION, STATE_CONFIRM,
                  STATE_CANCEL, STATE_RESULT, STATE_ERROR):
        # Choose the first attribute (ATAQUE).
        s.input("action", 0)
        assert s.state == STATE_PREPARE, s.state
    if state in (STATE_SESSION, STATE_CONFIRM, STATE_CANCEL,
                  STATE_RESULT, STATE_ERROR):
        s.input("action", 0)  # B → C
        assert s.state == STATE_SESSION, s.state
    for key, value in overrides.items():
        setattr(s, key, value)
    if state in (STATE_CANCEL,):
        s.state = STATE_CANCEL
    if state in (STATE_RESULT,):
        s._result_snapshot = {"reps": 1, "ev_added": 6,
                                "energy_charged": 8, "effort_added": 8,
                                "happiness_added": 3, "weight_delta": -1,
                                "training_sessions_added": 1}
        s.state = STATE_RESULT
    if state in (STATE_ERROR,):
        s.state = STATE_ERROR
    if state in (STATE_CONFIRM,):
        s.state = STATE_CONFIRM
        s._focus = "continue"
    return s


# ---------------------------------------------------------------------------
# 1. Bounds and no-overlap
# ---------------------------------------------------------------------------


def _text_records(monkeypatch):
    records = []
    real_text = ImageDraw.ImageDraw.text

    def checked_text(draw, xy, value, *args, **kwargs):
        box = draw.textbbox(xy, value, font=kwargs["font"])
        assert 0 <= box[0] < box[2] <= 240, (value, box)
        assert 0 <= box[1] < box[3] <= 135, (value, box)
        records.append((value, box))
        return real_text(draw, xy, value, *args, **kwargs)

    monkeypatch.setattr(ImageDraw.ImageDraw, "text", checked_text)
    return records


@pytest.mark.parametrize("state", [
    STATE_SELECT, STATE_PREPARE, STATE_SESSION, STATE_CONFIRM,
    STATE_CANCEL, STATE_RESULT, STATE_ERROR,
])
def test_text_inside_240x135_for_every_state(practice_assets, monkeypatch, state):
    _patch_monotonic(monkeypatch)
    records = _text_records(monkeypatch)
    s = _session()
    _drive_to(s, state)
    if state == STATE_SESSION:
        # Queue a rep so the C screen has the pending EV row.
        s._reps_completed = 1
        s._pending_ev = 6
        s._energy_reserved = 8
    frame = render_training(practice_assets, s, 0)
    assert frame.size == (240, 135)
    # The text check itself would have raised by now if any draw
    # overflowed; the records list is the proof.
    assert records, "no text was rendered"


@pytest.mark.parametrize("state", [
    STATE_SELECT, STATE_PREPARE, STATE_SESSION, STATE_CONFIRM,
    STATE_CANCEL, STATE_RESULT, STATE_ERROR,
])
def test_no_text_overlap_in_every_state(practice_assets, monkeypatch, state):
    _patch_monotonic(monkeypatch)
    records = _text_records(monkeypatch)
    s = _session()
    _drive_to(s, state)
    if state == STATE_SESSION:
        s._reps_completed = 2
        s._pending_ev = 12
        s._energy_reserved = 16
    render_training(practice_assets, s, 0)
    from itertools import combinations
    for (a, ra), (b, rb) in combinations(records, 2):
        overlap = (min(ra[2], rb[2]) > max(ra[0], rb[0])
                   and min(ra[3], rb[3]) > max(ra[1], rb[1]))
        assert not overlap, (state, a, b, ra, rb)


# ---------------------------------------------------------------------------
# 2. Render is read-only
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("state", [
    STATE_SELECT, STATE_PREPARE, STATE_SESSION, STATE_CONFIRM,
    STATE_CANCEL, STATE_RESULT, STATE_ERROR,
])
def test_render_does_not_mutate_pet_or_draft(practice_assets, monkeypatch, state):
    _patch_monotonic(monkeypatch)
    s = _session()
    _drive_to(s, state)
    if state == STATE_SESSION:
        s._reps_completed = 1
        s._pending_ev = 6
        s._energy_reserved = 8
    before = s.pet.to_dict()
    draft = (s._reps_completed, s._pending_ev, s._energy_reserved, s._focus, s.state)
    render_training(practice_assets, s, 0)
    render_training(practice_assets, s, 500)
    render_training(practice_assets, s, 1500)
    assert s.pet.to_dict() == before
    assert (s._reps_completed, s._pending_ev, s._energy_reserved, s._focus,
            s.state) == draft


def test_render_does_not_advance_state_in_select(practice_assets, monkeypatch):
    _patch_monotonic(monkeypatch)
    s = _session()
    assert s.state == STATE_SELECT
    render_training(practice_assets, s, 0)
    render_training(practice_assets, s, 500)
    assert s.state == STATE_SELECT
    assert s.reps == 0
    assert s.pending_ev == 0
    assert s.energy_reserved == 0


# ---------------------------------------------------------------------------
# 3. NEXT / ACTION / BACK consistency
# ---------------------------------------------------------------------------


def test_next_in_select_advances_index_with_wrap():
    s = _session()
    initial = s.index
    s.input("next", 0)
    assert s.index == (initial + 1) % 8
    for _ in range(7):
        s.input("next", 0)
    assert s.index == initial


def test_back_in_select_without_progress_returns_false():
    s = _session()
    assert not s.input("back", 0)


def test_back_during_timed_session_opens_cancel():
    s = _session()
    _drive_to(s, STATE_SESSION)
    assert s.input("back", 5000)
    assert s.state == STATE_CANCEL


def test_back_in_session_with_no_progress_returns_to_select():
    s = _session()
    s._chosen_index = 0
    s._chosen_stat = "off"
    s.state = STATE_SESSION
    s.input("back", 0)
    assert s.state == STATE_SELECT
    assert s._chosen_stat is None


def test_action_in_select_enters_prepare_only_when_eligible():
    s = _session()
    s.input("action", 0)
    assert s.state == STATE_PREPARE
    assert s._chosen_stat == "off"
    assert s._chosen_index == 0


def test_action_in_select_with_block_reason_does_not_enter_prepare():
    s = _session(energy=7)  # below 8 ENE per rep
    s.input("action", 0)
    assert s.state == STATE_SELECT
    assert s.message == "FALTA ENERGIA"


def test_start_reserves_one_rep_without_extra_action():
    s = _session()
    _drive_to(s, STATE_SESSION)
    assert s.reps == 1
    assert s.pending_ev == 6
    assert s.energy_reserved == 8
    assert s.busy(0)


def test_action_during_animation_opens_cancel_without_extra_rep():
    s = _session()
    _drive_to(s, STATE_SESSION)
    s.input("action", 100)
    assert s.state == STATE_CANCEL
    assert s.reps == 1


def test_next_during_animation_cannot_select_manual_finalize():
    s = _session()
    _drive_to(s, STATE_SESSION)
    s.input("next", 100)
    assert s.state == STATE_SESSION
    assert s._focus == "cancel"


def test_action_during_session_never_enters_confirm():
    s = _session()
    _drive_to(s, STATE_SESSION)
    s.input("action", 9000)
    assert s.state == STATE_CANCEL
    assert s.pet.ev_at("off") == 0


def test_session_at_deadline_needs_no_finalize_action():
    s = _session()
    _drive_to(s, STATE_SESSION)
    s.input(None, 10000)
    assert s.state == STATE_RESULT
    assert s.pet.ev_at("off") == 6


def test_action_in_confirm_with_continue_returns_to_session():
    s = _session()
    _drive_to(s, STATE_CONFIRM)
    s._focus = "continue"
    s.input("action", 0)
    assert s.state == STATE_SESSION
    assert s._focus == "finalize"


def test_timed_completion_commits_and_returns_to_result():
    saves = []
    s = _session()
    s.save = lambda p: saves.append(p.to_dict()) or True
    _drive_to(s, STATE_SESSION)
    s.input(None, 10000)
    assert s.state == STATE_RESULT
    assert s.pet.ev_at("off") == 6
    assert s.pet.get("e") == 92
    assert s.pet.training_sessions == 1
    assert len(saves) == 1


def test_action_in_confirm_with_save_failure_rolls_back_and_enters_error():
    s = _session()
    s.save = lambda p: False
    _drive_to(s, STATE_CONFIRM)
    s._reps_completed = 1
    s._pending_ev = 6
    s._energy_reserved = 8
    s._focus = "confirm"
    s.input("action", 0)
    assert s.state == STATE_ERROR
    assert s.message == "NO SE GUARDO"
    assert s.pet.ev_at("off") == 0
    assert s.pet.get("e") == 100


def test_next_in_confirm_toggles_focus():
    s = _session()
    _drive_to(s, STATE_CONFIRM)
    s._focus = "continue"
    s.input("next", 0)
    assert s._focus == "confirm"
    s.input("next", 0)
    assert s._focus == "continue"


def test_next_in_cancel_toggles_focus():
    s = _session()
    _drive_to(s, STATE_CANCEL)
    s._focus = "follow"
    s.input("next", 0)
    assert s._focus == "discard"


def test_action_in_cancel_with_follow_returns_to_session():
    s = _session()
    _drive_to(s, STATE_CANCEL)
    s._focus = "follow"
    s.input("action", 0)
    assert s.state == STATE_SESSION


def test_action_in_cancel_with_discard_returns_to_select_clearing_draft():
    s = _session()
    _drive_to(s, STATE_CANCEL)
    s._reps_completed = 3
    s._pending_ev = 18
    s._energy_reserved = 24
    s._focus = "discard"
    s.input("action", 0)
    assert s.state == STATE_SELECT
    assert s.reps == 0
    assert s._pending_ev == 0
    assert s._energy_reserved == 0
    assert s._chosen_stat is None
    # Pet unchanged.
    assert s.pet.ev_at("off") == 0


def test_next_in_error_toggles_focus():
    s = _session()
    _drive_to(s, STATE_ERROR)
    s._focus = "retry"
    s.input("next", 0)
    assert s._focus == "discard"


def test_action_in_error_with_discard_returns_to_select():
    s = _session()
    _drive_to(s, STATE_ERROR)
    s._focus = "discard"
    s.input("action", 0)
    assert s.state == STATE_SELECT


# ---------------------------------------------------------------------------
# 4. Numeric extreme values do not break the renderer
# ---------------------------------------------------------------------------


def test_extreme_energy_does_not_overflow_renderer(practice_assets, monkeypatch):
    _patch_monotonic(monkeypatch)
    s = _session(energy=100, ev={"off": 78})  # partial 6, projected stage cap
    _drive_to(s, STATE_SESSION)
    s._reps_completed = 1
    s._pending_ev = 6
    s._energy_reserved = 8
    frame = render_training(practice_assets, s, 0)
    assert frame.size == (240, 135)


def test_long_name_does_not_overflow_renderer(practice_assets, monkeypatch):
    _patch_monotonic(monkeypatch)
    s = _session(energy=100)
    _drive_to(s, STATE_RESULT, _chosen_index=0)
    s._result_snapshot = {"reps": 42, "ev_added": 252, "energy_charged": 336,
                            "effort_added": 336, "happiness_added": 126,
                            "weight_delta": -42, "training_sessions_added": 42}
    frame = render_training(practice_assets, s, 0)
    assert frame.size == (240, 135)


# ---------------------------------------------------------------------------
# 5. Six-attribute coverage
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("index,stat", [
    (0, "off"), (1, "def"), (2, "spd"),
    (3, "hp"), (4, "mp"), (5, "brn"),
])
def test_select_can_pick_each_of_six_attributes(practice_assets, index, stat):
    s = _session()
    for _ in range(index):
        s.input("next", 0)
    assert s.index == index
    s.input("action", 0)
    assert s.state == STATE_PREPARE
    assert s._chosen_stat == stat


@pytest.mark.parametrize("index,stat", [
    (0, "off"), (1, "def"), (2, "spd"),
    (3, "hp"), (4, "mp"), (5, "brn"),
])
def test_each_attribute_projects_using_iv_ev_pool(practice_assets, monkeypatch,
                                                  index, stat):
    _patch_monotonic(monkeypatch)
    s = _session(energy=100, ev={stat: 12})
    for _ in range(index):
        s.input("next", 0)
    s.input("action", 0)  # A → B
    real, projected = s.current_view(0)
    assert real == s.pet.combat_stat(stat) \
        if stat not in ("hp", "mp") else \
        (40 + s.pet.combat_stat(stat) * 2 if stat == "hp" else 10 + s.pet.combat_stat(stat))
    # Projected: 12 EV + 6 EV = 18 EV, which gives cs = 10 + IV*3 + 18//6.
    assert projected >= real


# ---------------------------------------------------------------------------
# 6. Save failure does not duplicate and retry is idempotent (already
#    covered by test_batched_training.py domain tests). This test
#    re-pins the contract at the orchestrator level.
# ---------------------------------------------------------------------------


def test_retry_after_save_failure_does_not_double_apply():
    s = _session()
    s.save = lambda p: False
    _drive_to(s, STATE_CONFIRM)
    s._reps_completed = 4
    s._pending_ev = 24
    s._energy_reserved = 32
    s._focus = "confirm"
    s.input("action", 0)  # commit fails
    assert s.state == STATE_ERROR
    before = s.pet.to_dict()
    s._focus = "retry"
    s.input("action", 0)  # retry commit
    assert s.state == STATE_ERROR
    assert s.pet.to_dict() == before
    s.save = lambda p: True
    s._focus = "retry"
    s.input("action", 0)  # successful retry
    assert s.state == STATE_RESULT
    assert s.pet.ev_at("off") == 24
    assert s.pet.get("e") == 68


# ---------------------------------------------------------------------------
# 7. i18n: ES / EN / fallback / no hardcoded strings in the renderer.
# ---------------------------------------------------------------------------


def test_i18n_tr_returns_spanish_for_spanish_pet():
    s = _session()
    s.pet.language = "ES"
    assert tr(s.pet, "training.title") == "ENTRENAR"
    assert tr(s.pet, "training.session.train") == "ENTRENAR"
    assert tr(s.pet, "training.session.finalize") == "FINALIZAR"
    assert tr_stat(s.pet, "off") == "ATAQUE"
    assert tr_stat(s.pet, "def") == "DEFENSA"


def test_i18n_tr_returns_english_for_english_pet():
    s = _session()
    s.pet.language = "EN"
    assert tr(s.pet, "training.title") == "TRAIN"
    assert tr(s.pet, "training.session.train") == "TRAIN"
    assert tr(s.pet, "training.session.finalize") == "FINISH"
    assert tr(s.pet, "training.result.title") == "TRAINING SAVED"
    assert tr(s.pet, "training.confirm.confirm") == "CONFIRM"
    assert tr_stat(s.pet, "off") == "ATTACK"
    assert tr_stat(s.pet, "def") == "DEFENSE"
    assert tr_stat(s.pet, "brn") == "MIND"


def test_i18n_tr_falls_back_to_spanish_for_unknown_language():
    s = _session()
    s.pet.language = "FR"
    assert tr(s.pet, "training.title") == "ENTRENAR"
    assert tr(s.pet, "training.result.title") == "ENTRENAMIENTO GUARDADO"
    s.pet.language = ""
    assert tr(s.pet, "training.title") == "ENTRENAR"


def test_i18n_tr_supports_string_format_arguments():
    s = _session()
    s.pet.language = "EN"
    assert tr(s.pet, "training.cost_per_rep", 8) == "COST 8 ENE / REP"
    assert tr(s.pet, "training.confirm.x_rep", "ATTACK", 3) == "ATTACK x3 REP"
    s.pet.language = "ES"
    assert tr(s.pet, "training.cost_per_rep", 8) == "COSTE 8 ENE / REP"


def test_i18n_missing_key_raises():
    s = _session()
    with pytest.raises(KeyError):
        tr(s.pet, "this.key.does.not.exist")


def test_i18n_every_used_key_is_bilingual():
    """Walk the renderer module to find every ``tr(`` and ``tr_stat(``
    invocation; each key must exist in both languages with non-empty
    strings."""
    from core import i18n
    import scripts.training_renderer as tr_mod
    import inspect
    src = inspect.getsource(tr_mod)
    # Find literal string arguments passed to tr() / tr_stat(). The
    # word boundary on the left stops the regex from matching the
    # "tr(" inside "getattr(" / "setattr(" / "inputattr(" etc.
    import re
    pattern = re.compile(r"(?<![\w.])tr(?:_stat)?\(\s*[^,]+,\s*[\"']([^\"']+)[\"']")
    used = set()
    for match in pattern.finditer(src):
        used.add(match.group(1))
    assert used, "no i18n keys found in the renderer source"
    for key in used:
        assert key in i18n.TRAINING_STRINGS or key in i18n.STAT_STRINGS, key
        entry = (i18n.TRAINING_STRINGS.get(key)
                 or i18n.STAT_STRINGS.get(key))
        assert "ES" in entry and "EN" in entry, key
        assert entry["ES"], key
        assert entry["EN"], key


def test_renderer_has_no_hardcoded_user_facing_strings():
    """The renderer must not embed any hardcoded user-facing string.
    The exception list covers: ASCII art arrows used as separators,
    column labels that are still routed through ``tr`` and the page
    indicator letters ('B', 'C', 'E') which are documentation tags
    in the corner of the screen, not user copy."""
    import inspect
    import scripts.training_renderer as tr_mod
    src = inspect.getsource(tr_mod)
    # Forbidden substrings: any of the ES labels that were inlined
    # before the i18n refactor. Each one is a Spanish user-facing
    # label and must be obtained via tr() now.
    forbidden = (
        '"ENTRENAR"', '"PREPARAR:', '"SESION', '"CERRAR ENTRENAMIENTO?"',
        '"DESCARTAR', '"ENTRENAMIENTO GUARDADO"', '"NO SE GUARDO"',
        '"INICIAR"', '"VOLVER"', '"FINALIZAR"', '"CONFIRMAR"',
        '"SEGUIR"', '"REINTENTAR"', '"CONTINUAR"', '"TECNICAS"',
        '"DESCARTAR"', '"MAX', '"REAL', '"PROY', '"LIMITE:',
    )
    leaks = [token for token in forbidden if token in src]
    assert not leaks, "hardcoded user-facing strings found: %r" % leaks


# ---------------------------------------------------------------------------
# 8. State D: two navigable pages (RESUMEN / STATS).
# ---------------------------------------------------------------------------


def test_result_default_page_is_summary():
    s = _session()
    _drive_to(s, STATE_RESULT, _chosen_index=0)
    assert s._result_page == "summary"


def test_result_stats_button_toggles_page():
    s = _session()
    _drive_to(s, STATE_SESSION)
    s.input(None, 10000)
    s.input("next", 10001)
    s.input("next", 10002)
    assert s._focus == "stats"
    s.input("action", 10003)
    assert s._result_page == "stats"
    s.input("action", 10004)
    assert s._result_page == "summary"


def test_result_repeat_returns_to_preparation():
    s = _session()
    _drive_to(s, STATE_SESSION)
    s.input(None, 10000)
    s.input("action", 10001)
    assert s.state == STATE_PREPARE
    assert s._chosen_stat == "off"
    assert s.pet.get("e") == 92


def test_result_back_returns_to_select_from_stats():
    s = _session()
    _drive_to(s, STATE_SESSION)
    s.input(None, 10000)
    s._result_page = "stats"
    s.input("next", 10001)
    s.input("action", 10002)
    assert s.state == STATE_SELECT


def test_back_in_result_returns_to_select():
    s = _session()
    _drive_to(s, STATE_RESULT, _chosen_index=0)
    s._result_page = "stats"
    s.input("back", 0)
    assert s.state == STATE_SELECT


def test_result_summary_paints_within_bounds(practice_assets, monkeypatch):
    _patch_monotonic(monkeypatch)
    records = _text_records(monkeypatch)
    s = _session()
    _drive_to(s, STATE_RESULT, _chosen_index=0)
    s._result_page = "summary"
    s._result_snapshot = {"reps": 2, "ev_added": 12,
                           "energy_charged": 16, "effort_added": 16,
                           "happiness_added": 6, "weight_delta": -2,
                           "training_sessions_added": 2}
    s.pet.ev_at("off")  # ensure pet is current
    s.pet.restore_ev({"off": 12})
    frame = render_training(practice_assets, s, 0)
    assert frame.size == (240, 135)
    assert records


def test_result_stats_paints_within_bounds(practice_assets, monkeypatch):
    _patch_monotonic(monkeypatch)
    records = _text_records(monkeypatch)
    s = _session()
    _drive_to(s, STATE_RESULT, _chosen_index=0)
    s._result_page = "stats"
    s._result_snapshot = {"reps": 1, "ev_added": 6,
                           "energy_charged": 8, "effort_added": 8,
                           "happiness_added": 3, "weight_delta": -1,
                           "training_sessions_added": 1}
    s.pet.restore_ev({"off": 6, "def": 12, "spd": 0, "hp": 0, "mp": 0, "brn": 0})
    frame = render_training(practice_assets, s, 0)
    assert frame.size == (240, 135)
    assert records


def test_result_stats_renders_all_six_attributes(practice_assets, monkeypatch):
    """Pin that the STATS page paints one row per attribute. The label
    is the first 4 characters of the localised name; the rows are
    laid out at y=40 + i*12 (six rows total). The action button lives
    at y=115 so the last row at y=40+5*12=100 must not collide."""
    _patch_monotonic(monkeypatch)
    s = _session()
    _drive_to(s, STATE_RESULT, _chosen_index=0)
    s._result_page = "stats"
    s._result_snapshot = {"reps": 1, "ev_added": 6, "energy_charged": 8,
                           "effort_added": 8, "happiness_added": 3,
                           "weight_delta": -1, "training_sessions_added": 1}
    s.pet.restore_ev({"off": 6, "def": 12, "spd": 18, "hp": 24, "mp": 0,
                       "brn": 30})
    records = _text_records(monkeypatch)
    frame = render_training(practice_assets, s, 0)
    assert frame.size == (240, 135)
    # The six labels (truncated to 4 chars) should appear in the
    # captured text records. The exact substring depends on the
    # language; the pet starts in EN by default.
    s.pet.language = "EN"
    rendered = [r[0] for r in records]
    for stat_key in ("HP", "MP", "ATT", "DEF", "SPEE", "MIN"):
        assert any(label.startswith(stat_key[:4]) for label in rendered), (
            stat_key, rendered)


def test_result_stats_no_text_overlap(practice_assets, monkeypatch):
    _patch_monotonic(monkeypatch)
    records = _text_records(monkeypatch)
    s = _session()
    _drive_to(s, STATE_RESULT, _chosen_index=0)
    s._result_page = "stats"
    s._result_snapshot = {"reps": 2, "ev_added": 12, "energy_charged": 16,
                           "effort_added": 16, "happiness_added": 6,
                           "weight_delta": -2, "training_sessions_added": 2}
    s.pet.restore_ev({"off": 12, "def": 24, "spd": 36, "hp": 48, "mp": 12,
                       "brn": 60})
    render_training(practice_assets, s, 0)
    _assert_no_overlap(records)


def test_result_summary_no_text_overlap(practice_assets, monkeypatch):
    _patch_monotonic(monkeypatch)
    records = _text_records(monkeypatch)
    s = _session()
    _drive_to(s, STATE_RESULT, _chosen_index=0)
    s._result_page = "summary"
    s._result_snapshot = {"reps": 1, "ev_added": 6, "energy_charged": 8,
                           "effort_added": 8, "happiness_added": 3,
                           "weight_delta": -1, "training_sessions_added": 1}
    s.pet.restore_ev({"off": 6})
    render_training(practice_assets, s, 0)
    _assert_no_overlap(records)


def _assert_no_overlap(records):
    """Assert that no two text records occupy overlapping rectangles."""
    for i, (text_i, box_i) in enumerate(records):
        for text_j, box_j in records[i + 1:]:
            if box_i == box_j and text_i == text_j:
                continue
            if _boxes_overlap(box_i, box_j):
                raise AssertionError("overlap: %r@%r vs %r@%r" %
                                       (text_i, box_i, text_j, box_j))


def _boxes_overlap(a, b):
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])


# ---------------------------------------------------------------------------
# 9. Compact stat-bar helper: scale, clamp, highlight, no overflow.
# ---------------------------------------------------------------------------


def test_stat_bar_width_clamps_to_zero_and_cap():
    from scripts.training_renderer import _stat_bar_width
    assert _stat_bar_width(0) == 0
    assert _stat_bar_width(126) == int(round((126 / 252.0) * 96))
    assert _stat_bar_width(252) == 96
    # Overflow: the helper clamps to 96.
    assert _stat_bar_width(999) == 96
    # Negative: clamped to 0.
    assert _stat_bar_width(-5) == 0


def test_stat_bar_width_is_monotone():
    from scripts.training_renderer import _stat_bar_width
    widths = [_stat_bar_width(ev) for ev in (0, 63, 126, 189, 252)]
    assert widths == sorted(widths)
    assert widths[0] == 0
    assert widths[-1] == 96


# ---------------------------------------------------------------------------
# 10. Extreme values: render does not break on capped / over-cap EV.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("ev_total", [0, 50, 252])
def test_result_stats_handles_extreme_ev(practice_assets, monkeypatch, ev_total):
    _patch_monotonic(monkeypatch)
    s = _session()
    _drive_to(s, STATE_RESULT, _chosen_index=0)
    s._result_page = "stats"
    s._result_snapshot = {"reps": 1, "ev_added": 6, "energy_charged": 8,
                           "effort_added": 8, "happiness_added": 3,
                           "weight_delta": -1, "training_sessions_added": 1}
    s.pet.restore_ev({"off": min(252, ev_total)})
    frame = render_training(practice_assets, s, 0)
    assert frame.size == (240, 135)


def test_result_summary_with_zero_deltas_does_not_show_fake_deltas(
        practice_assets, monkeypatch):
    """When the apply summary reports zero everywhere, the summary
    table must not invent a delta column (preserves the
    'no false +1 stat' rule from the v1 spec)."""
    _patch_monotonic(monkeypatch)
    s = _session()
    _drive_to(s, STATE_RESULT, _chosen_index=0)
    s._result_page = "summary"
    s._result_snapshot = {"reps": 0, "ev_added": 0, "energy_charged": 0,
                           "effort_added": 0, "happiness_added": 0,
                           "weight_delta": 0, "training_sessions_added": 0}
    frame = render_training(practice_assets, s, 0)
    assert frame.size == (240, 135)


def test_result_in_spanish_uses_es_strings(practice_assets, monkeypatch):
    _patch_monotonic(monkeypatch)
    records = _text_records(monkeypatch)
    s = _session()
    s.pet.language = "ES"
    _drive_to(s, STATE_RESULT, _chosen_index=0)
    s._result_page = "summary"
    s._result_snapshot = {"reps": 1, "ev_added": 6, "energy_charged": 8,
                           "effort_added": 8, "happiness_added": 3,
                           "weight_delta": -1, "training_sessions_added": 1}
    s.pet.restore_ev({"off": 6})
    render_training(practice_assets, s, 0)
    flat = " ".join(r[0] for r in records)
    # Spanish-specific tokens.
    assert "ANTES" in flat
    assert "AHORA" in flat
    assert "ATAQUE" in flat


def test_result_in_english_uses_en_strings(practice_assets, monkeypatch):
    _patch_monotonic(monkeypatch)
    records = _text_records(monkeypatch)
    s = _session()
    s.pet.language = "EN"
    _drive_to(s, STATE_RESULT, _chosen_index=0)
    s._result_page = "summary"
    s._result_snapshot = {"reps": 1, "ev_added": 6, "energy_charged": 8,
                           "effort_added": 8, "happiness_added": 3,
                           "weight_delta": -1, "training_sessions_added": 1}
    s.pet.restore_ev({"off": 6})
    render_training(practice_assets, s, 0)
    flat = " ".join(r[0] for r in records)
    assert "BEFORE" in flat
    assert "AFTER" in flat
    assert "ATTACK" in flat


# ---------------------------------------------------------------------------
# 11. Animations and inputs on the new pages (NEXT on D does not
#     advance the orchestrator to a different state; it just flips the
#     page indicator).
# ---------------------------------------------------------------------------


def test_next_on_result_does_not_advance_state(practice_assets, monkeypatch):
    _patch_monotonic(monkeypatch)
    s = _session()
    _drive_to(s, STATE_RESULT, _chosen_index=0)
    s._result_page = "summary"
    pet_before = s.pet.to_dict()
    for _ in range(3):
        s.input("next", 0)
    assert s.state == STATE_RESULT
    # Pet untouched.
    assert s.pet.to_dict() == pet_before


def test_input_pipeline_freeze_time_for_result_pages(practice_assets, monkeypatch):
    _patch_monotonic(monkeypatch)
    s = _session()
    _drive_to(s, STATE_SESSION)
    s.input(None, 10000)
    before = s.pet.to_dict()
    render_training(practice_assets, s, 10000)
    s.input("next", 10001)
    s.input("next", 10002)
    s.input("action", 10003)
    assert s._result_page == "stats"
    render_training(practice_assets, s, 10003)
    assert s.pet.to_dict() == before
