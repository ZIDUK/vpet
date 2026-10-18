"""Stable technique IDs and stage-gated progress for the fire evolution line."""

TECHNIQUES = (
    {"id": "punch", "name": "GOLPE", "power": 12, "mp": 0, "range": 1, "cooldown": 0, "element": "neutral"},
    {"id": "flame", "name": "LLAMA", "power": 24, "mp": 8, "range": 2, "cooldown": 1, "element": "fire"},
    {"id": "guard", "name": "GUARDIA", "power": 0, "mp": 0, "range": 2, "cooldown": 0, "element": None},
    {"id": "flare", "name": "RAFAGA", "power": 30, "mp": 12, "range": 2, "cooldown": 1, "element": "fire"},
    {"id": "inferno", "name": "INFERNO", "power": 38, "mp": 18, "range": 2, "cooldown": 2, "element": "fire"},
)
REQUIRED_STAGE = (1, 1, 1, 2, 3)
REQUIRED_TRAINING = (0, 2, 0, 4, 6)


def technique_name(index, english=False):
    return ("PUNCH", "FLAME", "GUARD", "FLARE", "INFERNO")[index] if english else TECHNIQUES[index]["name"]


def technique_stage(species):
    return {"rookie": 1, "champion": 2, "ultimate": 3}.get(species, 0)


def bounded(value, maximum):
    try:
        return max(0, min(maximum, int(value)))
    except (TypeError, ValueError, OverflowError):
        return 0


class TechniqueProgress:
    def __init__(self, data=None, species="rookie"):
        data = data if isinstance(data, dict) and data.get("version", 1) == 1 else {}
        self.training = bounded(data.get("training", 0), 255)
        self.bond = bounded(data.get("bond", 50), 100)
        mastery = data.get("mastery", {})
        mastery = mastery if isinstance(mastery, dict) else {}
        self.mastery = [bounded(mastery.get(t["id"], 0), 100) for t in TECHNIQUES]
        equipped = data.get("equipped", ["punch", "guard"])
        equipped = equipped if isinstance(equipped, list) else []
        self.equipped = []
        for i, tech in enumerate(TECHNIQUES):
            if tech["id"] in equipped and self.learned(i, species) and len(self.equipped) < self.capacity(species):
                self.equipped.append(i)
        if not self.equipped:
            self.equipped = [0, 2]

    @staticmethod
    def capacity(species):
        stage = technique_stage(species)
        return stage + 1 if stage else 0

    def learned(self, index, species="rookie"):
        return (0 <= index < len(TECHNIQUES) and technique_stage(species) >= REQUIRED_STAGE[index]
                and self.training >= REQUIRED_TRAINING[index])

    def equip(self, index, species="rookie"):
        if not self.learned(index, species):
            return False
        if index in self.equipped:
            if len(self.equipped) == 1:
                return False
            self.equipped.remove(index)
        else:
            if len(self.equipped) >= self.capacity(species):
                self.equipped.pop()
            self.equipped.append(index)
        self.equipped.sort()
        return True

    def train(self, pet, index):
        if pet.exploration.away:
            return False
        if not technique_stage(pet.species) or pet.dead or pet.injured or getattr(pet, "cold", False) or pet.get("e") < 4:
            return False
        if not 0 <= index < len(TECHNIQUES) or technique_stage(pet.species) < REQUIRED_STAGE[index]:
            return False
        pet.stats["e"] -= 4
        self.training = min(255, self.training + 1)
        if self.learned(index, pet.species):
            self.mastery[index] = min(100, self.mastery[index] + 5)
        self.bond = min(100, self.bond + 1)
        return True

    def to_dict(self):
        return {"version": 1, "training": self.training, "bond": self.bond,
                "mastery": {t["id"]: self.mastery[i] for i, t in enumerate(TECHNIQUES)},
                "equipped": [TECHNIQUES[i]["id"] for i in self.equipped]}
