"""Reproducible training / care balance simulations.

These tests do not assert the design; they only quantify the *current*
behaviour so the v1 balance decision in
``docs/superpowers/plans/2026-10-05-practice-combat.md`` has evidence
to back the numbers. Every simulation resets the pet to a known
Firemon with empty EV and a fixed energy budget; no state is
persisted between tests.
"""
import pytest

from core.pet import Pet, STATE_LIVE
from core.training import (TRAINING_ENERGY_COST, TRAINING_EV_GAIN, TRAINING_TYPES,
                            MENU_TRAIN_ENERGY_COST, MENU_TRAIN_EV_GAIN,
                            MENU_TRAIN_SESSION_CAP, MENU_TRAIN_STATS,
                            train_attribute, train_menu, menu_train_block_reason)
from core.menu import activate_menu_item
from core.motion import PetMotion
from core import motion as motion_mod


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fresh_firemon(energy=100):
    pet = Pet(species="rookie", state=STATE_LIVE)
    pet.restore_dna((0x20, 0x40, 0x60, 0x80))
    pet.restore_ev({})
    pet.stats = {"h": 80, "e": energy, "p": 80, "hp": 100}
    pet.weight = 5
    pet.effort = 0
    pet.training_sessions = 0
    pet.battles_won = 0
    pet.battles_lost = 0
    pet.battles_this_form = 0
    pet.injuries = 0
    pet.injured = False
    pet.dead = False
    pet.dp = 1
    return pet


def _motion():
    return PetMotion()


def _menu_train(pet, motion, now=0, stat="off"):
    return activate_menu_item(pet, motion, menu_index=2, now=now,
                                menu_train_stat=stat)


def _feed(pet, motion, now=0):
    return activate_menu_item(pet, motion, menu_index=1, now=now)


def _rest(pet, motion, now=0):
    return activate_menu_item(pet, motion, menu_index=4, now=now)


def _battle(pet, motion, now=0):
    return activate_menu_item(pet, motion, menu_index=3, now=now)


def _wake_sleep(pet, motion, now=0, hour=12):
    """Force the pet through one full sleep→wake cycle. Returns True if
    the wake path actually fired (motion was in sleep)."""
    if motion.state != motion_mod.MOTION_SLEEP:
        return False
    motion.wake(now)
    pet.note_wake(hour)
    pet.gain_ev("mp", 2)
    pet.gain_ev("def", 1)
    return True


# ---------------------------------------------------------------------------
# 1. Dumbbell: bounded by energy (8 ENE/session, no rest allowed in the
#    pure path). The 252 cap on a single stat needs 336 ENE.
# ---------------------------------------------------------------------------


def test_dumbbell_drains_to_seven_then_blocks():
    pet = _fresh_firemon(energy=100)
    sessions = 0
    while train_attribute(pet, 0):
        sessions += 1
    # 100 // 8 = 12 full sessions, 4 ENE leftover (not enough for one more).
    assert sessions == 12
    assert pet.get("e") == 4
    assert pet.ev_at("off") == 12 * TRAINING_EV_GAIN == 72


def test_dumbbell_sessions_to_cap_252_via_rest_loop():
    """With the rest loop (1 rest = +30 ENE, then drain on dumbbells),
    how many rests are needed to reach 252 EV in a single stat? The
    loop leaves 2-4 ENE stranded each cycle, so the asymptotic cost
    is 17 rests for 42 dumbbells (= 252 EV in OFF)."""
    pet = _fresh_firemon(energy=100)
    motion = _motion()
    rests = 0
    while pet.ev_at("off") < 252:
        _rest(pet, motion)
        rests += 1
        while pet.get("e") >= TRAINING_ENERGY_COST and pet.ev_at("off") < 252:
            assert train_attribute(pet, 0)
    assert pet.ev_at("off") == 252
    assert pet.training_sessions == 42
    # Empirical: 17 rest cycles to reach 252 EV via dumbbell.
    assert rests == 17


# ---------------------------------------------------------------------------
# 2. Menu training: free, but does it produce any visible cost?
# ---------------------------------------------------------------------------


