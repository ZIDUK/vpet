"""Shared nutrition and weight-condition rules."""

import pytest


@pytest.mark.parametrize(
    ("species", "weight", "expected"),
    [
        ("baby", 5, (5, 100, 0, 0, 0)),
        ("rookie", 6, (10, 60, 10, 10, 0)),
        ("rookie", 10, (10, 100, 0, 0, 0)),
        ("rookie", 14, (10, 140, 0, 0, 10)),
        ("champion", 20, (20, 100, 0, 0, 0)),
        ("ultimate", 42, (35, 120, 0, 0, 0)),
    ],
)
def test_body_condition_penalties_are_stage_aware(species, weight, expected):
    from core.nutrition import body_condition

    condition = body_condition(species, weight)
    assert (
        condition["reference"],
        condition["ratio"],
        condition["off_penalty"],
        condition["def_penalty"],
        condition["spd_penalty"],
    ) == expected


def test_effective_stat_clamps_and_rounds_without_mutating_base_stat():
    from core.nutrition import effective_stat

    assert effective_stat(50, 10) == 45
    assert effective_stat(99, 20) == 79
    assert effective_stat(1, 20) == 1
    assert effective_stat(50, 0) == 50


def test_unknown_species_uses_safe_neutral_reference():
    from core.nutrition import body_condition

    condition = body_condition("unlisted", 20)
    assert condition["reference"] == 20
    assert condition["off_penalty"] == 0
    assert condition["def_penalty"] == 0
    assert condition["spd_penalty"] == 0


def test_meat_and_protein_are_unlimited_foods_not_inventory_consumables():
    from core.nutrition import apply_food
    from core.pet import Pet, STATE_LIVE

    pet = Pet(species="rookie", state=STATE_LIVE)
    pet.inventory["meat"] = 0
    pet.inventory["protein"] = 0
    pet.stats.update(h=50, e=60)
    old_hp_ev = pet.ev_at("hp")
    assert apply_food(pet, "meat")["applied"]
    assert pet.get("h") == 70
    assert pet.weight == 11
    assert pet.ev_at("hp") == old_hp_ev
    assert pet.inventory["meat"] == 0
    assert apply_food(pet, "protein")["applied"]
    assert pet.get("e") == 80
    assert pet.weight == 13
    assert pet.inventory["protein"] == 0
    assert apply_food(pet, "protein")["applied"]
    assert (pet.get("e"), pet.weight) == (100, 15)


@pytest.mark.parametrize("food,stat,portions,initial,weight", [
    ("protein", "e", 6, 0, 22), ("meat", "h", 3, 100, 13),
])
def test_repeated_food_ignores_legacy_flags_and_preserves_ev(food, stat, portions, initial, weight):
    from core.nutrition import apply_food, food_preview
    from core.pet import Pet, STATE_LIVE

    pet = Pet(species="rookie", state=STATE_LIVE)
    pet.stats[stat] = initial
    pet.weight = 10
    pet.overfed_this_cycle = pet.protein_fed_this_cycle = True
    before_ev, before_dp, before_effort = dict(pet.ev), pet.dp, pet.effort
    for _ in range(portions):
        before = pet.to_dict()
        preview = food_preview(pet, food)
        assert pet.to_dict() == before
        assert preview["allowed"]
        assert apply_food(pet, food)["applied"]
        assert pet.weight == preview["weight_after"]
        assert pet.get(stat) == preview["energy_after" if stat == "e" else "hunger_after"]
    assert (pet.get(stat), pet.weight) == (100, weight)
    assert (pet.ev, pet.dp, pet.effort) == (before_ev, before_dp, before_effort)
    loaded = Pet()
    loaded.load_from_dict(pet.to_dict())
    assert apply_food(loaded, food)["applied"]


@pytest.mark.parametrize("food,stat", [("meat", "h"), ("protein", "e")])
def test_food_caps_recovery_and_no_effect_rejection(food, stat):
    from core.nutrition import apply_food, food_preview
    from core.pet import Pet, STATE_LIVE

    pet = Pet(species="rookie", state=STATE_LIVE)
    pet.stats[stat], pet.weight = 95, 98
    assert apply_food(pet, food)["applied"]
    assert (pet.get(stat), pet.weight) == (100, 99)
    before = pet.to_dict()
    assert not food_preview(pet, food)["allowed"]
    assert apply_food(pet, food)["reason"] == "full"
    assert pet.to_dict() == before
    pet.stats[stat] = 60
    for _ in range(2):
        assert apply_food(pet, food)["applied"]
    assert (pet.get(stat), pet.weight) == (100, 99)


