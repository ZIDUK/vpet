"""Read-only outgoing evolution requirements; never applies an evolution."""
from core.evolution import EVOLUTION_NODE_COUNT, evolution_current_stage

STAGES = ("egg", "baby", "rookie", "champion", "ultimate")
NAMES = ("EGG", "SPARKMON", "FIREMON", "FLAMEMON", "DRAGFIREMON")
ROWS_PER_PAGE = 4


def evolution_progress(pet, registry, selected=None, scale=1):
    current = evolution_current_stage(pet)
    stage = current if selected is None else int(selected) % EVOLUTION_NODE_COUNT
    result = {"stage": stage, "name": NAMES[stage], "state": "progress", "rows": [], "pages": 1}
    if stage != current:
        result["state"] = "reached" if stage < current else "hidden"
        if stage > current:
            result["name"] = "???"
        return result
    if stage == 0:
        result["state"] = "egg"
        return result
    rule = registry.get(STAGES[stage], {})
    if not rule.get("evolves_to"):
        result["state"] = "final"
        return result
    if rule.get("requirements_pending") or not rule.get("automatic", True):
        result["state"] = "unavailable"
        return result
    scale = max(1, int(scale))
    rows = result["rows"]

    def add(kind, current, target, upper=0, met=None, remaining=0):
        rows.append(dict(kind=kind, current=int(current), target=int(target), upper=int(upper),
                         met=bool(current >= target if met is None else met), remaining=remaining))

    target = int(rule.get("min_stage_age_seconds", rule.get("min_age_seconds", 0)))
    if target:
        elapsed = int(pet.stage_age_seconds) * scale
        add("time", elapsed, target, remaining=(max(0, target - elapsed) + scale - 1) // scale)
    if rule.get("max_care_mistakes") is not None:
        target = rule["max_care_mistakes"]
        add("mistakes", pet.care_mistakes, target, met=pet.care_mistakes <= target)
    if rule.get("battles_required", 0):
        add("battles", pet.battles_this_form, rule["battles_required"])
        played = pet.battles_won + pet.battles_lost
        add("wins", pet.battles_won * 100 // played if played else 0, 60, upper=played,
            met=not played or pet.battles_won * 100 >= 60 * played)
    for key, kind in (("h", "hunger"), ("e", "energy"), ("p", "mood"), ("hp", "health")):
        if rule.get("requirements", {}).get(key, 0):
            add(kind, pet.get(key), rule["requirements"][key])
    if rule.get("min_weight") is not None or rule.get("max_weight") is not None:
        low, high = rule.get("min_weight", 1), rule.get("max_weight", 99)
        add("weight", pet.weight, low, high, low <= pet.weight <= high)
    result["pages"] = max(1, (len(rows) + ROWS_PER_PAGE - 1) // ROWS_PER_PAGE)
    return result


def next_detail_index(pet, registry, index):
    stage = int(index) % EVOLUTION_NODE_COUNT
    pages = evolution_progress(pet, registry, stage)["pages"]
    return stage + EVOLUTION_NODE_COUNT * ((int(index) // EVOLUTION_NODE_COUNT + 1) % pages)
