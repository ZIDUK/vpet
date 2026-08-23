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
def monkeypatch_time(monkeypatch):
    fake = FakeTime()
    import core.pet as pet_mod
    monkeypatch.setattr(pet_mod.time, "monotonic", fake)
    return fake


def test_pet_starts_at_70(monkeypatch_time):
    from core.pet import Pet
    p = Pet()
    assert p.get("h") == 70
    assert p.get("e") == 70
    assert p.get("p") == 70
    assert p.get("hp") == 70
    assert p.species == "agumon"


def test_apply_action_feed(monkeypatch_time):
    from core.pet import Pet, ACTION_EFFECTS
    p = Pet()
    p.apply_action(0)  # FEED
    assert p.get("h") == 95  # 70 + 25


def test_apply_action_caps_at_100(monkeypatch_time):
    from core.pet import Pet
    p = Pet()
    p.stats["h"] = 90
    p.apply_action(0)  # FEED
    assert p.get("h") == 100  # capped


def test_decay_after_3_seconds(monkeypatch_time):
    from core.pet import Pet, DECAY_AMOUNT
    p = Pet()
    monkeypatch_time.advance(4)
    assert p.decay_if_due() is True
    for s in ["h", "e", "p", "hp"]:
        assert p.get(s) == 70 - DECAY_AMOUNT


def test_no_decay_before_period(monkeypatch_time):
    from core.pet import Pet
    p = Pet()
    monkeypatch_time.advance(2)  # less than 3s
    assert p.decay_if_due() is False
    assert p.get("h") == 70


def test_to_dict_roundtrip(monkeypatch_time):
    from core.pet import Pet
    p1 = Pet()
    p1.stats["h"] = 42
    p1.battles_won = 7
    data = p1.to_dict()
    p2 = Pet()
    p2.load_from_dict(data)
    assert p2.get("h") == 42
    assert p2.battles_won == 7
    assert p2.species == "agumon"


def test_evolution_json_files_exist():
    """Sanity: all 8 evolution JSONs are present and parseable."""
    import json
    from pathlib import Path
    data_dir = Path(__file__).parent.parent / "src" / "data" / "digimon"
    expected = ["agumon", "greymon", "metalgreymon", "wargreymon",
                "gabumon", "garurumon", "weregarurumon", "metalgarurumon"]
    for name in expected:
        path = data_dir / f"{name}.json"
        assert path.exists(), f"missing {path}"
        data = json.loads(path.read_text())
        assert "name" in data
        assert "evolves_to" in data
