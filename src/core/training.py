"""Targeted Firemon training prototype; integer EV gains preserve hatch DNA."""
from core.dna import combat_stat

TRAINING_ENERGY_COST = 8
TRAINING_EV_GAIN = 6
# Menu training (the cheap, focused, daily-capped path). The menu
# trains one of two stats per session at half the EV rate of the
# dumbbell, costs a visible fraction of an energy point, and is
# capped per care cycle so a player cannot farm it infinitely.
MENU_TRAIN_ENERGY_COST = 3
MENU_TRAIN_EV_GAIN = 1
MENU_TRAIN_SESSION_CAP = 8
MENU_TRAIN_STATS = ("off", "spd")
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


# ---------------------------------------------------------------------------
# Menu training: focused, capped, low-cost, visible energy spend.
# Players pick which of the two eligible stats (off / spd) the session
# targets. EV gain is 1 per session, the energy cost is 3 ENE, and a
# per-care-cycle cap of MENU_TRAIN_SESSION_CAP prevents infinite farming.
# ---------------------------------------------------------------------------


def menu_train_block_reason(pet):
    """Return a non-empty reason string if a menu training session is
    blocked, else an empty string. The block list mirrors the dumbbell
    plus the new cap and the per-stat cap of 252."""
    if pet.species == "egg" or pet.species == "baby":
        return "PET NO APTO"
    if pet.dead or pet.injured or getattr(pet, "cold", False):
        return "PET NO APTO"
    if getattr(pet, "menu_train_sessions", 0) >= MENU_TRAIN_SESSION_CAP:
        return "LIMITE DE SESIONES"
    if pet.get("e") < MENU_TRAIN_ENERGY_COST:
        return "FALTA ENERGIA"
    return ""


def train_menu(pet, stat):
    """Apply a menu training session. ``stat`` must be in
    ``MENU_TRAIN_STATS``. Returns True if the session was applied."""
    if stat not in MENU_TRAIN_STATS:
        return False
    if menu_train_block_reason(pet):
        return False
    if pet.ev_at(stat) >= 252:
        return False
    pet.gain_ev(stat, MENU_TRAIN_EV_GAIN)
    pet.stats["e"] = max(0, pet.get("e") - MENU_TRAIN_ENERGY_COST)
    # NOTE: pet.stats["p"] (felicidad) is NOT touched here. The menu
    # training menu_index runs ``pet.apply_action(ACTION_EFFECTS[2])``
    # before reaching train_menu, which already applies +15 felicidad
    # (ACTION_EFFECTS[2] = {"p": +15}). Adding a second +1 here would
    # double-count and push happiness past the legacy contract.
    pet.effort = min(100, getattr(pet, "effort", 0) + 2)
    pet.training_sessions = getattr(pet, "training_sessions", 0) + 1
    pet.menu_train_sessions = getattr(pet, "menu_train_sessions", 0) + 1
    return True


# ---------------------------------------------------------------------------
# Batched training session (2026-10-07).
# The dumbbell path now supports a draft-then-confirm flow: a session
# accumulates reps in memory, reserves energy without debiting, and only
# applies the batched EV + cost + secondary effects when the player
# explicitly finalises. The pre-v1 single-rep ``train_attribute`` is
# kept unchanged for backward compatibility with the dumbbell renderer's
# previews; the batched path is the canonical one for the simulator UI.
# ---------------------------------------------------------------------------


def training_index_for(stat):
    """Return the TRAINING_TYPES index for a stat name. Raises
    ValueError if the stat is not part of the dumbbell set."""
    for i, item in enumerate(TRAINING_TYPES):
        if item["stat"] == stat:
            return i
    raise ValueError("unknown training stat: %r" % stat)


def batch_block_reason(pet, stat):
    """Return the reason a batched training session for ``stat`` is
    blocked (empty string if eligible). Mirrors ``training_block_reason``
    but for a stat name instead of a TRAINING_TYPES index, and is the
    single source of truth for state A and state B of the batched UI."""
    if stat not in (t["stat"] for t in TRAINING_TYPES):
        return "TIPO INVALIDO"
    if not pet.is_live or pet.species != "rookie" or pet.dead or pet.injured \
            or getattr(pet, "cold", False):
        return "PET NO APTO"
    if pet.ev_at(stat) >= 252:
        return "EV AL MAXIMO"
    if pet.get("e") < TRAINING_ENERGY_COST:
        return "FALTA ENERGIA"
    return ""


def batch_max_reps(pet, stat):
    """Return the maximum reps the player can queue in a single batch
    for ``stat``. The bound is the minimum of:
      * energy budget: floor(energy / TRAINING_ENERGY_COST)
      * EV headroom: ceil((252 - current_ev) / TRAINING_EV_GAIN) but
        never zero when the stat is below 252
      * eligibility (PET NO APTO / EV AL MAXIMO returns 0)

    A pet that is already at 252 EV in the stat returns (0, reason).
    A pet that is below 252 EV but has no energy returns (0, "FALTA
    ENERGIA"). The result is deterministic; tests pin both branches.
    """
    reason = batch_block_reason(pet, stat)
    if reason:
        return 0, reason
    energy_reps = pet.get("e") // TRAINING_ENERGY_COST
    headroom = 252 - pet.ev_at(stat)
    # Use ceiling so the partial last rep is always included: at ev=248
    # we can still queue 1 rep (gain 4 EV, cost 8 ENE).
    import math
    ev_reps = math.ceil(headroom / TRAINING_EV_GAIN) if headroom > 0 else 0
    reps = min(energy_reps, ev_reps)
    if reps <= 0:
        # Distinguish the two zero-rep reasons for the UI.
        if energy_reps <= 0:
            return 0, "FALTA ENERGIA"
        return 0, "EV AL MAXIMO"
    return int(reps), ""


