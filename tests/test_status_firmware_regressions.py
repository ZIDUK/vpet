"""Pin hardware adapter contracts that Pillow-only previews cannot exercise."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def section(name, next_name):
    source = (ROOT / "firmware/t-display/src/Panels.cpp").read_text()
    return source.split("void Panels::" + name, 1)[1].split("void Panels::" + next_name, 1)[0]


def test_vital_rows_use_small_font_above_meter():
    source = section("drawVital", "drawBar")
    assert "drawFrameScaled" in source
    assert "drawLabel(label, x + 22, y + 2, 44, 1)" in source
    assert "drawLabel(num, x + width - 3, y + 2, 28, 1)" in source


def test_list_icons_fit_inside_rows():
    source = section("drawStatus(", "drawInventory")
    assert "drawFrameScaled(display_, icon, 0, x + 2, y + 2, 12, 12" in source


def test_dna_refresh_includes_pet_and_clears_transparent_background():
    source = (ROOT / "firmware/t-display/src/Panels.cpp").read_text()
    branch = source.split("if (!statusPageChanged", 1)[1].split("char title[20]", 1)[0]
    assert "drawStatusPet(pet, nowMs)" in branch
    assert "fillRect(0, 48, kStatusSplitX, 87, kPanel)" in branch


def test_buttons_are_sampled_outside_render_loop():
    source = (ROOT / "firmware/t-display/src/BoardInput.cpp").read_text()
    assert "xTaskCreate" in source
    assert "vTaskDelayUntil" in source
    assert "xQueueReceive" in source


def test_long_press_discards_pending_navigation_events():
    source = (ROOT / "firmware/t-display/src/BoardInput.cpp").read_text()
    assert "if (event == InputEvent::Back) {" in source
    assert "self.nextQueued_.store(false);" in source
    assert source.index("xQueueReset") < source.index("xQueueSend")


def test_pending_next_events_are_coalesced():
    source = (ROOT / "firmware/t-display/src/BoardInput.cpp").read_text()
    assert "!self.nextQueued_.exchange(true)" in source
    assert "if (event == InputEvent::Next) nextQueued_.store(false);" in source


def test_inactivity_timeout_preserves_live_activities():
    source = (ROOT / "firmware/t-display/src/App.cpp").read_text()
    assert "training_.state == TrainingSession::State::Session" in source
    assert "!practice_.battle.result" in source
    assert "if (event != InputEvent::None || busy) lastInteractionMs_ = nowMs;" in source
    assert "!busy && nowMs - lastInteractionMs_ >= 10000" in source
    assert "navigation_.setPanel(PanelId::Home);" in source


def test_battle_menu_opens_practice_for_all_combat_evolutions():
    source = (ROOT / "firmware/t-display/src/App.cpp").read_text()
    activation = source.split("void App::activate", 1)[1]
    branch = activation.split("case 3:", 1)[1].split("case 4:", 1)[0]
    assert "pet_.species() != SpeciesId::Egg" in branch
    assert "pet_.species() != SpeciesId::Baby" in branch
    assert "practice_ = PracticeSession();" in branch
    assert "practicing_ = true;" in branch
    assert "SpeciesId::Rookie" not in branch
