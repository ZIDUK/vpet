"""Generate reproducible native-resolution previews without changing a save."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from PIL import Image
from core.pet import Pet
from scripts.practice_session import PracticeSession
from scripts.practice_renderer import render_practice
from scripts.practice_icons import INFO_ICONS, info_icon
from scripts.training_session import (TRAINING_ANIMATION_MS, TrainingSession,
                                       STATE_SELECT, STATE_PREPARE,
                                       STATE_SESSION, STATE_CONFIRM,
                                       STATE_RESULT, STATE_CANCEL, STATE_ERROR)
from scripts.training_renderer import (render_training, RESULT_PAGE_SUMMARY,
                                        RESULT_PAGE_STATS)


# ---------------------------------------------------------------------------
# Locale-aware capture helpers
# ---------------------------------------------------------------------------


def _make_session():
    """Fresh pet + session. The pet is fully alive, EV is 0 in every
    stat, energy at 100. The session uses a save callback that always
    returns True so the orchestrator can commit during the previews
    that exercise state D (none of them actually call commit; the
    summary is set directly)."""
    pet = Pet()
    pet.complete_hatch("rookie", entropy=12345)
    return TrainingSession(pet, lambda _: True)


def _drive_to_state_d(training):
    """Drive a session all the way through B->C->D with a deterministic
    draft. Mirrors the legacy preview recipe."""
    training.input("action", 0)  # A -> B (ATAQUE)
    assert training.state == STATE_PREPARE
    training.input("action", 0)  # B -> C
    assert training.state == STATE_SESSION
    training._reps_completed = 3
    training._pending_ev = 18
    training._energy_reserved = 24
    return training


def capture_training_for_language(output, language, build_dir):
    """Render the eight training states plus the two result pages
    (RESUMEN / STATS) for a given language. Saves them as
    ``training-<state>-<lang>.png`` and ``training-result-stats-<lang>.png``
    so both languages sit side by side without overwriting each other."""
    pet = Pet()
    pet.complete_hatch("rookie", entropy=12345)
    pet.language = language
    training = TrainingSession(pet, lambda _: True)
    saved = []
    # State A: focused on ATAQUE.
    frame = render_training(build_dir, training, 0)
    frame.save(output / ("training-select-" + language.lower() + ".png"))
    saved.append(("training-select-" + language.lower(), frame))
    # State A: focused on DEFENSA (one NEXT from ATAQUE).
    training.input("next", 0)
    frame = render_training(build_dir, training, 0)
    frame.save(output / ("training-select-def-" + language.lower() + ".png"))
    saved.append(("training-select-def-" + language.lower(), frame))
    # State B.
    training.input("action", 0)
    assert training.state == STATE_PREPARE
    frame = render_training(build_dir, training, 0)
    frame.save(output / ("training-prepare-" + language.lower() + ".png"))
    saved.append(("training-prepare-" + language.lower(), frame))
    # State C with 3 reps.
    training.input("action", 0)
    assert training.state == STATE_SESSION
    training._reps_completed = 3
    training._pending_ev = 18
    training._energy_reserved = 24
    frame = render_training(build_dir, training, 0)
    frame.save(output / ("training-session-" + language.lower() + ".png"))
    saved.append(("training-session-" + language.lower(), frame))
    # State C at cap.
    pet_cap = Pet()
    pet_cap.complete_hatch("rookie", entropy=12345)
    pet_cap.language = language
    pet_cap.ev["off"] = 250
    cap_session = TrainingSession(pet_cap, lambda _: True)
    cap_session.input("action", 0)
    cap_session.input("action", 0)
    cap_session._reps_completed = 1
    cap_session._pending_ev = 2
    cap_session._energy_reserved = 8
    frame = render_training(build_dir, cap_session, 0)
    frame.save(output / ("training-session-cap-" + language.lower() + ".png"))
    saved.append(("training-session-cap-" + language.lower(), frame))
    # Sub-state confirm.
    training._focus = "confirm"
    training.state = STATE_CONFIRM
    frame = render_training(build_dir, training, 0)
    frame.save(output / ("training-confirm-" + language.lower() + ".png"))
    saved.append(("training-confirm-" + language.lower(), frame))
    # State D page 1 (summary).
    training._result_snapshot = {"reps": 3, "ev_added": 18,
                                   "energy_charged": 24, "effort_added": 24,
                                   "happiness_added": 9, "weight_delta": -3,
                                   "training_sessions_added": 3}
    # Mirror the post-apply EV on the pet so the result page shows a
    # realistic before -> after jump. Without this the bars on the
    # STATS page would be empty and the summary would show +18 from
    # 0 to 0, which is misleading.
    pet.ev["off"] = training._result_snapshot["ev_added"]
    pet.stats["e"] = max(0, pet.stats["e"] - training._result_snapshot["energy_charged"])
    pet.effort = min(100, getattr(pet, "effort", 0) + training._result_snapshot["effort_added"])
    training.state = STATE_RESULT
    training._result_page = RESULT_PAGE_SUMMARY
    frame = render_training(build_dir, training, 0)
    frame.save(output / ("training-result-" + language.lower() + ".png"))
    saved.append(("training-result-" + language.lower(), frame))
    # State D page 2 (stats). NEXT toggles the page.
    training.input("next", 0)
    assert training._result_page == RESULT_PAGE_STATS
    frame = render_training(build_dir, training, 0)
    frame.save(output / ("training-result-stats-" + language.lower() + ".png"))
    saved.append(("training-result-stats-" + language.lower(), frame))
    # Sub-state cancel.
    training.input("back", 0)  # back to select
    training2 = _make_session()
    training2.pet.language = language
    training2.input("action", 0)
    training2.input("action", 0)
    training2._reps_completed = 2
    training2._pending_ev = 12
    training2._energy_reserved = 16
    training2.state = STATE_CANCEL
    training2._focus = "follow"
    frame = render_training(build_dir, training2, 0)
    frame.save(output / ("training-cancel-" + language.lower() + ".png"))
    saved.append(("training-cancel-" + language.lower(), frame))
    # State E (error).
    training3 = _make_session()
    training3.pet.language = language
    training3.input("action", 0)
    training3.input("action", 0)
    training3.state = STATE_ERROR
    training3._focus = "retry"
    frame = render_training(build_dir, training3, 0)
    frame.save(output / ("training-error-" + language.lower() + ".png"))
    saved.append(("training-error-" + language.lower(), frame))
    return saved


def main():
    pet = Pet()
    pet.complete_hatch("rookie", entropy=12345)
    session = PracticeSession(pet, lambda _: True)
    output = ROOT / "out" / "practice-preview"
    output.mkdir(parents=True, exist_ok=True)
    frames = {}
    build_dir = ROOT / "build-tdisplay"

    def capture(name, now=0, sess=None):
        if sess is None:
            sess = session
        frame = render_practice(build_dir, sess, now)
        frame.save(output / (name + ".png"))
        frames[name] = frame

    def capture_training(name, sess, now=0):
        frame = render_training(build_dir, sess, now)
        frame.save(output / (name + ".png"))
        frames[name] = frame

    capture("battle-entry")
    # ------------------------------------------------------------------
    # Batched training previews (2026-10-07 spec) — default language is
    # ES so the legacy frame names (training-select, training-result,
    # etc.) keep the same content they had before the i18n refactor.
    # ------------------------------------------------------------------
    training = TrainingSession(pet, lambda _: True)
    pet.language = "ES"
    capture_training("training-select", training, 0)
    training.input("next", 0)
    capture_training("training-select-def", training, 0)
    training.input("action", 0)
    assert training.state == STATE_PREPARE
    capture_training("training-prepare", training, 0)
    training.input("action", 0)
    assert training.state == STATE_SESSION
    training._reps_completed = 3
    training._pending_ev = 18
    training._energy_reserved = 24
    capture_training("training-session", training, 0)
    pet_cap = Pet()
    pet_cap.complete_hatch("rookie", entropy=12345)
    pet_cap.language = "ES"
    pet_cap.ev["off"] = 250
    cap_session = TrainingSession(pet_cap, lambda _: True)
    cap_session.input("action", 0)
    cap_session.input("action", 0)
    cap_session._reps_completed = 1
    cap_session._pending_ev = 2
    cap_session._energy_reserved = 8
    capture_training("training-session-cap", cap_session, 0)
    training._focus = "confirm"
    training.state = STATE_CONFIRM
    capture_training("training-confirm", training, 0)
    training._result_snapshot = {"reps": 3, "ev_added": 18,
                                   "energy_charged": 24, "effort_added": 24,
                                   "happiness_added": 9, "weight_delta": -3,
                                   "training_sessions_added": 3}
    # Mirror the post-apply EV / energy / effort on the pet so the
    # summary and the STATS page show a realistic delta. The renderer
    # reads pet.ev (post) and the summary's ev_added to compute the
    # pre value, so without this step the bars are empty.
    pet.ev["off"] = training._result_snapshot["ev_added"]
    pet.stats["e"] = max(0, pet.stats["e"] - training._result_snapshot["energy_charged"])
    pet.effort = min(100, getattr(pet, "effort", 0) + training._result_snapshot["effort_added"])
    training.state = STATE_RESULT
    capture_training("training-result", training, 0)
    # Capture the new STATS page in ES (next page from summary).
    training._result_page = RESULT_PAGE_STATS
    capture_training("training-result-stats", training, 0)
    training._result_page = RESULT_PAGE_SUMMARY
    training.state = STATE_CANCEL
    training._focus = "follow"
    capture_training("training-cancel", training, 0)
    training.state = STATE_ERROR
    training._focus = "retry"
    capture_training("training-error", training, 0)
    # ------------------------------------------------------------------
    # Bilingual previews (ES + EN) for the whole flow. The
    # capture_training_for_language helper returns the list of saved
    # names so we can build a single overview sheet with both
    # languages side by side.
    # ------------------------------------------------------------------
    es_saved = capture_training_for_language(output, "ES", build_dir)
    en_saved = capture_training_for_language(output, "EN", build_dir)
    # ------------------------------------------------------------------
    # Legacy / techniques previews (kept for visual continuity).
    # ------------------------------------------------------------------
    legacy = TrainingSession(pet, lambda _: True)
    legacy.input("next", 0)
    capture_training("training", legacy, 0)
    for _ in range(5):
        legacy.input("next", 3000)
    legacy.input("action", 3000)
    capture_training("training-result-legacy", legacy, 1800)
    techniques = legacy.techniques
    capture("tech")
    techniques.input("next", 0)
    capture("locked")
    techniques.input("action", 0)
    capture("locked-detail")
    techniques.input("action", 0)
    techniques.input("action", 0)
    techniques.input("next", 0)
    techniques.input("action", 0)
    capture("flame")
    techniques.input("back", 0)
    capture("equipped")
    session = PracticeSession(pet, lambda _: True)
    capture("battle-ready", 1000)
    session.input("next", 1000)
    session.input("next", 1000)
    capture("battle-order", 1000)
    session.input("action", 1000)
    capture("battle", 1800)
    session.input("next", 2600)
    session.input("next", 2600)
    capture("battle-cooldown", 2600)
    session.input("action", 2600)
    capture("battle-changed-order", 3400)
    pet.techniques.equip(1)
    pet.techniques.equip(2)
    session = PracticeSession(pet, lambda _: True)
    session.input("next", 0)
    session.input("next", 0)
    session.input("action", 1000)
    capture("battle-block", 1800)
    sheet = Image.new("RGB", (480, 270))
    for i, name in enumerate(("battle-entry", "equipped", "battle-order",
                                "battle-changed-order")):
        frame = frames[name]
        sheet.paste(frame, ((i % 2) * 240, (i // 2) * 135))
    sheet.resize((960, 540), Image.Resampling.NEAREST).save(output / "overview.png")
    # Batched training overview: 8 frames in a 4x2 grid.
    batched_names = ("training-select", "training-select-def",
                      "training-prepare", "training-session",
                      "training-session-cap", "training-confirm",
                      "training-result", "training-cancel")
    batched_sheet = Image.new("RGB", (960, 270))
    for i, name in enumerate(batched_names):
        with Image.open(output / (name + ".png")) as frame:
            batched_sheet.paste(frame, ((i % 4) * 240, (i // 4) * 135))
    batched_sheet.resize((1920, 540), Image.Resampling.NEAREST).save(
        output / "training-batched-overview.png")
    # Bilingual overview: ES top row, EN bottom row, 8 states each.
    state_names = ("select", "select-def", "prepare", "session",
                    "session-cap", "confirm", "result", "result-stats")
    bilingual = Image.new("RGB", (1920, 540))
    for row, lang in enumerate(("es", "en")):
        for col, name in enumerate(state_names):
            with Image.open(output / ("training-" + name + "-" + lang + ".png")) as frame:
                bilingual.paste(frame, (col * 240, row * 135))
    bilingual.resize((1920, 540), Image.Resampling.NEAREST).save(
        output / "training-bilingual-overview.png")
    # Training legacy overview (kept for the techniques screenshots).
    training_sheet = Image.new("RGB", (480, 270))
    for i, name in enumerate(("training", "training-result-legacy",
                                "battle-entry", "battle-block")):
        with Image.open(output / (name + ".png")) as frame:
            training_sheet.paste(frame, ((i % 2) * 240, (i // 2) * 135))
    training_sheet.resize((960, 540), Image.Resampling.NEAREST).save(
        output / "training-overview.png")
    # Export the generated glyphs for inspection and later firmware asset work.
    for name in INFO_ICONS:
        info_icon(name).save(output / ("icon-" + name + ".png"))
    print(output / "training-bilingual-overview.png")


if __name__ == "__main__":
    main()
