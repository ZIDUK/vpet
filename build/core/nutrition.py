"""Portable nutrition and body-condition rules shared with vpet_core."""
from core.item_catalog import effect_amount

BODY_WEIGHT_REFERENCE = {
    "baby": 5,
    "rookie": 10,
    "champion": 20,
    "ultimate": 35,
}


def body_condition(species, weight):
    """Return stage-relative condition and bounded combat penalties."""
    reference = BODY_WEIGHT_REFERENCE.get(str(species).lower())
    if reference is None:
        reference = max(1, int(weight))
    weight = max(1, min(99, int(weight)))
    ratio = (100 * weight + reference // 2) // reference
    low = min(15, (max(0, 80 - ratio) + 1) // 2)
    high = min(20, (max(0, ratio - 120) + 1) // 2)
    return {
        "reference": reference,
        "ratio": ratio,
        "off_penalty": low,
        "def_penalty": low,
        "spd_penalty": high,
    }


def healthy_weight_range(species):
    """Return the inclusive 80%-120% target range for the current stage."""
    reference = BODY_WEIGHT_REFERENCE.get(str(species).lower())
    if reference is None:
        return None
    return ((80 * reference + 99) // 100, (120 * reference) // 100)


def effective_stat(base, penalty):
    """Apply a percentage penalty with integer rounding and combat bounds."""
    base = max(1, min(99, int(base)))
    penalty = max(0, min(100, int(penalty)))
    return max(1, (base * (100 - penalty) + 50) // 100)


FOOD_IDS = ("meat", "protein")


def food_preview(pet, food_id, available=True, asleep=False, busy=False):
    """Describe an unlimited feeding action without changing pet state."""
    result = {
        "allowed": False,
        "reason": "ok",
        "hunger_after": int(pet.get("h")),
        "energy_after": int(pet.get("e")),
        "weight_after": max(1, min(99, int(pet.weight))),
    }
    if food_id not in FOOD_IDS:
        result["reason"] = "invalid_food"
    elif getattr(pet, "species", "egg") == "egg" or getattr(pet, "is_egg", False):
        result["reason"] = "egg"
    elif getattr(pet, "dead", False):
        result["reason"] = "dead"
    elif asleep:
        result["reason"] = "asleep"
    elif busy:
        result["reason"] = "busy"
    elif food_id == "meat" and pet.get("h") >= 100:
        if getattr(pet, "overfed_this_cycle", False):
            result["reason"] = "overfeed_used"
        else:
            result.update(allowed=True, hunger_after=100,
                          weight_after=min(99, int(pet.weight) + effect_amount("meat", "weight", "weight")))
    elif food_id == "protein" and getattr(pet, "protein_fed_this_cycle", False):
        result["reason"] = "protein_cycle"
    elif food_id == "protein" and pet.get("e") > 100 - effect_amount("protein", "restore", "e"):
        result["reason"] = "full"
    else:
        result["allowed"] = True
        if food_id == "meat":
            result["hunger_after"] = min(100, pet.get("h") + effect_amount("meat", "restore", "h"))
            result["weight_after"] = min(99, int(pet.weight) + effect_amount("meat", "weight", "weight"))
        else:
            result["energy_after"] = min(100, pet.get("e") + effect_amount("protein", "restore", "e"))
            result["weight_after"] = min(99, int(pet.weight) + effect_amount("protein", "weight", "weight"))
    return result


def apply_food(pet, food_id, available=True, asleep=False, busy=False):
    """Apply one validated feeding action; food has no inventory stock."""
    preview = food_preview(pet, food_id, available, asleep, busy)
    if not preview["allowed"]:
        return {"applied": False, "reason": preview["reason"], "changed_fields": {}}
    weight_before = int(pet.weight)
    if food_id == "meat":
        gained = preview["hunger_after"] - pet.get("h")
        pet.stats["h"] = preview["hunger_after"]
        pet.weight = preview["weight_after"]
        if gained == 0:
            pet.overfed_this_cycle = True
            pet.overfeeds = min(99, getattr(pet, "overfeeds", 0) + 1)
        pet.meals = getattr(pet, "meals", 0) + 1
        if getattr(pet, "call_reason", None) == "hunger" and preview["hunger_after"] > 0:
            pet.call_reason = None
            pet.call_started_ms = 0
        changed = {"hunger": gained, "weight": pet.weight - weight_before}
    else:
        energy_before = pet.get("e")
        pet.stats["e"] = preview["energy_after"]
        pet.weight = preview["weight_after"]
        pet.protein_fed_this_cycle = True
        if (getattr(pet, "call_reason", None) == "strength"
                and preview["energy_after"] > 0):
            pet.call_reason = None
            pet.call_started_ms = 0
        changed = {"energy": preview["energy_after"] - energy_before, "weight": pet.weight - weight_before}
    return {"applied": True, "reason": "ok", "changed_fields": changed}


def consume_hunger(pet, lost_points):
    """Count only real hunger decay toward the metabolic cycle."""
    lost_points = max(0, int(lost_points))
    accumulated = getattr(pet, "hunger_cycle_remainder", 0) + lost_points
    cycles, pet.hunger_cycle_remainder = divmod(accumulated, 20)
    pet.weight = max(1, int(pet.weight) - cycles)
    if cycles:
        pet.protein_fed_this_cycle = False
        pet.overfed_this_cycle = False
    return cycles


def complete_training_weight(pet, repetitions):
    """Apply training weight loss, preserving fractional progress."""
    repetitions = max(0, int(repetitions))
    total = getattr(pet, "training_weight_remainder", 0) + repetitions
    loss, pet.training_weight_remainder = divmod(total, 4)
    before = int(pet.weight)
    pet.weight = max(1, before - loss)
    return int(pet.weight) - before


def evolved_weight(from_species, to_species, weight):
    """Scale weight proportionally to the target form's reference body."""
    source = BODY_WEIGHT_REFERENCE.get(str(from_species).lower())
    target = BODY_WEIGHT_REFERENCE.get(str(to_species).lower())
    weight = max(1, min(99, int(weight)))
    if source is None or target is None:
        return weight
    return max(1, min(99, (weight * target + source // 2) // source))


def migrate_legacy_weight(species, weight):
    """Move a legacy save to the nearest healthy boundary exactly once."""
    reference = BODY_WEIGHT_REFERENCE.get(str(species).lower())
    weight = max(1, min(99, int(weight)))
    if reference is None:
        return weight
    low = (80 * reference + 99) // 100
    high = (120 * reference) // 100
    if weight < low:
        return low
    if weight > high:
        return high
    return weight
