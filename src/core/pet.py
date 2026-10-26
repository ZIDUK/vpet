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

from core.dna import SPECIES_ID, combat_stat, iv_at, mix_entropy
from core.growth import adult_rank, ev_limit, stat_limit, projected_ev
from core.techniques import TechniqueProgress
from core.exploration import Exploration
from core.sleep import SleepRoutine
from core.profile import PetProfile
from core.item_catalog import DEFAULT_STOCK, ITEM_BY_ID, effect_amount
from core.nutrition import (apply_food, body_condition, complete_training_weight,
                            consume_hunger, effective_stat, migrate_legacy_weight)

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
    3: {"e": +30, "hp": +10},   # REST
}

# Lifecycle states
STATE_EGG = "egg"
STATE_HATCHING = "hatching"
STATE_LIVE = "live"

# Default species the pet starts as (the egg stage)
DEFAULT_SPECIES = "egg"
DEFAULT_LINE = "custom_line"

# Canonical stage progression. Sprites live in /<Stage>/<file>.bmp on the device.
STAGE_ORDER = ["egg", "baby", "rookie", "champion", "ultimate", "mega"]
STAGE_FRIENDLY = {
    "egg": "Egg",
    "baby": "Sparkmon",
    "rookie": "Firemon",
    "champion": "Flamemon",
    "ultimate": "Dragfiremon",
    "mega": "???",           # no name yet, future evolution
}


