import copy
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from config import EVOLUTION_REGISTRY
from core.evolution import Evolution
from core.pet import Pet
from scripts.practice_session import PracticeSession
from scripts.sim_services import SimulatorServices

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def arena_app(tmp_path_factory):
    binary = tmp_path_factory.mktemp("arena-evolution-app") / "app"
    core = ROOT / "firmware/t-display/lib/vpet_core/src"
    subprocess.run(["c++", "-std=c++17", "-I" + str(ROOT / "tests/app_stubs"),
                    "-I" + str(ROOT / "firmware/t-display/include"), "-I" + str(core),
                    str(ROOT / "tests/arena_evolution_app.cpp"), str(ROOT / "firmware/t-display/src/App.cpp"),
                    *[str(core / "vpet" / (name + ".cpp")) for name in
                      ("PetState", "Nutrition", "SettingsStore", "PracticeBattle", "Motion", "Navigation", "Evolution", "DateTimeMenu")],
                    "-o", str(binary)], check=True)
    return binary


@pytest.mark.parametrize("mode", range(5))
def test_real_app_arena_save_retry_reboot_and_automatic_evolution(arena_app, mode):
    subprocess.run([str(arena_app), str(mode)], check=True)


def champion():
    pet = Pet(species="champion", state="live")
    pet.stage_age_seconds = 129600
    pet.battles_this_form, pet.battles_won, pet.battles_lost = 14, 8, 6
    return pet


@pytest.mark.parametrize("species", ["rookie", "champion", "ultimate"])
@pytest.mark.parametrize("result", ["VICTORIA", "DERROTA", "EMPATE"])
def test_arena_counts_decisive_results_once_without_changing_care(species, result):
    pet = champion()
    pet.species = species
    before = copy.deepcopy(pet.__dict__)
    session = PracticeSession(pet, lambda _: True)
    session.battle.result = result
    assert session._award_result()
    expected = (15, 9, 6) if result == "VICTORIA" else (15, 8, 7) if result == "DERROTA" else (14, 8, 6)
    assert (pet.battles_this_form, pet.battles_won, pet.battles_lost) == expected
    assert (pet.stats, pet.dp, pet.injured, pet.ev) == (before["stats"], before["dp"], before["injured"], before["ev"])
    for ms in (1500, 3000, 15000):
        session.tick(ms)
        assert session._award_result()
    assert (pet.battles_this_form, pet.battles_won, pet.battles_lost) == expected


def test_fifteenth_arena_win_unlocks_existing_automatic_evolution():
    pet = champion()
    evolution = Evolution(EVOLUTION_REGISTRY)
    assert evolution.check(pet)[0] is None
    session = PracticeSession(pet, lambda _: True)
    session.battle.result = "VICTORIA"
    assert session._award_result()
    assert evolution.check(pet)[0] == "ultimate"  # 15 battles, exactly 9/15 wins.
    pet.stage_age_seconds -= 1
    assert evolution.check(pet)[0] is None


def test_fifteenth_arena_loss_still_requires_sixty_percent_wins():
    pet = champion()
    session = PracticeSession(pet, lambda _: True)
    session.battle.result = "DERROTA"
    assert session._award_result()
    assert pet.battles_this_form == 15
    assert Evolution(EVOLUTION_REGISTRY).check(pet)[0] is None


def test_arena_save_rejection_rolls_back_counters_and_reward_before_retry(tmp_path):
    pet = champion()
    services = SimulatorServices(tmp_path)
    assert services.save(pet)
    before = pet.to_dict()
    session = PracticeSession(pet, lambda _: False)
    session.battle.result = "VICTORIA"
    assert not session._award_result()
    assert pet.to_dict() == before and not session.awarded
    session.save = services.save
    assert session._award_result()
    assert session._award_result()
    restored = Pet()
    assert services.load(restored)
    assert (restored.battles_this_form, restored.battles_won, restored.battles_lost) == (15, 9, 6)
    assert restored.item_reward_cursor == pet.item_reward_cursor


