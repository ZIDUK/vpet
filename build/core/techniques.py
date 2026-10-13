"""Versioned progress for the initial Firemon practice catalogue."""

TECHNIQUES = (
    {"id": "punch", "name": "GOLPE", "power": 12, "mp": 0, "range": 1, "cooldown": 0},
    {"id": "flame", "name": "LLAMA", "power": 24, "mp": 8, "range": 2, "cooldown": 1},
    {"id": "guard", "name": "GUARDIA", "power": 0, "mp": 0, "range": 2, "cooldown": 0},
)


def bounded(value, maximum):
    try:
        return max(0, min(maximum, int(value)))
    except (TypeError, ValueError, OverflowError):
        return 0


class TechniqueProgress:
    def __init__(self, data=None):
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
            if tech["id"] in equipped and self.learned(i) and len(self.equipped) < 2:
                self.equipped.append(i)
        if not self.equipped:
            self.equipped = [0, 2]

    def learned(self, index):
        return index in (0, 2) or (index == 1 and self.training >= 2)

    def equip(self, index):
        if not self.learned(index):
            return False
        if index in self.equipped:
            if len(self.equipped) == 1:
                return False
            self.equipped.remove(index)
        else:
            if len(self.equipped) == 2:
                self.equipped.pop()
            self.equipped.append(index)
        self.equipped.sort()
        return True

    def train(self, pet, index):
        if pet.species != "rookie" or pet.dead or pet.injured or getattr(pet, "cold", False) or pet.get("e") < 4:
            return False
        if index not in (0, 1, 2):
            return False
        pet.stats["e"] -= 4
        self.training = min(255, self.training + 1)
        if self.learned(index):
            self.mastery[index] = min(100, self.mastery[index] + 5)
        self.bond = min(100, self.bond + 1)
        return True

    def to_dict(self):
        return {"version": 1, "training": self.training, "bond": self.bond,
                "mastery": {t["id"]: self.mastery[i] for i, t in enumerate(TECHNIQUES)},
                "equipped": [TECHNIQUES[i]["id"] for i in self.equipped]}
