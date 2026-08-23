"""Pet data model.

A Pet has 4 stats:
  - hunger (h):   0=starving, 100=full
  - energy (e):   0=exhausted, 100=rested
  - happiness (p):0=miserable, 100=joyful
  - health (hp):  0=critical, 100=perfect

Stats decay over time. Actions raise stats. Evolution triggers based on stat thresholds.
"""
import time

# Stat names in display order (left to right on the device's stat bar row)
STAT_ORDER = ["h", "e", "p", "hp"]
STAT_LABELS = {"h": "HUN", "e": "ENR", "p": "MOO", "hp": "HP"}
STAT_COLORS = {
    "h": 0xffd700,  # gold
    "e": 0x4080ff,  # blue
    "p": 0x40ff60,  # green
    "hp": 0xff5050, # red
}

# Decay rates: amount lost per DECAY_PERIOD_SECONDS
DECAY_PERIOD_SECONDS = 3
DECAY_AMOUNT = 1

# Action effects (added to current stat, capped at 100)
ACTION_EFFECTS = {
    # menu_idx -> {stat: delta}
    0: {"h": +25},              # FEED
    1: {"hp": +30},             # HEAL
    2: {"p": +15},              # PLAY
    3: {"h": +10, "hp": +10},   # REST
}


class Pet:
    """Holds pet state: stats, age, species, line."""

    def __init__(self, species="agumon", line="agumon_line"):
        self.species = species      # current form: "agumon", "greymon", ...
        self.line = line            # evolution line: "agumon_line" | "gabumon_line"
        self.stats = {"h": 70, "e": 70, "p": 70, "hp": 70}
        self.born_at = time.monotonic()
        self.last_decay = time.monotonic()
        self.battles_won = 0

    @property
    def age_seconds(self):
        return time.monotonic() - self.born_at

    def get(self, stat):
        return self.stats[stat]

    def apply_action(self, menu_idx):
        """Apply action effects from ACTION_EFFECTS[menu_idx]."""
        effects = ACTION_EFFECTS.get(menu_idx, {})
        for stat, delta in effects.items():
            self.stats[stat] = max(0, min(100, self.stats[stat] + delta))

    def decay_if_due(self):
        """Decay stats every DECAY_PERIOD_SECONDS. Returns True if decay happened."""
        now = time.monotonic()
        if now - self.last_decay > DECAY_PERIOD_SECONDS:
            for stat in STAT_ORDER:
                self.stats[stat] = max(0, self.stats[stat] - DECAY_AMOUNT)
            self.last_decay = now
            return True
        return False

    def to_dict(self):
        """Serialise for save file (excluding time.monotonic)."""
        return {
            "species": self.species,
            "line": self.line,
            "stats": dict(self.stats),
            "battles_won": self.battles_won,
        }

    def load_from_dict(self, d):
        self.species = d.get("species", self.species)
        self.line = d.get("line", self.line)
        self.stats = dict(d.get("stats", self.stats))
        self.battles_won = d.get("battles_won", 0)
