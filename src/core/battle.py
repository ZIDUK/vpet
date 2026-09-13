"""Battle system.

A battle is a turn-based exchange between the pet and an NPC. Each round:
  1. Pet attacks (damage based on pet's happiness + energy)
  2. NPC attacks (damage based on NPC's stats)
  3. Repeat until one side's HP reaches 0

The battle ends with a victory (pet HP > 0) or defeat (pet HP == 0).
Victory increments pet.battles_won. Defeat damages happiness.

NPCs are simple dicts: {name, hp, attack, sprite}.
"""
import random


class Battle:
    def __init__(self, pet, npc):
        self.pet = pet
        self.npc = npc
        self.pet_hp = pet.get("hp")
        self.npc_hp = npc["hp"]
        self.log = []
        self.over = False
        self.won = False

    def pet_attack(self):
        """Pet's attack power scales with happiness + energy."""
        if self.over:
            return
        power = (self.pet.get("p") + self.pet.get("e")) // 4
        power = max(1, power + random.randint(-3, 3))
        self.npc_hp = max(0, self.npc_hp - power)
        self.log.append(("pet", power))
        self._check_end()

    def npc_attack(self):
        """NPC's attack is fixed ± small random."""
        if self.over:
            return
        power = self.npc.get("attack", 10) + random.randint(-2, 2)
        power = max(1, power)
        self.pet_hp = max(0, self.pet_hp - power)
        self.log.append(("npc", power))
        self._check_end()

    def _check_end(self):
        if self.npc_hp == 0:
            self.over = True
            self.won = True
            self.pet.battles_won += 1
            self.pet.battles_this_form = getattr(self.pet, "battles_this_form", 0) + 1
        elif self.pet_hp == 0:
            self.over = True
            self.won = False
            # Defeat: reduce happiness
            self.pet.stats["p"] = max(0, self.pet.stats["p"] - 20)

    def commit_to_pet(self):
        """Save pet HP back to pet stats after battle ends."""
        self.pet.stats["hp"] = self.pet_hp
