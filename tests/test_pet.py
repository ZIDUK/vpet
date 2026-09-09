"""Smoke tests for the Pet model.

These run on the dev machine (Mac) using pytest, NOT on the Pico.
We mock time.monotonic so tests are deterministic.
"""
import pytest


class FakeTime:
    def __init__(self, start=0.0):
        self.now = start

    def __call__(self):
        return self.now

    def advance(self, dt):
        self.now += dt


@pytest.fixture
def fake_time(monkeypatch):
    fake = FakeTime()
    import core.pet as pet_mod
    monkeypatch.setattr(pet_mod.time, "monotonic", fake)
    return fake


def test_pet_starts_as_egg(fake_time):
    from core.pet import Pet, STATE_EGG
    p = Pet()
    assert p.is_egg
    assert not p.is_live
    assert p.species == "egg"
    # Stats still initialized
    assert p.get("h") == 70


def test_pet_starts_with_default_stats(fake_time):
    from core.pet import Pet
    p = Pet()
    assert p.get("h") == 70
    assert p.get("e") == 70
    assert p.get("p") == 70
    assert p.get("hp") == 70


def test_apply_action_feed(fake_time):
    from core.pet import Pet
    p = Pet()
    p.apply_action(0)  # FEED
    assert p.get("h") == 95  # 70 + 25


def test_apply_action_caps_at_100(fake_time):
    from core.pet import Pet
    p = Pet()
    p.stats["h"] = 90
    p.apply_action(0)
    assert p.get("h") == 100


def test_decay_after_3_seconds(fake_time):
    from core.pet import Pet, DECAY_AMOUNT
    p = Pet(state="live")  # decay only works in live state
    fake_time.advance(4)
    assert p.decay_if_due() is True
    for s in ["h", "e", "p", "hp"]:
        assert p.get(s) == 70 - DECAY_AMOUNT


def test_decay_skipped_in_egg_state(fake_time):
    """Eggs don't decay — they're inside an egg, not eating yet."""
    from core.pet import Pet
    p = Pet()  # default is egg
    fake_time.advance(10)
    assert p.decay_if_due() is False
    assert p.get("h") == 70


def test_no_decay_before_period(fake_time):
    from core.pet import Pet
    p = Pet(state="live")
    fake_time.advance(2)
    assert p.decay_if_due() is False
    assert p.get("h") == 70


def test_to_dict_roundtrip(fake_time):
    from core.pet import Pet
    p1 = Pet(state="live")
    p1.stats["h"] = 42
    p1.battles_won = 7
    p1.inventory["meat"] = 1
    p1.language = "ES"
    p1.sound_enabled = False
    fake_time.advance(12)
    data = p1.to_dict()
    p2 = Pet()
    p2.load_from_dict(data)
    assert p2.get("h") == 42
    assert p2.battles_won == 7
    assert p2.inventory["meat"] == 1
    assert p2.language == "ES"
    assert p2.sound_enabled is False
    assert 12 <= p2.age_seconds < 13
    assert p2.state == "live"


def test_save_egg_state_loads_as_egg(fake_time):
    """If we save as an egg, we should load as an egg (and restart the timer)."""
    from core.pet import Pet
    p1 = Pet()
    assert p1.is_egg
    data = p1.to_dict()
    p2 = Pet()
    p2.load_from_dict(data)
    assert p2.is_egg


def test_hatch_state_transition(fake_time):
    """Egg -> Hatching (via start_hatch) -> Live (via complete_hatch)."""
    from core.pet import Pet
    p = Pet()
    assert p.is_egg
    p.start_hatch()
    assert p.is_hatching
    p.complete_hatch("baby")
    assert p.is_live
    assert p.species == "baby"


def test_hatch_boosts_stats(fake_time):
    from core.pet import Pet
    p = Pet(state="hatching")
    p.complete_hatch("baby")
    # Each stat should have a +15 boost from the signature move
    for s in ["h", "e", "p", "hp"]:
        assert p.get(s) == 85  # 70 + 15


def test_hatch_progress(fake_time):
    from core.pet import Pet
    p = Pet()
    p.start_hatch()
    fake_time.advance(4)  # 4s of an 8s hatch
    progress = p.hatch_progress(8)
    assert 0.4 < progress < 0.6


def test_hatch_progress_complete(fake_time):
    from core.pet import Pet
    p = Pet(state="live")  # not hatching
    assert p.hatch_progress(8) == 1.0


def test_evolution_json_files_exist():
    """All 6 stage JSONs (egg, baby, rookie, champion, ultimate, mega) are present."""
    import json
    from pathlib import Path
    data_dir = Path(__file__).parent.parent / "src" / "data" / "digimon"
    expected = ["egg", "baby", "rookie", "champion", "ultimate", "mega"]
    for name in expected:
        path = data_dir / f"{name}.json"
        assert path.exists(), f"missing {path}"
        data = json.loads(path.read_text())
        assert "name" in data
        assert "evolves_to" in data
        assert "line" in data
