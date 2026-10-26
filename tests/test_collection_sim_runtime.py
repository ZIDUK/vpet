"""Drive the actual pygame loop against temporary saves and a fake clock."""
from pathlib import Path
from types import SimpleNamespace

from core.pet import Pet
from scripts.sim_services import SimulatorServices

ROOT = Path(__file__).resolve().parents[1]


def test_actual_simulator_creates_switches_and_hatches_a_confirmed_founder(tmp_path, monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    from scripts import sim
    pet = Pet(species="rookie", state="live")
    pet.roll_dna(42)
    services = SimulatorServices(tmp_path)
    assert services.start(pet)
    original_id = pet.profile.pet_id
    legacy = services.save_path.read_bytes()
    monkeypatch.setattr(sim, "Pet", lambda: pet)
    monkeypatch.setattr(sim, "SimulatorServices", lambda _: services)
    monkeypatch.setattr(sim, "parse_args", lambda: SimpleNamespace(
        profile="tdisplay", scale=1, build_dir=str(ROOT / "build-tdisplay"), record=None,
        practice=False, training=False, max_frames=250))
    frame = [0]
    monkeypatch.setattr(sim.pygame.time, "get_ticks", lambda: frame[0] * 100)
    monkeypatch.setattr(sim.time, "monotonic", lambda: 100 + frame[0] / 10)
    monkeypatch.setattr(sim.pygame.time, "Clock", lambda: SimpleNamespace(tick=lambda _: None))
    commands = list("n" * 8 + "a" + "n" * 9 + "a" + "na" + "na" + "na" + "naa" + "na")
    pending_release = [None]

    def events():
        frame[0] += 1
        if frame[0] < 30:
            return []
        if pending_release[0] is not None:
            key, pending_release[0] = pending_release[0], None
            return [sim.pygame.event.Event(sim.pygame.KEYUP, key=key)]
        if commands:
            key = {"n": sim.pygame.K_n, "a": sim.pygame.K_a}[commands.pop(0)]
            pending_release[0] = key
            return [sim.pygame.event.Event(sim.pygame.KEYDOWN, key=key)]
        if pet.profile.pet_id != original_id and pet.species == "baby":
            return [sim.pygame.event.Event(sim.pygame.QUIT)]
        return []

    monkeypatch.setattr(sim.pygame.event, "get", events)
    sim.main()
    assert services.collection is not None and len(services.collection.slots) == 2
    assert pet.profile.pet_id != original_id and pet.species == "baby"
    assert services.save_path.read_bytes() == legacy
    restored = Pet()
    fresh = SimulatorServices(tmp_path)
    assert fresh.start(restored)
    assert restored.profile == pet.profile and restored.species == "baby"
    assert restored.inventory == pet.inventory