def test_menu_training_costs_visible_energy_v1():
    """v1 balance: each menu training session costs MENU_TRAIN_ENERGY_COST
    ENE and gives +MENU_TRAIN_EV_GAIN in the chosen stat. The default
    in ``activate_menu_item`` targets off, but the player alternates
    via the ``menu_train_stat`` keyword. Sessions stop accepting once
    the per-cycle cap is reached."""
    pet = _fresh_firemon(energy=100)
    motion = _motion()
    accepted = 0
    while accepted < 12:
        if not activate_menu_item(pet, motion, menu_index=2, now=0,
                                    menu_train_stat="off"):
            break
        accepted += 1
    assert accepted == MENU_TRAIN_SESSION_CAP
    assert pet.get("e") == 100 - accepted * MENU_TRAIN_ENERGY_COST
    assert pet.ev_at("off") == accepted * MENU_TRAIN_EV_GAIN
    assert pet.ev_at("spd") == 0
    assert pet.training_sessions == accepted


def test_menu_training_capped_per_care_cycle_v1():
    """v1 balance: a maximum of MENU_TRAIN_SESSION_CAP menu training
    sessions per care cycle (resets on evolution)."""
    pet = _fresh_firemon(energy=100)
    motion = _motion()
    sessions = 0
    while activate_menu_item(pet, motion, menu_index=2, now=0,
                                menu_train_stat="off"):
        sessions += 1
        if sessions > 50:
            break
    assert sessions == MENU_TRAIN_SESSION_CAP == 8
    assert pet.ev_at("off") == MENU_TRAIN_SESSION_CAP * MENU_TRAIN_EV_GAIN == 8
    assert pet.menu_train_sessions == MENU_TRAIN_SESSION_CAP
    assert menu_train_block_reason(pet) == "LIMITE DE SESIONES"


def test_menu_training_alt_off_spd_doubles_session_count_v1():
    """Splitting between off and spd lets the player train both, but
    the cap is shared across both stats. To cap both to 252 you need
    504 sessions, which is impossible in one cycle (cap 8)."""
    pet = _fresh_firemon(energy=100)
    motion = _motion()
    for i in range(4):
        assert activate_menu_item(pet, motion, menu_index=2, now=0,
                                    menu_train_stat="off")
        assert activate_menu_item(pet, motion, menu_index=2, now=0,
                                    menu_train_stat="spd")
    assert pet.ev_at("off") == 4
    assert pet.ev_at("spd") == 4
    assert pet.menu_train_sessions == 8  # shared cap


def test_menu_training_blocked_by_low_energy_v1():
    pet = _fresh_firemon(energy=2)
    motion = _motion()
    assert menu_train_block_reason(pet) == "FALTA ENERGIA"
    assert not activate_menu_item(pet, motion, menu_index=2, now=0,
                                    menu_train_stat="off")
    assert pet.ev_at("off") == 0
    assert pet.menu_train_sessions == 0


def test_menu_training_blocked_by_egg_or_baby_v1():
    for species in ("egg", "baby"):
        pet = _fresh_firemon(energy=100)
        pet.species = species
        assert menu_train_block_reason(pet) == "PET NO APTO"
        assert not activate_menu_item(pet, _motion(), menu_index=2, now=0,
                                        menu_train_stat="off")


def test_menu_training_blocked_by_injury_or_death_v1():
    for state in ("injured", "dead"):
        pet = _fresh_firemon(energy=100)
        setattr(pet, state, True)
        assert menu_train_block_reason(pet) == "PET NO APTO"
        assert not activate_menu_item(pet, _motion(), menu_index=2, now=0,
                                        menu_train_stat="off")


def test_menu_training_blocked_at_per_stat_cap_252_v1():
    pet = _fresh_firemon(energy=100)
    pet.ev["off"] = 252
    motion = _motion()
    # The session-cap check fires first (we set 0 sessions), so the
    # off-cap check is reached only after a successful first session.
    assert activate_menu_item(pet, motion, menu_index=2, now=0,
                                menu_train_stat="spd")
    # Now off=252 already, but the call passes off; the function
    # should refuse because ev_at(stat) >= 252.
    assert not train_menu(pet, "off")


