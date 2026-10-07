"""Targeted Firemon training prototype; integer EV gains preserve hatch DNA."""
from core.dna import combat_stat

TRAINING_ENERGY_COST = 8
TRAINING_EV_GAIN = 6
TRAINING_TYPES = (
    {"stat": "off", "name": "ATAQUE", "icon": "attack", "animation": 0},
    {"stat": "def", "name": "DEFENSA", "icon": "defense", "animation": 2},
    {"stat": "spd", "name": "VELOCIDAD", "icon": "speed", "animation": "walk"},
    {"stat": "hp", "name": "VIDA", "icon": "hp", "animation": "walk"},
    {"stat": "mp", "name": "MP", "icon": "mp", "animation": 1},
    {"stat": "brn", "name": "MENTE", "icon": "mind", "animation": None},
)


def training_values(pet, index):
    """Return current and projected battle values, including HP/MP pool sizes."""
    stat = TRAINING_TYPES[index]["stat"]
    projected_ev = dict(pet.ev)
    projected_ev[stat] = min(252, pet.ev_at(stat) + TRAINING_EV_GAIN)
    before, after = pet.combat_stat(stat), combat_stat(pet.dna, projected_ev, stat)
    if stat == "hp":
        return 40 + before * 2, 40 + after * 2
    if stat == "mp":
        return 10 + before, 10 + after
    return before, after


def training_block_reason(pet, index):
    if index not in range(len(TRAINING_TYPES)):
        return "TIPO INVALIDO"
    if not pet.is_live or pet.species != "rookie" or pet.dead or pet.injured or getattr(pet, "cold", False):
        return "PET NO APTO"
    if pet.ev_at(TRAINING_TYPES[index]["stat"]) >= 252:
        return "NIVEL MAXIMO"
    if pet.get("e") < TRAINING_ENERGY_COST:
        return "FALTA ENERGIA"
    return ""


def train_attribute(pet, index):
    if training_block_reason(pet, index):
        return False
    pet.gain_ev(TRAINING_TYPES[index]["stat"], TRAINING_EV_GAIN)
    pet.stats["e"] -= TRAINING_ENERGY_COST
    pet.stats["p"] = min(100, pet.stats["p"] + 3)
    pet.effort = min(100, pet.effort + 8)
    pet.training_sessions += 1
    pet.weight = max(0, pet.weight - 1)
    return True
