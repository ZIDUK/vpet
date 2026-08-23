"""Tests for evolution rules."""
import pytest


def test_evolution_check_blocks_when_stats_low():
    from core.evolution import Evolution
    from core.pet import Pet

    # Simulate an agumon registry
    registry = {
        "agumon": {
            "evolves_to": "greymon",
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
        "agumon": {
            "evolves_to": "greymon",
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
    assert new_form == "greymon"
    assert reason is not None


def test_evolution_check_blocks_when_too_young(monkeypatch):
    from core.evolution import Evolution
    from core.pet import Pet
    import core.pet as pet_mod

    fake_t = [100.0]
    monkeypatch.setattr(pet_mod.time, "monotonic", lambda: fake_t[0])

    registry = {
        "agumon": {
            "evolves_to": "greymon",
            "min_age_seconds": 200,  # not enough yet
            "battles_required": 0,
            "requirements": {},
        }
    }
    p = Pet()
    fake_t[0] = 150.0  # less than 200
    ev = Evolution(registry)
    assert ev.check(p) == (None, None)


def test_evolution_check_blocks_when_battles_required_not_met():
    from core.evolution import Evolution
    from core.pet import Pet

    registry = {
        "agumon": {
            "evolves_to": "greymon",
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
        "wargreymon": {"evolves_to": None, "requirements": {}},
    }
    p = Pet(species="wargreymon")
    ev = Evolution(registry)
    assert ev.check(p) == (None, None)