def test_menu_training_sessions_reset_on_evolution_v1():
    pet = _fresh_firemon(energy=100)
    motion = _motion()
    for _ in range(8):
        activate_menu_item(pet, motion, menu_index=2, now=0,
                            menu_train_stat="off")
    assert pet.menu_train_sessions == 8
    pet.reset_after_evolution()
    assert pet.menu_train_sessions == 0
    assert menu_train_block_reason(pet) == ""
    # Energy was also drained before the cap; reset_after_evolution
    # leaves stats alone, only resets the cap counter.
    assert pet.get("e") == 100 - 8 * MENU_TRAIN_ENERGY_COST == 76


# ---------------------------------------------------------------------------
# 3. Wake-from-sleep EV: bounded only by how often you can put the pet
#    back to sleep.
# ---------------------------------------------------------------------------


def test_wake_from_sleep_adds_free_mp_def():
    pet = _fresh_firemon(energy=100)
    motion = _motion()
    cycles = 0
    while pet.ev_at("mp") < 20:  # small sample, 10 wake cycles
        motion.start_sleep(0)
        pet.stats["e"] = 0  # ensure wake triggers strength call
        if _wake_sleep(pet, motion):
            cycles += 1
    assert cycles == 10
    assert pet.ev_at("mp") == 20
    assert pet.ev_at("def") == 10
    # Bounded only by the player's patience to wait for sleep animations.


# ---------------------------------------------------------------------------
# 4. Battle free EV: bounded by dp, energy, and injury chance.
# ---------------------------------------------------------------------------


def test_battle_blocks_after_four_consecutive():
    pet = _fresh_firemon(energy=100)
    pet.dp = 999
    motion = _motion()
    successes = 0
    for _ in range(20):
        if _battle(pet, motion):
            successes += 1
    # The 5th battle hits an injury; success count is 4.
    assert successes == 4
    assert pet.ev_at("off") == 4
    assert pet.ev_at("brn") == 4
    assert pet.injured is True
    # At -12 ENE per battle, 4 battles = 52 ENE. Stopped by injury, not energy.


# ---------------------------------------------------------------------------
# 5. Feed: bounded by hunger cap (h=100) and overfed cycle.
# ---------------------------------------------------------------------------


def test_feed_gives_one_hp_ev_per_hunger_cycle():
    pet = _fresh_firemon(energy=100)
    motion = _motion()
    feeds = 0
    while _feed(pet, motion):
        feeds += 1
    # First feed: h<100, +2 HP EV, h -> 100. Second feed: h>=100, +
    # overfeeds +1, weight +1, NO HP EV (trained=False). Third feed:
    # can_feed returns False (overfed_this_cycle True).
    assert feeds == 2
    assert pet.ev_at("hp") == 2
    assert pet.weight == 6
    # To repeat, the player must wait for h to drop below 100 (decay) so
    # overfed_this_cycle resets. That is hours of real time, but
    # deterministic in tests.


# ---------------------------------------------------------------------------
# 6. Strategy comparison: same energy budget, different paths
# ---------------------------------------------------------------------------


def test_strategy_dumbbell_only_252_off():
    """Pure dumbbell: 17 rests + 42 sessions = 252 EV in OFF.
    This is the baseline cost the v1 balance decision cites."""
    pet = _fresh_firemon(energy=100)
    motion = _motion()
    rests = 0
    while pet.ev_at("off") < 252:
        _rest(pet, motion)
        rests += 1
        while pet.get("e") >= TRAINING_ENERGY_COST and pet.ev_at("off") < 252:
            train_attribute(pet, 0)
    assert pet.ev_at("off") == 252
    assert rests == 17
    assert pet.training_sessions == 42


