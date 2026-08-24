"""Pet data model.

A Pet has 4 stats:
  - hunger (h):   0=starving, 100=full
  - energy (e):   0=exhausted, 100=rested
  - happiness (p):0=miserable, 100=joyful
  - health (hp):  0=critical, 100=perfect

Stats decay over time. Actions raise stats. Evolution triggers based on stat thresholds.
A Pet also has a lifecycle state:
  - "egg"      : in the egg, showing the hatch animation
  - "hatching" : in the middle of the hatch animation (transient)
  - "live"     : hatched, regular pet gameplay
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

# Lifecycle states
STATE_EGG = "egg"
STATE_HATCHING = "hatching"
STATE_LIVE = "live"

# Default species the pet starts as (the egg)
DEFAULT_SPECIES = "sproutspore"
DEFAULT_LINE = "sprout_line"


class Pet:
    """Holds pet state: stats, age, species, line, lifecycle state."""

    def __init__(self, species=DEFAULT_SPECIES, line=DEFAULT_LINE, state=None):
        self.species = species      # current form: "sproutspore", "sprouto", "thornback", "hydravine"
        self.line = line            # evolution line: "sprout_line"
        self.stats = {"h": 70, "e": 70, "p": 70, "hp": 70}
        self.born_at = time.monotonic()
        self.last_decay = time.monotonic()
        self.battles_won = 0
        # Lifecycle: starts as egg unless overridden (live = already hatched)
        self.state = state if state is not None else STATE_EGG
        self.hatch_started_at = time.monotonic() if self.state == STATE_EGG else None

    @property
    def age_seconds(self):
        return time.monotonic() - self.born_at

    @property
    def is_egg(self):
        return self.state == STATE_EGG

    @property
    def is_hatching(self):
        return self.state == STATE_HATCHING

    @property
    def is_live(self):
        return self.state == STATE_LIVE

    def get(self, stat):
        return self.stats[stat]

    def apply_action(self, menu_idx):
        """Apply action effects from ACTION_EFFECTS[menu_idx]."""
        effects = ACTION_EFFECTS.get(menu_idx, {})
        for stat, delta in effects.items():
            self.stats[stat] = max(0, min(100, self.stats[stat] + delta))

    def decay_if_due(self):
        """Decay stats every DECAY_PERIOD_SECONDS. Returns True if decay happened.

        Only decays in LIVE state. Eggs don't decay.
        """
        if self.state != STATE_LIVE:
            return False
        now = time.monotonic()
        if now - self.last_decay > DECAY_PERIOD_SECONDS:
            for stat in STAT_ORDER:
                self.stats[stat] = max(0, self.stats[stat] - DECAY_AMOUNT)
            self.last_decay = now
            return True
        return False

    def start_hatch(self):
        """Transition from EGG to HATCHING. The animation runs for hatch_duration_seconds."""
        if self.state == STATE_EGG:
            self.state = STATE_HATCHING
            self.hatch_started_at = time.monotonic()

    def hatch_progress(self, hatch_duration):
        """Returns 0.0..1.0 progress through the hatch animation, or 1.0 if done."""
        if self.state != STATE_HATCHING or self.hatch_started_at is None:
            return 1.0
        elapsed = time.monotonic() - self.hatch_started_at
        return min(1.0, elapsed / hatch_duration)

    def complete_hatch(self, next_species):
        """Complete the hatch: transition to LIVE with the new species."""
        self.state = STATE_LIVE
        self.species = next_species
        # Boost stats a bit on hatch (signature move)
        for stat in self.stats:
            self.stats[stat] = min(100, self.stats[stat] + 15)
        self.hatch_started_at = None

    def to_dict(self):
        """Serialise for save file."""
        return {
            "species": self.species,
            "line": self.line,
            "state": self.state,
            "stats": dict(self.stats),
            "battles_won": self.battles_won,
        }

    def load_from_dict(self, d):
        self.species = d.get("species", self.species)
        self.line = d.get("line", self.line)
        self.state = d.get("state", STATE_LIVE)  # backward compat: if no state, assume live
        self.stats = dict(d.get("stats", self.stats))
        self.battles_won = d.get("battles_won", 0)
        # If we loaded as an egg, restart the hatch timer
        if self.state == STATE_EGG:
            self.hatch_started_at = time.monotonic()
