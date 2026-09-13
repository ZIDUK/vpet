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
    p.stage_age_seconds = 86400
    for stat in p.stats:
        p.stats[stat] = 100

    assert Evolution(EVOLUTION_REGISTRY).evolve(p) is True
    assert p.species == "champion"


def test_flamemon_evolves_with_age_and_fifteen_battles():
    from config import EVOLUTION_REGISTRY
    from core.evolution import Evolution
    from core.pet import Pet

    p = Pet(species="champion", state="live")
    p.stage_age_seconds = 129600
    p.battles_this_form = 15
    for stat in p.stats:
        p.stats[stat] = 100

    assert Evolution(EVOLUTION_REGISTRY).evolve(p) is True
    assert p.species == "ultimate"


def test_sparkmon_color_timer_and_cm_gate():
    from config import EVOLUTION_REGISTRY
    from core.evolution import Evolution
    from core.pet import Pet

    ev = Evolution(EVOLUTION_REGISTRY)
    p = Pet(species="baby", state="live")
    p.stage_age_seconds = 43799
    p.care_mistakes = 0
    assert ev.check(p) == (None, None)
    p.stage_age_seconds = 43800
    assert ev.check(p)[0] == "rookie"
    p.care_mistakes = 2
    assert ev.check(p) == (None, None)


def test_scale_600_evolves_sparkmon_at_seventy_three_seconds():
    from config import EVOLUTION_REGISTRY
    from core.evolution import Evolution
    from core.pet import Pet

    p = Pet(species="baby", state="live")
    p.stage_age_seconds = 73
    p.care_mistakes = 0
    assert Evolution(EVOLUTION_REGISTRY).check(p, 600)[0] == "rookie"


def test_ignored_hunger_call_adds_one_care_mistake():
    from core.pet import Pet

    p = Pet(species="baby", state="live")
    p.stats["h"] = 0
    assert p.update_call(0, 1) == "started"
    assert p.call_reason == "hunger"
    assert p.update_call(600001, 1) == "missed"
    assert p.care_mistakes == 1
    assert p.call_reason is None


def test_bedtime_without_sleep_starts_lights_call():
    from core.pet import Pet

    p = Pet(species="baby", state="live")
    assert p.update_call(0, 1, hour=21, asleep=False) == "started"
    assert p.call_reason == "lights"


def test_asleep_at_bedtime_does_not_start_lights_call():
    from core.pet import Pet

    p = Pet(species="baby", state="live")
    assert p.update_call(0, 1, hour=21, asleep=True) == "none"
    assert p.call_reason is None


def test_rest_clears_lights_and_does_not_restart_same_night():
    from core.pet import Pet

    p = Pet(species="baby", state="live")
    assert p.update_call(0, 1, hour=21, asleep=False) == "started"
    p.call_reason = None
    p.answer_lights()
    assert p.update_call(1000, 1, hour=22, asleep=False) == "none"


def test_ignored_lights_call_adds_one_care_mistake():
    from core.pet import Pet

    p = Pet(species="baby", state="live")
    assert p.update_call(0, 1, hour=21, asleep=False) == "started"
    assert p.update_call(600001, 1, hour=21, asleep=False) == "none"
    assert p.update_call(3600001, 1, hour=21, asleep=False) == "missed"
    assert p.care_mistakes == 1
    assert p.call_reason is None
    assert p.update_call(3600002, 1, hour=22, asleep=False) == "none"


def test_evolution_apply_resets_care_and_keeps_wins():
    from config import EVOLUTION_REGISTRY
    from core.evolution import Evolution
    from core.pet import Pet

    p = Pet(species="baby", state="live")
    p.stage_age_seconds = 43800
    p.care_mistakes = 1
    p.battles_this_form = 3
    p.battles_won = 4
    assert Evolution(EVOLUTION_REGISTRY).evolve(p) is True
    assert p.species == "rookie"
    assert p.care_mistakes == 0
    assert p.battles_this_form == 0
    assert p.stage_age_seconds == 0
    assert p.battles_won == 4


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
    assert evolution.force(p) is True
    assert p.species == "egg"


def test_evolution_tree_shares_trunk_and_forks_after_spark():
    from core.evolution import (
        EVOLUTION_NODE_COUNT,
        EVO_CHIP,
        EVO_COLOR_Y,
        EVO_DARK_Y,
        evolution_tree_node,
        evolution_tree_xy,
    )

    assert EVOLUTION_NODE_COUNT == 8
    assert [evolution_tree_node(index) for index in range(8)] == [
        (0, False),
        (1, False),
        (2, False),
        (3, False),
        (4, False),
        (2, True),
        (3, True),
        (4, True),
    ]
    egg_x, egg_y = evolution_tree_xy(0)
    dark_x, dark_y = evolution_tree_xy(5)
    assert egg_y == EVO_COLOR_Y
    assert dark_y == EVO_DARK_Y
    assert dark_x > egg_x + EVO_CHIP
    assert evolution_tree_xy(2)[0] == dark_x


def test_evolution_card_shows_reach_rules_or_hides_unknown():
    from config import EVOLUTION_REGISTRY
    from core.evolution import evolution_card
    from core.pet import Pet, STATE_LIVE

    pet = Pet(species="rookie", state=STATE_LIVE)
    pet.stage_age_seconds = 12
    pet.care_mistakes = 1
    fire = evolution_card(2, pet, EVOLUTION_REGISTRY, spanish=False)
    assert fire["label"] == "FIRE"
    assert fire["status"] == "NOW"
    assert "CM<=1" in fire["requirements"]
    assert "12s" in fire["snapshot"]
    spark = evolution_card(1, pet, EVOLUTION_REGISTRY, spanish=False)
    assert spark["status"] == "REACHED"
    assert "8S" in spark["requirements"]
    dark = evolution_card(5, pet, EVOLUTION_REGISTRY, spanish=False)
    assert dark["hidden"] is True
    assert dark["label"] == "???"
    assert dark["requirements"] == ""
    assert dark["snapshot"] == ""


def test_requirement_lines_split_after_the_timer():
    from core.evolution import split_requirement_lines

    assert split_requirement_lines("8S") == ("8S", "")
    assert split_requirement_lines("12H10M CM<=1") == ("12H10M", "CM<=1")
    assert split_requirement_lines("24H H55 E55 P55 HP75") == ("24H", "H55 E55 P55 HP75")


def test_evolution_window_follows_selected_node():
    from core.evolution import evolution_window

    assert evolution_window(0) == (0, 1, 2)
    assert evolution_window(1) == (0, 1, 2)
    assert evolution_window(4) == (3, 4, 5)
    assert evolution_window(7) == (5, 6, 7)