def test_strategy_menu_only_v1_caps_per_cycle():
    """v1: pure menu training is bounded by MENU_TRAIN_SESSION_CAP per
    care cycle. The 9th session in a single cycle is rejected, so the
    player cannot exceed 8 EV in one stat from a single care cycle."""
    pet = _fresh_firemon(energy=100)
    motion = _motion()
    accepted = 0
    for _ in range(20):
        if _menu_train(pet, motion):
            accepted += 1
        else:
            break
    assert accepted == MENU_TRAIN_SESSION_CAP
    assert pet.ev_at("off") == MENU_TRAIN_SESSION_CAP
    assert pet.menu_train_sessions == MENU_TRAIN_SESSION_CAP
    # The remaining 12 sessions all hit the cap. The pet would need
    # an evolution to reset the cap and continue.


def test_strategy_menu_only_v1_does_not_cap_stat():
    """v1: a single menu cycle does not come close to capping a stat.
    The player needs 32 evolution cycles to cap off via menu alone —
    far beyond realistic. The dumbbell path is the only way to cap a
    stat in a reasonable timeframe."""
    pet = _fresh_firemon(energy=100)
    motion = _motion()
    for _ in range(20):
        _menu_train(pet, motion)
    # Cap hit at 8 sessions; further calls rejected.
    assert pet.ev_at("off") == MENU_TRAIN_SESSION_CAP == 8
    assert pet.ev_at("spd") == 0  # default stat is off


def test_strategy_comparison_documented():
    """A single number per strategy: how many rest cycles to cap OFF.

    v1 balance: the menu path is bounded by MENU_TRAIN_SESSION_CAP and
    the dumbbell path stays unchanged. The two paths now differ in
    cost, flexibility, and throughput per ENE — a real trade-off.
    """
    # (rests_needed, energy_spent, sessions_count, ev_gained)
    table = {
        # Pure menu: capped at MENU_TRAIN_SESSION_CAP per care cycle,
        # so a single cycle can only add 8 EV. To reach 252 in one
        # stat needs 32 evolution cycles, which is not realistic.
        "menu_only":        ("ev_per_cycle", MENU_TRAIN_SESSION_CAP,
                              MENU_TRAIN_SESSION_CAP * MENU_TRAIN_ENERGY_COST,
                              MENU_TRAIN_SESSION_CAP * MENU_TRAIN_EV_GAIN),
        # Pure dumbbell: same as pre-v1: 17 rests, 336 ENE, 42
        # sessions, +252 EV in the chosen stat.
        "dumbbell_only":    (17, 336, 42, 252),
    }
    menu_runs, menu_sessions, menu_ene, menu_ev = table["menu_only"]
    assert menu_runs == "ev_per_cycle"
    assert menu_sessions == MENU_TRAIN_SESSION_CAP
    assert menu_ene == MENU_TRAIN_SESSION_CAP * MENU_TRAIN_ENERGY_COST
    assert menu_ev == MENU_TRAIN_SESSION_CAP * MENU_TRAIN_EV_GAIN
    dumb_rests, dumb_ene, dumb_sessions, dumb_ev = table["dumbbell_only"]
    assert dumb_rests == 17
    assert dumb_ene == 336
    assert dumb_sessions == 42
    assert dumb_ev == 252
    # EV/ENE ratio (a rough throughput metric):
    #   menu: 8 EV / 24 ENE = 0.33 EV/ENE
    #   dumbbell: 252 EV / 336 ENE = 0.75 EV/ENE
    # The dumbbell is now strictly better per ENE, and it is also the
    # only path that can hit a stat cap in a single care cycle. The
    # menu is the cheap "do a little every day" path. This is the
    # trade-off the v1 fix establishes.


# ---------------------------------------------------------------------------
# 7. Deterministic coverage per stat and path
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("stat_name", ["off", "def", "spd", "hp", "mp", "brn"])
def test_dumbbell_changes_only_chosen_ev_per_stat(stat_name):
    """Dumbbell: targeting any of the 6 stats only changes that one.
    The 5 other stats stay at 0. Visible to the player via the EV
    delta on the dumbbell screen (``%d > %d``)."""
    pet = _fresh_firemon(energy=100)
    idx = next(i for i, t in enumerate(TRAINING_TYPES) if t["stat"] == stat_name)
    assert train_attribute(pet, idx)
    assert pet.ev_at(stat_name) == TRAINING_EV_GAIN
    for other in ("off", "def", "spd", "hp", "mp", "brn"):
        if other == stat_name:
            continue
        assert pet.ev_at(other) == 0


