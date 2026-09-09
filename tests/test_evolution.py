"""Tests for evolution rules.

These tests use synthetic registries (in-memory) rather than reading the actual
JSON files, because the sprout_line has a lifecycle (egg → live) that needs
careful test setup. Once the evolution code is stable, we add tests that
read the actual JSON files.
"""
import pytest


def test_evolution_check_blocks_when_stats_low():
    from core.evolution import Evolution
    from core.pet import Pet

    registry = {
        "rookie": {
            "evolves_to": "champion",
            "min_age_seconds": 0,
            "battles_required": 0,
            "requirements": {"h": 80, "hp": 80},
        }
    }
    p = Pet(species="rookie", state="live")
    p.stats["h"] = 50
    p.stats["hp"] = 50
    ev = Evolution(registry)
    assert ev.check(p) == (None, None)


def test_evolution_check_passes_when_all_requirements_met():
    from core.evolution import Evolution
    from core.pet import Pet

    registry = {
        "rookie": {
            "evolves_to": "champion",
            "min_age_seconds": 0,
            "battles_required": 0,
            "requirements": {"h": 80, "hp": 80},
        }
    }
    p = Pet(species="rookie", state="live")
    p.stats["h"] = 90
    p.stats["hp"] = 90
    ev = Evolution(registry)
    new_form, reason = ev.check(p)
    assert new_form == "champion"
    assert reason is not None


def test_evolution_check_blocks_when_too_young(monkeypatch):
    from core.evolution import Evolution
    from core.pet import Pet
    import core.pet as pet_mod

    fake_t = [100.0]
    monkeypatch.setattr(pet_mod.time, "monotonic", lambda: fake_t[0])

    registry = {
        "rookie": {
            "evolves_to": "champion",
            "min_age_seconds": 200,
            "battles_required": 0,
            "requirements": {},
        }
    }
    p = Pet(species="rookie", state="live")
    fake_t[0] = 150.0
    ev = Evolution(registry)
    assert ev.check(p) == (None, None)


def test_evolution_check_blocks_when_battles_required_not_met():
    from core.evolution import Evolution
    from core.pet import Pet

    registry = {
        "rookie": {
            "evolves_to": "champion",
            "min_age_seconds": 0,
            "battles_required": 5,
            "requirements": {},
        }
    }
    p = Pet(species="rookie", state="live")
    p.battles_won = 2
    ev = Evolution(registry)
    assert ev.check(p) == (None, None)


def test_evolution_no_next_form_returns_none():
    from core.evolution import Evolution
    from core.pet import Pet

    registry = {
        "mega": {"evolves_to": None, "requirements": {}},
    }
    p = Pet(species="mega", state="live")
    ev = Evolution(registry)
    assert ev.check(p) == (None, None)


def test_evolve_increases_stats_as_signature_move():
    """Evolution should boost stats a bit (the signature move)."""
    from core.evolution import Evolution
    from core.pet import Pet

    registry = {
        "rookie": {
            "evolves_to": "champion",
            "min_age_seconds": 0,
            "battles_required": 0,
            "requirements": {"h": 0, "hp": 0, "p": 0, "e": 0},
        }
    }
    p = Pet(species="rookie", state="live")
    p.stats["h"] = 50
    p.stats["e"] = 50
    ev = Evolution(registry)
    assert ev.evolve(p) is True
    assert p.species == "champion"
    # All stats should have gotten a boost
    assert p.stats["h"] == 60  # 50 + 10 boost
    assert p.stats["e"] == 60


def test_force_evolution_uses_registered_next_form():
    from core.evolution import Evolution
    from core.pet import Pet

    p = Pet(species="rookie", state="live")
    ev = Evolution({"rookie": {"evolves_to": "champion"}})

    assert ev.force(p) is True
    assert p.species == "champion"
    assert ev.force(p) is False


def test_runtime_registry_evolves_ready_rookie_to_flamemon():
    from config import EVOLUTION_REGISTRY
    from core.evolution import Evolution
    from core.pet import Pet

    p = Pet(species="rookie", state="live")
    p.born_at -= 61
    for stat in p.stats:
        p.stats[stat] = 100

    assert Evolution(EVOLUTION_REGISTRY).evolve(p) is True
    assert p.species == "champion"


def test_flamemon_automatic_evolution_is_pending():
    from config import EVOLUTION_REGISTRY
    from core.evolution import Evolution
    from core.pet import Pet

    p = Pet(species="champion", state="live")
    p.born_at -= 10000
    p.battles_won = 99
    for stat in p.stats:
        p.stats[stat] = 100

    assert Evolution(EVOLUTION_REGISTRY).check(p) == (None, None)


def test_force_evolution_reaches_dragfiremon_one_stage_at_a_time():
    from config import EVOLUTION_REGISTRY
    from core.evolution import Evolution
    from core.pet import Pet

    p = Pet(species="rookie", state="live")
    evolution = Evolution(EVOLUTION_REGISTRY)

    assert evolution.force(p) is True
    assert p.species == "champion"
    assert evolution.force(p) is True
    assert p.species == "ultimate"
    assert evolution.force(p) is False