def test_simulator_automatic_evolution_is_saved_and_rejection_is_reversible(tmp_path, monkeypatch):
    services = SimulatorServices(tmp_path)
    pet = champion()
    session = PracticeSession(pet, services.save)
    session.battle.result = "VICTORIA"
    assert session._award_result()
    before = pet.to_dict()
    evolution = Evolution(EVOLUTION_REGISTRY)
    with monkeypatch.context() as patch:
        patch.setattr(services, "save", lambda _: False)
        assert not services.evolve_and_save(pet, evolution)
    assert pet.to_dict() == before
    assert services.evolve_and_save(pet, evolution)
    assert pet.species == "ultimate" and pet.battles_this_form == 0
    assert pet.battles_won == 9 and pet.battles_lost == 6
    restored = Pet()
    assert services.load(restored) and restored.species == "ultimate"
    assert not services.evolve_and_save(pet, evolution)


@pytest.mark.parametrize("result,counter", [("VICTORIA", "battles_won"), ("DERROTA", "battles_lost")])
def test_arena_counter_storage_limits_do_not_wrap(result, counter):
    pet = champion()
    pet.battles_this_form = 2147483647
    setattr(pet, counter, 255)
    session = PracticeSession(pet, lambda _: True)
    session.battle.result = result
    assert session._award_result()
    assert pet.battles_this_form == 2147483647 and getattr(pet, counter) == 255


def test_real_simulator_arena_to_saved_evolution_with_user_inputs(tmp_path, monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    from scripts import build, sim
    assets = tmp_path / "assets"
    build.main(profile_name="tdisplay", output_dir=assets)
    pet = champion()
    pet.ev.update({stat: 252 for stat in pet.ev})
    pet.techniques.equipped = [0]
    pet.techniques.mastery[0], pet.techniques.bond = 100, 100
    services = SimulatorServices(tmp_path)
    assert services.save(pet)
    monkeypatch.setattr(sim, "Pet", lambda: pet)
    monkeypatch.setattr(sim, "SimulatorServices", lambda _: services)
    monkeypatch.setattr(sim, "parse_args", lambda: SimpleNamespace(
        profile="tdisplay", scale=1, build_dir=str(assets), record=None,
        practice=False, training=False, max_frames=500))
    sessions = []

    def start(*args, **kwargs):
        session = PracticeSession(*args, **kwargs)
        sessions.append(session)
        return session

    monkeypatch.setattr(sim, "PracticeSession", start)
    frame = [0]
    monkeypatch.setattr(sim.pygame.time, "get_ticks", lambda: frame[0] * 100)
    monkeypatch.setattr(sim.time, "monotonic", lambda: 100 + frame[0] / 10)
    monkeypatch.setattr(sim.pygame.time, "Clock", lambda: SimpleNamespace(tick=lambda _: None))
    exited = [False]

    def events():
        frame[0] += 1
        n = frame[0]
        if 31 <= n <= 40:
            key = sim.pygame.K_n if n <= 38 else sim.pygame.K_a
            kind = sim.pygame.KEYDOWN if n % 2 else sim.pygame.KEYUP
            return [sim.pygame.event.Event(kind, key=key)]
        if sessions and sessions[0].awarded and not exited[0]:
            exited[0] = True
            return [sim.pygame.event.Event(sim.pygame.KEYDOWN, key=sim.pygame.K_a)]
        if pet.species == "ultimate":
            return [sim.pygame.event.Event(sim.pygame.QUIT)]
        return []

    monkeypatch.setattr(sim.pygame.event, "get", events)
    sim.main()
    assert sessions and sessions[0].battle.result == "VICTORIA" and exited[0]
    assert pet.species == "ultimate" and pet.battles_this_form == 0
    restored = Pet()
    assert services.load(restored) and restored.species == "ultimate"
    assert restored.battles_won == 9 and restored.battles_lost == 6