def batch_plan_one_rep(pet, stat):
    """Return a description of the next valid rep without mutating the
    pet. The dict has:
        * can: True if the rep is doable
        * ev_added: how much EV the rep would add (may be partial)
        * energy_cost: the ENE charged
        * secondary: the secondary effects (effort/happiness/weight)
        * reason: empty when can, else the block reason
    """
    reason = batch_block_reason(pet, stat)
    if reason:
        return {"can": False, "ev_added": 0, "energy_cost": 0,
                "secondary": {}, "reason": reason}
    if pet.get("e") < TRAINING_ENERGY_COST:
        return {"can": False, "ev_added": 0, "energy_cost": 0,
                "secondary": {}, "reason": "FALTA ENERGIA"}
    headroom = 252 - pet.ev_at(stat)
    ev_added = min(TRAINING_EV_GAIN, headroom)
    return {"can": True, "ev_added": int(ev_added),
            "energy_cost": TRAINING_ENERGY_COST,
            "secondary": {
                "happiness": 3,
                "effort": 8,
                "weight": -1,
                "training_sessions": 1,
            },
            "reason": ""}


def batch_projected_stat(pet, stat, ev_delta):
    """Return the combat_stat value (or HP/MP pool) after adding
    ``ev_delta`` EV to the stat, without mutating the pet. HP/MP use
    the project's pool conversions (40 + hp*2, 10 + mp)."""
    projected_ev = dict(pet.ev)
    projected_ev[stat] = min(252, pet.ev_at(stat) + ev_delta)
    value = combat_stat(pet.dna, projected_ev, stat)
    if stat == "hp":
        return 40 + value * 2
    if stat == "mp":
        return 10 + value
    return value


def batch_projected_value(pet, stat, ev_delta):
    """Convenience wrapper returning (current, projected) for the
    stat-pool view used by the renderer."""
    current = combat_stat(pet.dna, pet.ev, stat)
    if stat == "hp":
        current = 40 + current * 2
    elif stat == "mp":
        current = 10 + current
    projected_ev = dict(pet.ev)
    projected_ev[stat] = min(252, pet.ev_at(stat) + ev_delta)
    value = combat_stat(pet.dna, projected_ev, stat)
    if stat == "hp":
        value = 40 + value * 2
    elif stat == "mp":
        value = 10 + value
    return current, value


def batch_apply(pet, stat, reps):
    """Apply ``reps`` training sessions to ``pet`` in one call. The
    cost/EV/secondary effects are computed once and charged once. The
    last rep may be partial (less than TRAINING_EV_GAIN if the stat
    would exceed 252); the energy cost and secondary effects are NOT
    discounted on the partial rep. The function returns a dict with
    the totals actually applied. The function does NOT save; the
    caller is responsible for the atomic save and rollback on
    failure."""
    if reps <= 0:
        return {"reps": 0, "ev_added": 0, "energy_charged": 0,
                "effort_added": 0, "happiness_added": 0, "weight_delta": 0,
                "training_sessions_added": 0}
    plan = batch_plan_one_rep(pet, stat)
    if not plan["can"]:
        return {"reps": 0, "ev_added": 0, "energy_charged": 0,
                "effort_added": 0, "happiness_added": 0, "weight_delta": 0,
                "training_sessions_added": 0}
    if reps > (pet.get("e") // TRAINING_ENERGY_COST):
        reps = pet.get("e") // TRAINING_ENERGY_COST
    ev_added = 0
    for _ in range(int(reps)):
        headroom = 252 - pet.ev_at(stat)
        gain = min(TRAINING_EV_GAIN, headroom)
        if gain <= 0:
            break
        pet.gain_ev(stat, gain)
        ev_added += gain
    energy_charged = int(reps) * TRAINING_ENERGY_COST
    pet.stats["e"] = max(0, pet.get("e") - energy_charged)
    happiness_added = int(reps) * plan["secondary"]["happiness"]
    effort_added = int(reps) * plan["secondary"]["effort"]
    weight_delta = int(reps) * plan["secondary"]["weight"]
    pet.stats["p"] = min(100, pet.stats["p"] + happiness_added)
    pet.effort = min(100, getattr(pet, "effort", 0) + effort_added)
    pet.weight = max(0, pet.weight + weight_delta)
    pet.training_sessions = getattr(pet, "training_sessions", 0) + int(reps)
    return {"reps": int(reps), "ev_added": ev_added,
            "energy_charged": energy_charged,
            "effort_added": effort_added,
            "happiness_added": happiness_added,
            "weight_delta": weight_delta,
            "training_sessions_added": int(reps)}


def batch_commit(pet, stat, reps, save):
    """Atomic transaction: apply ``reps`` training sessions to ``pet``
    and persist through ``save`` in one step. If the save callback
    returns a falsy value, the pet is restored from a snapshot taken
    before the apply and ``BatchSaveError`` is raised. The caller
    can safely retry by calling ``batch_commit`` again on the same
    pet: the second call observes the rolled-back state.

    The save callback is expected to take a Pet and return a truthy
    value on success. Returns the apply summary dict on success."""
    snapshot = pet.to_dict()
    summary = batch_apply(pet, stat, reps)
    if save(pet):
        return summary
    pet.load_from_dict(snapshot)
    raise BatchSaveError("save failed; pet rolled back from in-memory snapshot")


class BatchSaveError(RuntimeError):
    """Raised by batch_save when the save callback returns falsy. The
    pet is restored to its pre-apply state before the exception
    propagates."""

    def __init__(self, message):
        super().__init__(message)
        self.message = message
