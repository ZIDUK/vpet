"""Tests for evolution rules.

These tests use synthetic registries (in-memory) rather than reading the actual
JSON files, because the placeholder digimon doesn't evolve yet. Once you add
more forms, the registry will have more entries.
"""
import pytest


def test_evolution_check_blocks_when_stats_low():
    from core.evolution import Evolution
    from core.pet import Pet

    registry = {
        "placeholder": {
            "evolves_to": "champion_form",
            "min_age_seconds": 0,
            "battles_required": 0,
            "requirements": {"h": 80, "hp": 80},
        }
    }
    p = Pet()
    p.stats["h"] = 50
    p.stats["hp"] = 50
    ev = Evolution(registry)
    assert ev.check(p) == (None, None)


def test_evolution_check_passes_when_all_requirements_met():
    from core.evolution import Evolution
    from core.pet import Pet

    registry = {
        "placeholder": {
            "evolves_to": "champion_form",
            "min_age_seconds": 0,
            "battles_required": 0,
            "requirements": {"h": 80, "hp": 80},
        }
    }
    p = Pet()
    p.stats["h"] = 90
    p.stats["hp"] = 90
    ev = Evolution(registry)
    new_form, reason = ev.check(p)
    assert new_form == "champion_form"
    assert reason is not None


def test_evolution_check_blocks_when_too_young(monkeypatch):
    from core.evolution import Evolution
    from core.pet import Pet
    import core.pet as pet_mod

    fake_t = [100.0]
    monkeypatch.setattr(pet_mod.time, "monotonic", lambda: fake_t[0])

    registry = {
        "placeholder": {
            "evolves_to": "champion_form",
            "min_age_seconds": 200,
            "battles_required": 0,
            "requirements": {},
        }
    }
    p = Pet()
    fake_t[0] = 150.0
    ev = Evolution(registry)
    assert ev.check(p) == (None, None)


def test_evolution_check_blocks_when_battles_required_not_met():
    from core.evolution import Evolution
    from core.pet import Pet

    registry = {
        "placeholder": {
            "evolves_to": "champion_form",
            "min_age_seconds": 0,
            "battles_required": 5,
            "requirements": {},
        }
    }
    p = Pet()
    p.battles_won = 2
    ev = Evolution(registry)
    assert ev.check(p) == (None, None)


def test_evolution_no_next_form_returns_none():
    from core.evolution import Evolution
    from core.pet import Pet

    registry = {
        "placeholder": {"evolves_to": None, "requirements": {}},
    }
    p = Pet(species="placeholder")
    ev = Evolution(registry)
    assert ev.check(p) == (None, None)


def test_evolve_increases_stats_as_signature_move():
    """Evolution should boost stats a bit (the signature move)."""
    from core.evolution import Evolution
    from core.pet import Pet

    registry = {
        "placeholder": {
            "evolves_to": "champion_form",
            "min_age_seconds": 0,
            "battles_required": 0,
            "requirements": {"h": 0, "hp": 0, "p": 0, "e": 0},
        }
    }
    p = Pet()
    p.stats["h"] = 50
    p.stats["e"] = 50
    ev = Evolution(registry)
    assert ev.evolve(p) is True
    assert p.species == "champion_form"
    # All stats should have gotten a boost
    assert p.stats["h"] == 60  # 50 + 10 boost
    assert p.stats["e"] == 60
