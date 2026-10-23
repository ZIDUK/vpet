"""Actual pygame inputs plus ES/EN screens and continuously animated species."""
from pathlib import Path
from types import SimpleNamespace
import json
import pytest
from PIL import Image
from core.pet import Pet
from display_profiles import get_display_profile
from scripts import build as build_script
from scripts.exploration_session import ExplorationSession
from scripts.sim_renderer import render_frame


@pytest.fixture(scope="module")
def assets(tmp_path_factory):
    path = tmp_path_factory.mktemp("explore-assets")
    build_script.main(profile_name="tdisplay", output_dir=path)
    return path


@pytest.mark.parametrize("language", ["ES", "EN"])
@pytest.mark.parametrize("page", ["routes", "stats", "confirm", "trip", "recall", "receipt"])
def test_all_screens_fit_es_en(assets, language, page):
    p = Pet(species="champion", state="live")
    p.language = language
    s = ExplorationSession(p, lambda _: True, lambda: 100000)
    s.route, s.stat, s.page = "jornada", "off", page
    if page in ("trip", "recall", "receipt"):
        p.exploration.start(p, "jornada", "off", 71200)
    if page == "receipt":
        p.exploration.claim(p, 100000)
    image = render_frame(assets, p, panel_mode="explore", exploration_menu=s,
                         profile=get_display_profile("tdisplay"))
    assert image.size == (240, 135)
    assert len(set(image.crop((0, 24, 240, 135)).getdata())) > 5


@pytest.mark.parametrize("species", ["rookie", "champion", "ultimate"])
def test_travel_animation_advances_under_a_second(assets, species):
    p = Pet(species=species, state="live")
    p.exploration.start(p, "patio", None, 100000)
    kwargs = dict(exploration_now=100900, profile=get_display_profile("tdisplay"))
    a = render_frame(assets, p, now_ms=0, **kwargs)
    b = render_frame(assets, p, now_ms=350, **kwargs)
    assert a.crop((0, 56, 240, 85)).tobytes() != b.crop((0, 56, 240, 85)).tobytes()


@pytest.mark.parametrize("species", ["rookie", "champion", "ultimate"])
@pytest.mark.parametrize("language", ["ES", "EN"])
@pytest.mark.parametrize("elapsed", [0, 14400, 28799])
@pytest.mark.parametrize("view", ["home", "panel"])
def test_large_travel_sprite_does_not_cover_trip_information(assets, species, language, elapsed, view):
    p = Pet(species=species, state="live")
    p.language = language
    assert p.exploration.start(p, "jornada", "off", 100000)
    session = ExplorationSession(p, lambda _: True, lambda: 100000 + elapsed) if view == "panel" else None
    frame = render_frame(assets, p, now_ms=1700, panel_mode="explore" if session else None,
                         exploration_menu=session, exploration_now=100000 + elapsed,
                         profile=get_display_profile("tdisplay"))
    lane = frame.crop((0, 60, 240, 104))
    mask = Image.new("1", lane.size)
    mask.putdata([r > 100 and r > g * 1.2 and r > b * 1.5 for r, g, b in lane.getdata()])
    bounds = mask.getbbox()
    assert bounds is not None and bounds[3] - bounds[1] >= 30
    assert bounds[0] >= 4 and bounds[2] <= 236


def test_real_simulator_jornada_claim_guide_and_training(assets, tmp_path, monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    from scripts import sim
    from scripts.sim_services import SimulatorServices

    p = Pet(species="rookie", state="live")
    # This input trace exercises the legacy Guide path, not the new starter bag.
    p.adopted_inventory = {item_id: 0 for item_id in p.adopted_inventory}
    p.stats.update(h=100, e=100, p=100)
    services = SimulatorServices(tmp_path)
    travel = [0]
    services.exploration_time = lambda: 1791979200 + travel[0]
    monkeypatch.setattr(sim, "Pet", lambda: p)
    monkeypatch.setattr(sim, "SimulatorServices", lambda _: services)
    monkeypatch.setattr(sim, "parse_args", lambda: SimpleNamespace(
        profile="tdisplay", scale=1, build_dir=str(assets), record=None,
        practice=False, training=False, max_frames=500))
    frame = [0]
    monkeypatch.setattr(sim.pygame.time, "get_ticks", lambda: frame[0] * 100)
    monkeypatch.setattr(sim.time, "monotonic", lambda: 100 + frame[0] / 10)
    monkeypatch.setattr(sim.pygame.time, "Clock", lambda: SimpleNamespace(tick=lambda _: None))
    queue = [[] for _ in range(30)]

    def press(key):
        queue.append([sim.pygame.event.Event(sim.pygame.KEYDOWN, key=key)])
        queue.append([sim.pygame.event.Event(sim.pygame.KEYUP, key=key)])

    n, a, b = sim.pygame.K_n, sim.pygame.K_a, sim.pygame.K_b
    for key in (n, n, n, a, n, a, n, n, a, a, b, n, a, b):
        press(key)
    queue.append("finish-trip")
    for key in (a, a, a, b, n, n, n, a, n, n, n, n, a, a, a):
        press(key)
    queue.extend([[] for _ in range(110)])
    press(sim.pygame.K_ESCAPE)
    inputs = iter(queue)

    def events():
        frame[0] += 1
        value = next(inputs, [])
        if value == "finish-trip":
            travel[0] = 28800
            return []
        return value

    monkeypatch.setattr(sim.pygame.event, "get", events)
    results = []
    render_training = sim.render_training

    def observe_training(*args):
        if args[1]._result_snapshot:
            results.append(dict(args[1]._result_snapshot))
        return render_training(*args)

    monkeypatch.setattr(sim, "render_training", observe_training)
    sim.main()
    assert p.ev_at("off") == 9
    assert results and results[-1]["guide_ev"] == 1
    assert not p.exploration.away and not p.exploration.guide
    saved = json.loads(services.save_path.read_text())
    assert saved["ev"]["off"] == 9
    assert not saved["exploration"]["guide"]
