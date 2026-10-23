import pytest

from core import menu


@pytest.mark.parametrize("species,sequence", [
    ("egg", (0, 6, 7, 8)),
    ("baby", (0, 1, 5, 6, 7, 8)),
    ("rookie", tuple(range(9))),
    ("champion", tuple(range(9))),
    ("ultimate", tuple(range(9))),
])
def test_tdisplay_next_visits_only_available_stage_menus(species, sequence):
    current = 0
    for expected in sequence * 2:
        assert current == expected
        current = menu.next_tdisplay_menu(species, current)
    assert current == 0
    assert tuple(i for i in range(9) if menu.tdisplay_menu_available(species, i)) == sequence


def test_tdisplay_next_handles_a_previously_selected_locked_menu():
    assert menu.next_tdisplay_menu("baby", 2) == 5
    assert menu.next_tdisplay_menu("egg", 5) == 6


@pytest.mark.parametrize("profile,species,expected", [
    ("tdisplay", "egg", (6, 7, 8, 0)),
    ("tdisplay", "baby", (1, 5, 6, 7, 8, 0)),
    ("tdisplay", "rookie", tuple(range(1, 9)) + (0,)),
    ("pico", "baby", (1, 2, 3, 4)),
])
def test_real_simulator_next_uses_stage_access_only_on_tdisplay(
        profile, species, expected, tmp_path, monkeypatch):
    from types import SimpleNamespace
    from PIL import Image
    from core.pet import Pet
    from scripts import sim
    from scripts.sim_services import SimulatorServices

    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    pet = Pet(species=species, state="egg" if species == "egg" else "live")
    monkeypatch.setattr(sim, "Pet", lambda: pet)
    monkeypatch.setattr(sim, "HATCH_DURATION_SECONDS", 1000)
    monkeypatch.setattr(sim, "SimulatorServices", lambda _: SimulatorServices(tmp_path))
    monkeypatch.setattr(sim, "parse_args", lambda: SimpleNamespace(
        profile=profile, scale=1, build_dir=str(tmp_path), record=None,
        practice=False, training=False, max_frames=31 + len(expected)))
    frame = [0]
    monkeypatch.setattr(sim.pygame.time, "get_ticks", lambda: frame[0] * 100)
    monkeypatch.setattr(sim.time, "monotonic", lambda: 100 + frame[0] / 10)
    monkeypatch.setattr(sim.pygame.time, "Clock", lambda: SimpleNamespace(tick=lambda _: None))

    def events():
        frame[0] += 1
        return ([sim.pygame.event.Event(sim.pygame.KEYDOWN, key=sim.pygame.K_n)]
                if frame[0] >= 32 else [])

    monkeypatch.setattr(sim.pygame.event, "get", events)
    observed = []

    def render(*args, **kwargs):
        if frame[0] >= 32:
            observed.append(args[2])
        display = kwargs["profile"]
        return Image.new("RGB", (display.width, display.height))

    monkeypatch.setattr(sim, "render_frame", render)
    sim.main()
    assert tuple(observed) == expected