@pytest.mark.parametrize("condition,reason", [
    ("egg", "egg"), ("dead", "dead"), ("cold", "frozen"),
    ("asleep", "asleep"), ("busy", "busy"),
])
@pytest.mark.parametrize("food", ["meat", "protein"])
def test_repeated_food_preserves_eligibility_guards(condition, reason, food):
    from core.nutrition import apply_food
    from core.pet import Pet, STATE_LIVE

    pet = Pet(species="egg" if condition == "egg" else "rookie", state=STATE_LIVE)
    if condition in ("dead", "cold"):
        setattr(pet, condition, True)
    before = pet.to_dict()
    result = apply_food(pet, food, asleep=condition == "asleep", busy=condition == "busy")
    assert not result["applied"] and result["reason"] == reason
    assert pet.to_dict() == before


def test_food_clears_matching_care_call_and_timer():
    from core.nutrition import apply_food
    from core.pet import Pet, STATE_LIVE

    pet = Pet(species="rookie", state=STATE_LIVE)
    pet.call_reason = "hunger"
    pet.call_started_ms = 123
    assert apply_food(pet, "meat")["applied"]
    assert pet.call_reason is None
    assert pet.call_started_ms == 0

    pet.call_reason = "strength"
    pet.call_started_ms = 456
    assert apply_food(pet, "protein")["applied"]
    assert pet.call_reason is None
    assert pet.call_started_ms == 0


def test_legacy_meat_and_protein_inventory_slots_are_hidden_and_not_consumed():
    from core.inventory import use_inventory_item, visible_inventory_indexes
    from core.pet import Pet, STATE_LIVE

    pet = Pet(species="rookie", state=STATE_LIVE)
    pet.inventory.update(meat=3, protein=2)
    assert 0 not in visible_inventory_indexes(pet)
    assert 4 not in visible_inventory_indexes(pet)
    assert use_inventory_item(pet, 0) == "blocked"
    assert use_inventory_item(pet, 4) == "blocked"
    assert pet.inventory["meat"] == 3
    assert pet.inventory["protein"] == 2


def test_actual_hunger_spend_reopens_food_cycle_and_training_weight_is_batched():
    from core.nutrition import complete_training_weight, consume_hunger
    from core.pet import Pet, STATE_LIVE

    pet = Pet(species="rookie", state=STATE_LIVE)
    pet.weight = 10
    pet.protein_fed_this_cycle = True
    pet.overfed_this_cycle = True
    assert consume_hunger(pet, 19) == 0
    assert pet.weight == 10
    assert pet.protein_fed_this_cycle
    assert consume_hunger(pet, 1) == 1
    assert pet.weight == 9
    assert not pet.protein_fed_this_cycle
    assert complete_training_weight(pet, 3) == 0
    assert complete_training_weight(pet, 1) == -1
    assert pet.weight == 8


def test_evolved_weight_preserves_body_condition_ratio():
    from core.nutrition import evolved_weight

    assert evolved_weight("rookie", "champion", 10) == 20
    assert evolved_weight("rookie", "champion", 14) == 28
    assert evolved_weight("unknown", "champion", 14) == 14


def test_legacy_weight_is_normalized_once_and_remains_round_trip_stable():
    from core.pet import Pet, STATE_LIVE

    pet = Pet(species="champion", state=STATE_LIVE)
    pet.load_from_dict({"species": "champion", "state": STATE_LIVE, "weight": 5})
    assert pet.weight == 16
    assert pet.legacy_weight == 5
    restored = Pet(species="egg")
    restored.load_from_dict(pet.to_dict())
    assert restored.weight == 16


def test_weight_changes_effective_combat_stats_without_mutating_base():
    from core.pet import Pet, STATE_LIVE

    pet = Pet(species="rookie", state=STATE_LIVE)
    pet.weight = 6
    base = pet.combat_stat("off")
    assert pet.effective_combat_stat("off") == max(1, (base * 90 + 50) // 100)
    assert pet.combat_stat("off") == base
    pet.weight = 14
    assert pet.effective_combat_stat("spd") < pet.combat_stat("spd")


def test_evolution_requires_healthy_weight_and_scales_weight_on_evolution():
    from config import EVOLUTION_REGISTRY
    from core.evolution import Evolution
    from core.pet import Pet, STATE_LIVE

    pet = Pet(species="rookie", state=STATE_LIVE)
    pet.stage_age_seconds = 100000
    pet.stats.update(h=80, e=80, p=80, hp=100)
    pet.weight = 7
    evolution = Evolution(EVOLUTION_REGISTRY)
    assert evolution.check(pet)[0] is None
    pet.weight = 10
    assert evolution.evolve(pet)
    assert pet.species == "champion"
    assert pet.weight == 20