class Pet:
    """Holds pet state: stats, age, species, line, lifecycle state."""

    def __init__(self, species=DEFAULT_SPECIES, line=DEFAULT_LINE, state=None):
        self._learning = None
        self.profile = PetProfile()
        self.species = species      # current form: "sproutspore", "sprouto", "thornback", "hydravine"
        self.line = line            # evolution line: "sprout_line"
        self.stats = {"h": 70, "e": 70, "p": 70, "hp": 70}
        self.inventory = dict(DEFAULT_STOCK)
        from core.adopted_items import load_stock
        self.adopted_inventory, self.item_reward_cursor = load_stock(None, missing=True)
        self.effort = 0
        self.language = "EN"
        self.sound_enabled = True
        self.cold = False
        self.born_at = time.monotonic()
        self.last_decay = time.monotonic()
        self.battles_won = 0
        self.battles_lost = 0
        self.battles_this_form = 0
        self.care_mistakes = 0
        self.call_reason = None
        self.call_started_ms = 0
        self.lights_handled_tonight = False
        self.stage_age_seconds = 0
        self.meals = 0
        self.training_sessions = 0
        self.menu_train_sessions = 0
        self.weight = 5
        if state == STATE_LIVE:
            self.weight = body_condition(species, 5)["reference"]
        self.hunger_cycle_remainder = 0
        self.training_weight_remainder = 0
        self.protein_fed_this_cycle = False
        self.dp = 1
        self.protein = 0
        self.protein_uses = 0
        self.overfeeds = 0
        self.overfed_this_cycle = False
        self.injured = False
        self.injuries = 0
        self.injured_ms = 0
        self.dead = False
        self.last_battle_won = False
        self.battle_roll = None
        self.dna = [0, 0, 0, 0]
        self.ev = {"hp": 0, "mp": 0, "off": 0, "def": 0, "spd": 0, "brn": 0}
        self.techniques = TechniqueProgress()
        self.exploration = Exploration()
        self.sleep = SleepRoutine()
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
        if self.state != STATE_LIVE or self.cold:
            return False
        now = time.monotonic()
        if now - self.last_decay > DECAY_PERIOD_SECONDS:
            for stat in STAT_ORDER:
                before = self.stats[stat]
                self.stats[stat] = max(0, self.stats[stat] - DECAY_AMOUNT)
                if stat == "h" and before > self.stats[stat]:
                    consume_hunger(self, before - self.stats[stat])
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

    def reset_to_egg(self):
        language = self.language
        sound = self.sound_enabled
        line = self.line
        stock, cursor = dict(self.adopted_inventory), self.item_reward_cursor
        self.__init__(species=DEFAULT_SPECIES, line=line, state=STATE_EGG)
        self.adopted_inventory, self.item_reward_cursor = stock, cursor
        self.language = language
        self.sound_enabled = sound

    def reset_after_evolution(self):
        self.care_mistakes = 0
        self.call_reason = None
        self.call_started_ms = 0
        self.lights_handled_tonight = False
        self.training_sessions = 0
        self.battles_this_form = 0
        self.meals = 0
        self.stage_age_seconds = 0
        self.protein = 0
        self.protein_uses = 0
        self.overfeeds = 0
        self.overfed_this_cycle = False
        self.injured = False
        self.injuries = 0
        self.injured_ms = 0
        self.dead = False
        self.last_battle_won = False
        self.dp = 1
        # v1 balance: the per-care-cycle menu training cap resets on
        # evolution. The field is absent on legacy saves; default to 0.
        self.menu_train_sessions = 0

    def can_feed(self):
        if self.is_egg:
            return False
        return not (self.stats.get("h", 0) >= 100 and self.overfed_this_cycle)

    def has_dna(self):
        return any(self.dna)

    def roll_dna(self, entropy):
        self.dna = mix_entropy(entropy)

    def restore_dna(self, dna):
        self.dna = [int(value) & 0xFF for value in list(dna)[:4]]
        while len(self.dna) < 4:
            self.dna.append(0)

    def restore_ev(self, ev):
        for key in self.ev:
            self.ev[key] = min(252, max(0, int(ev.get(key, 0))))

    def iv_at(self, stat):
        return iv_at(self.dna, stat)

    def ev_at(self, stat):
        return int(self.ev.get(stat, 0))

    def combat_stat(self, stat):
        return combat_stat(self.dna, self.ev, stat, self.species)

    def ev_limit(self):
        return ev_limit(self.species)

    def stat_limit(self, stat):
        rank = adult_rank(self.species)
        return stat_limit(self.iv_at(stat), rank) if rank else 99

    def effective_combat_stat(self, stat):
        condition = body_condition(self.species, self.weight)
        penalty = condition.get({"off": "off_penalty", "def": "def_penalty",
                                "spd": "spd_penalty"}.get(stat, ""), 0)
        return effective_stat(self.combat_stat(stat), penalty)

    def use_food(self, food_id, asleep=False, busy=False):
        return apply_food(self, food_id, asleep=asleep, busy=busy)

    def gain_ev(self, stat, amount):
        if stat not in self.ev:
            return
        self.ev[stat] = projected_ev(self.ev[stat], amount, self.species)

    def feed(self, from_item=False):
        return apply_food(self, "meat")["applied"]

    def effort_hearts(self):
        return min(4, getattr(self, "training_sessions", 0) // 4)

    def use_protein(self):
        self.stats["e"] = min(100, self.stats.get("e", 0) + 20)
        self.protein_uses = min(99, getattr(self, "protein_uses", 0) + 1)
        if self.protein_uses % 4 == 0:
            self.protein = min(7, self.protein + 1)
            self.dp = min(3, self.dp + 1)
        if self.call_reason == "strength" and self.stats.get("e", 0) > 0:
            self.call_reason = None

    def use_medkit(self):
        if not self.injured:
            return False
        self.injured = False
        self.injured_ms = 0
        self.stats["hp"] = min(100, self.stats.get("hp", 0) + effect_amount("medkit", "restore", "hp"))
        return True

    def can_battle(self):
        if self.is_egg or self.dead or self.injured or self.dp <= 0:
            return False
        if self.species == "baby":
            return False
        return True

    def finish_battle(self):
        if not self.can_battle():
            return False
        self.dp = max(0, self.dp - 1)
        self.stats["e"] = max(0, self.stats.get("e", 0) - 12)
        self.effort = min(100, getattr(self, "effort", 0) + 4)
        self.battles_this_form = getattr(self, "battles_this_form", 0) + 1
        roll = self.battle_roll if self.battle_roll is not None else (int(self.age_seconds) + self.battles_this_form * 17) % 100
        condition = body_condition(self.species, self.weight)
        condition_penalty = (condition["off_penalty"] + condition["def_penalty"]
                             + condition["spd_penalty"] + 2) // 3
        chance = (50 + self.effort_hearts() * 8 + self.stats.get("e", 0) // 20
                  - condition_penalty)
        chance = max(15, min(90, chance))
        self.last_battle_won = roll < chance
        if self.last_battle_won:
            self.battles_won += 1
        else:
            self.battles_lost += 1
            self._injure()
        self.gain_ev("off", 1)
        self.gain_ev("brn", 1)
        return True

    def _injure(self):
        self.injured = True
        self.injuries = min(99, getattr(self, "injuries", 0) + 1)
        self._check_death()

    def _check_death(self):
        if self.is_egg:
            return
        if self.injuries >= 15 or (self.injured and getattr(self, "injured_ms", 0) >= 21600000):
            self.dead = True

    def restore_dp(self):
        self.dp = min(3, getattr(self, "dp", 0) + 1)

    def note_wake(self, hour=12):
        if self.is_egg:
            return
        if hour < 8 or hour >= 21:
            self.care_mistakes = min(99, self.care_mistakes + 1)

    def answer_lights(self):
        if self.call_reason == "lights":
            self.call_reason = None
            self.call_started_ms = 0
        self.lights_handled_tonight = True

    def update_call(self, now_ms, scale, hour=12, asleep=False, lights_enabled=True):
        """Return 'started', 'missed', or 'none'. Scale 1 = COLOR, 600 = sim."""
        if not lights_enabled and self.call_reason == "lights":
            self.call_reason = None
            self.call_started_ms = 0
        if self.state == STATE_EGG or scale <= 0:
            return "none"
        if self.call_reason == "hunger" and self.stats.get("h", 0) > 0:
            self.call_reason = None
            self.call_started_ms = 0
        if self.call_reason == "strength" and self.stats.get("e", 0) > 0:
            self.call_reason = None
            self.call_started_ms = 0
        night = hour >= 21 or hour < 8
        if not night:
            self.lights_handled_tonight = False
        margin = (3600000 if self.call_reason == "lights" else 600000) // scale
        if self.call_reason and now_ms - self.call_started_ms >= margin:
            self.care_mistakes = min(99, self.care_mistakes + 1)
            start_strength = self.call_reason == "hunger" and self.stats.get("e", 0) == 0
            if self.call_reason == "lights":
                self.lights_handled_tonight = True
            self.call_reason = None
            self.call_started_ms = 0
            if start_strength:
                self.call_reason = "strength"
                self.call_started_ms = now_ms
            return "missed"
        if self.call_reason:
            return "none"
        if self.stats.get("h", 0) == 0:
            self.call_reason = "hunger"
            self.call_started_ms = now_ms
            return "started"
        if self.stats.get("e", 0) == 0:
            self.call_reason = "strength"
            self.call_started_ms = now_ms
            return "started"
        if lights_enabled and night and not asleep and not self.lights_handled_tonight:
            self.lights_handled_tonight = True
            self.call_reason = "lights"
            self.call_started_ms = now_ms
            return "started"
        return "none"

    def complete_hatch(self, next_species, entropy=None, preserve_dna=False):
        """Complete the hatch: transition to LIVE with the new species."""
        self.state = STATE_LIVE
        self.species = next_species
        # Boost stats a bit on hatch (signature move)
        for stat in self.stats:
            self.stats[stat] = min(100, self.stats[stat] + 15)
        self.hatch_started_at = None
        self.reset_after_evolution()
        if not self.has_dna() and not preserve_dna:
            if entropy is None:
                entropy = int(time.monotonic() * 1000) & 0xFFFFFFFF
            self.roll_dna(entropy)

    @property
    def learning(self):
        # The preserved Pico path does not import desktop codecs unless enabled.
        if self._learning is None:
            from core.learning import LearningState
            self._learning = LearningState()
        return self._learning

    @learning.setter
    def learning(self, value):
        self._learning = value

    def to_dict(self):
        """Serialise for save file."""
        data = {
            "profile": self.profile.encode(),
            "species": self.species,
            "line": self.line,
            "state": self.state,
            "stats": dict(self.stats),
            "inventory": dict(self.inventory),
            "adopted_items": {"version": 1, "counts": dict(self.adopted_inventory),
                              "reward_cursor": self.item_reward_cursor},
            "effort": self.effort,
            "language": self.language,
            "sound_enabled": self.sound_enabled,
            "cold": self.cold,
            "battles_won": self.battles_won,
            "battles_lost": self.battles_lost,
            "battles_this_form": self.battles_this_form,
            "care_mistakes": self.care_mistakes,
            "call_reason": self.call_reason,
            "stage_age_seconds": max(0, int(self.stage_age_seconds)),
            "meals": self.meals,
            "training_sessions": self.training_sessions,
            "menu_train_sessions": getattr(self, "menu_train_sessions", 0),
            "weight": self.weight,
            "nutrition_version": 1,
            "legacy_weight": getattr(self, "legacy_weight", None),
            "hunger_cycle_remainder": self.hunger_cycle_remainder,
            "training_weight_remainder": self.training_weight_remainder,
            "protein_fed_this_cycle": self.protein_fed_this_cycle,
            "dp": self.dp,
            "protein": self.protein,
            "overfeeds": self.overfeeds,
            "overfed_this_cycle": self.overfed_this_cycle,
            "age_seconds": max(0, int(self.age_seconds)),
            "dna": list(self.dna),
            "ev": dict(self.ev),
            "techniques": self.techniques.to_dict(),
            "exploration": self.exploration.to_dict(),
            "sleep": self.sleep.to_dict(),
        }
        if self._learning is not None:
            data["learning"] = self._learning.encode()
        return data

    def load_from_dict(self, d):
        profile = PetProfile.decode(d.get("profile", ""))
        learning = None
        if "learning" in d:
            from core.learning import LearningState
            learning = LearningState.decode(d["learning"])
        from core.adopted_items import load_stock
        self.adopted_inventory, self.item_reward_cursor = load_stock(
            d.get('adopted_items'), missing='adopted_items' not in d)
        self.techniques = TechniqueProgress(d.get("techniques"), d.get("species", self.species))
        self.exploration = Exploration(d.get("exploration"))
        self.sleep = SleepRoutine(d.get("sleep"))
        self.profile = profile
        self._learning = learning
        self.cold = d.get("cold",False) is True
        self.species = d.get("species", self.species)
        self.line = d.get("line", self.line)
        self.state = d.get("state", STATE_LIVE)  # backward compat: if no state, assume live
        self.stats = dict(d.get("stats", self.stats))
        loaded = dict(d.get("inventory", self.inventory))
        self.inventory = dict(DEFAULT_STOCK)
        for key in self.inventory:
            if key in loaded:
                try:
                    self.inventory[key] = max(0, min(ITEM_BY_ID[key]["stack_max"] or 99, int(loaded[key])))
                except (TypeError, ValueError, OverflowError):
                    self.inventory[key] = 0
        self.effort = int(d.get("effort", self.effort))
        self.language = d.get("language", self.language)
        self.sound_enabled = d.get("sound_enabled", self.sound_enabled)
        self.battles_won = d.get("battles_won", 0)
        self.battles_lost = d.get("battles_lost", 0)
        self.battles_this_form = d.get("battles_this_form", 0)
        self.care_mistakes = d.get("care_mistakes", 0)
        self.call_reason = d.get("call_reason")
        self.stage_age_seconds = max(0, int(d.get("stage_age_seconds", 0)))
        self.meals = d.get("meals", 0)
        self.training_sessions = d.get("training_sessions", 0)
        self.menu_train_sessions = d.get("menu_train_sessions", 0)
        self.weight = max(1, min(99, int(d.get("weight", 5))))
        nutrition_version = int(d.get("nutrition_version", 0))
        self.legacy_weight = d.get("legacy_weight")
        if nutrition_version < 1:
            self.legacy_weight = self.weight
            self.weight = migrate_legacy_weight(self.species, self.weight)
        self.hunger_cycle_remainder = max(0, min(19, int(d.get("hunger_cycle_remainder", 0))))
        self.training_weight_remainder = max(0, min(3, int(d.get("training_weight_remainder", 0))))
        self.protein_fed_this_cycle = bool(d.get("protein_fed_this_cycle", False))
        self.dp = d.get("dp", 0)
        self.protein = d.get("protein", 0)
        self.overfeeds = int(d.get("overfeeds", 0))
        self.overfed_this_cycle = bool(d.get("overfed_this_cycle", False))
        age = max(0, int(d.get("age_seconds", 0)))
        self.born_at = time.monotonic() - age
        loaded_dna = d.get("dna") or [0, 0, 0, 0]
        self.restore_dna(loaded_dna)
        self.restore_ev(d.get("ev") or {})
        if not self.has_dna() and self.state != STATE_EGG and self.species != "egg":
            species_id = SPECIES_ID.get(self.species, 0)
            self.roll_dna((age * 2654435761 + species_id + int(self.battles_won) * 17) & 0xFFFFFFFF)
        # If we loaded as an egg, restart the hatch timer
        if self.state == STATE_EGG:
            self.hatch_started_at = time.monotonic()