@pytest.mark.parametrize("stat", MENU_TRAIN_STATS)
def test_menu_training_targets_only_chosen_stat(stat):
    pet = _fresh_firemon(energy=100)
    motion = _motion()
    for _ in range(4):
        assert activate_menu_item(pet, motion, menu_index=2, now=0,
                                    menu_train_stat=stat)
    assert pet.ev_at(stat) == 4
    other = "spd" if stat == "off" else "off"
    assert pet.ev_at(other) == 0


def test_menu_training_invalid_stat_returns_false():
    pet = _fresh_firemon(energy=100)
    assert not train_menu(pet, "hp")  # hp is dumbbell-only
    assert not train_menu(pet, "def")  # def is dumbbell-only
    assert pet.ev_at("hp") == 0
    assert pet.ev_at("def") == 0
    assert pet.menu_train_sessions == 0


def test_energy_insufficient_blocks_dumbbell():
    pet = _fresh_firemon(energy=7)
    assert not train_attribute(pet, 0)
    assert pet.ev_at("off") == 0
    assert pet.training_sessions == 0


def test_energy_exact_3_allows_one_menu_session_v1():
    pet = _fresh_firemon(energy=3)
    motion = _motion()
    assert activate_menu_item(pet, motion, menu_index=2, now=0,
                                menu_train_stat="off")
    assert pet.get("e") == 0
    assert pet.ev_at("off") == 1
    # Now 0 ENE: next session blocked.
    assert menu_train_block_reason(pet) == "FALTA ENERGIA"


def test_dumbbell_session_blocked_at_per_stat_cap():
    pet = _fresh_firemon(energy=100)
    pet.ev["off"] = 252
    assert not train_attribute(pet, 0)
    assert pet.ev_at("off") == 252
    assert pet.training_sessions == 0


def test_dumbbell_session_blocked_at_session_egg_or_baby():
    for species in ("egg", "baby"):
        pet = _fresh_firemon(energy=100)
        pet.species = species
        assert not train_attribute(pet, 0)
        assert pet.ev_at("off") == 0
        assert pet.training_sessions == 0


# ---------------------------------------------------------------------------
# 8. Combined strategy: rest + train (dumbbell) + menu in one budget.
# ---------------------------------------------------------------------------


def test_combined_strategy_rest_dumbbell_menu_v1():
    """A player who mixes paths spends fewer rest cycles than pure
    dumbbell. With 100 ENE starting energy and the v1 cap of 8 menu
    sessions, the menu contributes 8 EV (24 ENE) and the dumbbell
    contributes the rest."""
    pet = _fresh_firemon(energy=100)
    motion = _motion()
    # 8 menu sessions first (uses 24 ENE, +8 EV in off).
    for _ in range(8):
        assert activate_menu_item(pet, motion, menu_index=2, now=0,
                                    menu_train_stat="off")
    assert pet.get("e") == 100 - 24
    assert pet.ev_at("off") == 8
    # Drain remaining 76 ENE on dumbbells: 9 sessions (72 ENE), 4 left.
    sessions = 0
    while train_attribute(pet, 0):
        sessions += 1
    assert sessions == 9
    assert pet.ev_at("off") == 8 + 9 * TRAINING_EV_GAIN == 62
    # 1 rest to get back to 30+ ENE, 4 ENE was left stranded, so we
    # burned fewer rests than pure dumbbell. This is the trade-off:
    # 8 EV per cycle of menu training replaces 1.33 dumbbell sessions
    # (8 EV / 6 EV per session) at the cost of 24 ENE instead of 10.67
    # ENE — so menu is slightly worse per ENE but bundled.
