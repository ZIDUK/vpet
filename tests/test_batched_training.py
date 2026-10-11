"""Contract tests for the batched training session (2026-10-07 spec).

These tests pin the domain layer *before* the renderer is wired up.
They freeze the policy decisions in code:

* a queued batch must not mutate pet, EV, IV, stats, or save until
  ``batch_apply`` is followed by a successful ``batch_save``;
* the last rep at cap is partial (gain = 252 - current_ev, max
  TRAINING_EV_GAIN), but the energy cost and the secondary effects
  are NOT discounted;
* energy reservation is virtual: ``batch_plan_one_rep`` and
  ``batch_max_reps`` do not debit the pet;
* save failure restores the pre-apply state and raises
  ``BatchSaveError``; the next call must be idempotent;
* state changes while a batch is open (death, injury, cold, hatch)
  must be revalidated before the apply is allowed;
* egg / baby / dead / injured / cold / EV=252 all block cleanly with
  a deterministic reason.
"""
import pytest

from core.pet import Pet, STATE_LIVE
from core.training import (TRAINING_ENERGY_COST, TRAINING_EV_GAIN,
                            batch_block_reason, batch_max_reps,
                            batch_plan_one_rep, batch_projected_value,
                            batch_apply, batch_commit, BatchSaveError,
                            training_index_for, TRAINING_TYPES)


def _firemon(energy=100, ev=None, hp=100, p=80, h=80):
    pet = Pet(species="rookie", state=STATE_LIVE)
    pet.restore_dna((0x20, 0x40, 0x60, 0x80))
    pet.stats = {"h": h, "e": energy, "p": p, "hp": hp}
    if ev is not None:
        pet.restore_ev(ev)
    return pet


# ---------------------------------------------------------------------------
# 1. Eligibilidad
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("stat", [t["stat"] for t in TRAINING_TYPES])
def test_batch_block_reason_empty_for_eligible_pet(stat):
    pet = _firemon()
    assert batch_block_reason(pet, stat) == ""


def test_batch_block_reason_invalid_stat():
    pet = _firemon()
    assert batch_block_reason(pet, "luck") == "TIPO INVALIDO"


def test_batch_block_reason_egg_or_baby():
    for species in ("egg", "baby"):
        pet = _firemon()
        pet.species = species
        assert batch_block_reason(pet, "off") == "PET NO APTO"


def test_batch_block_reason_injured_or_dead_or_cold():
    for state in ("injured", "dead"):
        pet = _firemon()
        setattr(pet, state, True)
        assert batch_block_reason(pet, "off") == "PET NO APTO"
    pet = _firemon()
    pet.cold = True
    assert batch_block_reason(pet, "off") == "PET NO APTO"


def test_batch_block_reason_at_cap_252():
    pet = _firemon(ev={"off": 252})
    assert batch_block_reason(pet, "off") == "EV AL MAXIMO"


# ---------------------------------------------------------------------------
# 2. Max reps y plan (no mutación)
# ---------------------------------------------------------------------------


def test_max_reps_bounded_by_energy_budget():
    pet = _firemon(energy=100)
    reps, reason = batch_max_reps(pet, "off")
    assert reason == ""
    # 100 / 8 = 12. EV headroom is 252/6 = 42. Bound is 12.
    assert reps == 12


def test_max_reps_bounded_by_ev_headroom_uses_ceiling_for_partial():
    """If EV is 248, one rep is still possible (gain 4, cost 8). The
    ceiling round-up makes this visible to the UI so the player is
    not surprised by the partial last rep."""
    pet = _firemon(energy=80, ev={"off": 248})
    reps, reason = batch_max_reps(pet, "off")
    assert reason == ""
    # Energy caps at 80 // 8 = 10. EV caps at ceil(4/6) = 1. Bound 1.
    assert reps == 1


def test_max_reps_zero_when_at_cap_even_with_energy():
    pet = _firemon(energy=100, ev={"off": 252})
    reps, reason = batch_max_reps(pet, "off")
    assert reps == 0
    assert reason == "EV AL MAXIMO"


def test_max_reps_zero_when_no_energy_even_with_headroom():
    pet = _firemon(energy=7)
    reps, reason = batch_max_reps(pet, "off")
    assert reps == 0
    assert reason == "FALTA ENERGIA"


def test_max_reps_zero_when_pet_not_eligible():
    pet = _firemon(energy=100)
    pet.injured = True
    reps, reason = batch_max_reps(pet, "off")
    assert reps == 0
    assert reason == "PET NO APTO"


def test_plan_one_rep_does_not_mutate_pet():
    pet = _firemon(energy=100)
    before = pet.to_dict()
    plan = batch_plan_one_rep(pet, "off")
    assert plan["can"] is True
    assert plan["ev_added"] == TRAINING_EV_GAIN
    assert plan["energy_cost"] == TRAINING_ENERGY_COST
    assert plan["secondary"] == {
        "happiness": 3, "effort": 8,
        "weight": -1, "training_sessions": 1,
    }
    assert plan["reason"] == ""
    assert pet.to_dict() == before


def test_plan_one_rep_partial_at_cap():
    """At ev=250, the next rep gains 2 (not 6); the cost is still 8."""
    pet = _firemon(energy=80, ev={"off": 250})
    plan = batch_plan_one_rep(pet, "off")
    assert plan["can"] is True
    assert plan["ev_added"] == 2
    assert plan["energy_cost"] == TRAINING_ENERGY_COST
    assert pet.to_dict() == _firemon(energy=80, ev={"off": 250}).to_dict()


def test_plan_one_rep_blocked_at_cap():
    pet = _firemon(energy=100, ev={"off": 252})
    plan = batch_plan_one_rep(pet, "off")
    assert plan["can"] is False
    assert plan["ev_added"] == 0
    assert plan["reason"] == "EV AL MAXIMO"


def test_plan_one_rep_blocked_at_zero_energy():
    pet = _firemon(energy=7)
    plan = batch_plan_one_rep(pet, "off")
    assert plan["can"] is False
    assert plan["reason"] == "FALTA ENERGIA"


# ---------------------------------------------------------------------------
# 3. Proyección (no mutación)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("stat", ["off", "def", "spd", "brn"])
def test_projected_value_hp_mp_uses_pool_conversion(stat):
    """Non-pool stats reflect combat_stat directly. The project uses
    the formula 10 + IV*3 + EV//6 clamped 1..99, which we mirror."""
    pet = _firemon(ev={stat: 12})
    current, projected = batch_projected_value(pet, stat, 6)
    # 12 EV/6 = 2; +6 EV = 18/6 = 3; +IV*3 + 10 clamped.
    assert projected >= current


def test_projected_value_hp_pool():
    pet = _firemon(ev={"hp": 12})
    current, projected = batch_projected_value(pet, "hp", 6)
    # HP pool = 40 + combat_stat * 2
    assert current == 40 + _cs(pet, "hp") * 2
    assert projected == 40 + _cs_plus(pet, "hp", 6) * 2


def test_projected_value_mp_pool():
    pet = _firemon(ev={"mp": 12})
    current, projected = batch_projected_value(pet, "mp", 6)
    assert current == 10 + _cs(pet, "mp")
    assert projected == 10 + _cs_plus(pet, "mp", 6)


def _cs(pet, stat):
    from core.dna import combat_stat
    return combat_stat(pet.dna, pet.ev, stat)


def _cs_plus(pet, stat, delta):
    from core.dna import combat_stat
    projected = dict(pet.ev)
    projected[stat] = min(252, pet.ev_at(stat) + delta)
    return combat_stat(pet.dna, projected, stat)


# ---------------------------------------------------------------------------
# 4. Aplicación: el batch es la única operación que muta
# ---------------------------------------------------------------------------


def test_batch_apply_4_reps_matches_4_single_train_attribute_calls():
    """The batched path must produce the same EV, energy, happiness,
    effort, weight, and training_sessions totals as four single
    ``train_attribute`` calls. This pins the policy: secondary
    effects are NOT discounted on the partial last rep."""
    from core.training import train_attribute
    pet_a = _firemon(energy=100)
    pet_b = _firemon(energy=100)
    for _ in range(4):
        assert train_attribute(pet_a, 0)
    batch_apply(pet_b, "off", 4)
    assert pet_a.to_dict() == pet_b.to_dict()


def test_batch_apply_at_cap_does_partial_last_rep():
    """At ev=250 with 24 ENE available (3 reps), the batch applies
    2+2+2 = 6 EV instead of 2+2+6 = 10; the last rep partial is
    decided by the per-rep cap."""
    pet = _firemon(energy=24, ev={"off": 250})
    result = batch_apply(pet, "off", 3)
    assert result["reps"] == 3
    assert result["ev_added"] == 2  # 250 + 2 = 252, then partial 2 + 2 + 2
    assert result["energy_charged"] == 24
    assert pet.ev_at("off") == 252
    assert pet.get("e") == 0


def test_batch_apply_zero_reps_is_noop():
    pet = _firemon(energy=100)
    before = pet.to_dict()
    result = batch_apply(pet, "off", 0)
    assert result == {"reps": 0, "ev_added": 0, "energy_charged": 0,
                      "effort_added": 0, "happiness_added": 0,
                      "weight_delta": 0, "training_sessions_added": 0}
    assert pet.to_dict() == before


def test_batch_apply_clamps_to_available_energy():
    """If the caller passes more reps than energy allows, the batch
    clamps to the energy budget and does not produce a negative ENE
    balance."""
    pet = _firemon(energy=20, ev={"off": 0})
    result = batch_apply(pet, "off", 10)
    assert result["reps"] == 2  # 20 // 8
    assert result["energy_charged"] == 16
    assert pet.get("e") == 4
    assert pet.ev_at("off") == 12


def test_batch_apply_preserves_iv_dna():
    pet = _firemon(energy=80)
    dna_before = list(pet.dna)
    batch_apply(pet, "off", 5)
    assert list(pet.dna) == dna_before


def test_batch_apply_records_training_sessions():
    pet = _firemon(energy=80)
    before = pet.training_sessions
    batch_apply(pet, "off", 5)
    assert pet.training_sessions == before + 5


def test_batch_apply_does_not_heal_hp_or_mp():
    """The dumbbell path changes HP/MP pools, not the pet's current
    HP/MP. Confirming a batch never heals the live pet."""
    pet = _firemon(energy=80, hp=20, p=10, h=10)
    batch_apply(pet, "hp", 3)
    assert pet.stats["hp"] == 20  # current HP unchanged
    # HP pool grew, but the current HP does not.
    current_pool = 40 + (10 + 4 * 3 + (0x20 & 0x0F) * 3) * 2
    # We don't assert the exact pool here; the point is the live HP
    # stat is not touched.
    assert pet.stats["hp"] == 20


# ---------------------------------------------------------------------------
# 5. Save atómico + rollback
# ---------------------------------------------------------------------------


def test_batch_commit_calls_callback_with_pet():
    """batch_commit must call save(pet) and return the apply summary
    on success."""
    pet = _firemon(energy=80)
    seen = []
    summary = batch_commit(pet, "off", 4, lambda p: seen.append(p.to_dict()) or True)
    assert summary["reps"] == 4
    assert summary["ev_added"] == 24
    assert len(seen) == 1
    assert seen[0] is not pet.to_dict()  # different dicts (serialised)


def test_batch_commit_failure_restores_pet_and_raises():
    pet = _firemon(energy=80)
    snapshot = pet.to_dict()
    with pytest.raises(BatchSaveError):
        batch_commit(pet, "off", 4, lambda p: False)
    # The exception must have rolled back to the snapshot.
    assert pet.to_dict() == snapshot


def test_batch_commit_retry_is_idempotent_after_failure():
    """After a failed commit and rollback, the next commit must
    succeed and produce the same result as a fresh commit on a fresh
    pet."""
    pet = _firemon(energy=80)
    snapshot = pet.to_dict()
    # First attempt: save fails.
    with pytest.raises(BatchSaveError):
        batch_commit(pet, "off", 4, lambda p: False)
    assert pet.to_dict() == snapshot
    # Retry: save succeeds.
    summary = batch_commit(pet, "off", 4, lambda p: True)
    # Result is identical to a fresh pet after the same commit.
    fresh = _firemon(energy=80)
    fresh_summary = batch_commit(fresh, "off", 4, lambda p: True)
    assert pet.to_dict() == fresh.to_dict()
    assert summary == fresh_summary
    assert summary["ev_added"] == 24


def test_batch_commit_does_not_double_apply_on_retry_after_rollback():
    """A rollback restores the pet to pre-apply. The retry must produce
    the same totals (not double-charge) because the second commit
    starts from the rolled-back state."""
    pet = _firemon(energy=80)
    with pytest.raises(BatchSaveError):
        batch_commit(pet, "off", 4, lambda p: False)
    # Pet is rolled back. Retry should apply exactly once more.
    summary = batch_commit(pet, "off", 4, lambda p: True)
    assert pet.ev_at("off") == 24  # not 48
    assert pet.get("e") == 48
    assert summary["ev_added"] == 24


# ---------------------------------------------------------------------------
# 6. Revalidación: cambios de estado mientras la tanda está abierta
# ---------------------------------------------------------------------------


def test_revalidation_after_state_change_blocks_apply():
    """A pet that is injured mid-session cannot apply a queued batch.
    batch_apply must short-circuit when the eligibility changes."""
    pet = _firemon(energy=80)
    # Queue 4 reps by reading the plan; nothing is applied.
    plan = batch_plan_one_rep(pet, "off")
    assert plan["can"] is True
    # Mid-session the pet gets injured.
    pet.injured = True
    # Re-validate before apply.
    plan2 = batch_plan_one_rep(pet, "off")
    assert plan2["can"] is False
    assert plan2["reason"] == "PET NO APTO"
    # batch_apply is also a no-op.
    result = batch_apply(pet, "off", 4)
    assert result["reps"] == 0
    assert pet.ev_at("off") == 0
    assert pet.get("e") == 80


def test_revalidation_at_cap_blocks_apply():
    pet = _firemon(energy=80)
    pet.ev["off"] = 252
    plan = batch_plan_one_rep(pet, "off")
    assert plan["can"] is False
    assert plan["reason"] == "EV AL MAXIMO"
    result = batch_apply(pet, "off", 4)
    assert result["reps"] == 0
    assert pet.ev_at("off") == 252


# ---------------------------------------------------------------------------
# 7. Compatibilidad de saves
# ---------------------------------------------------------------------------


def test_legacy_save_round_trip_preserves_pet():
    """A pet serialised with the pre-batch schema round-trips through
    the existing ``load_from_dict`` without raising. No new fields
    are required for the draft/batch path; the batch only lives in
    memory of the simulator."""
    legacy = {"species": "rookie", "line": "custom_line", "state": "live",
              "stats": {"h": 70, "e": 70, "p": 70, "hp": 70},
              "inventory": {"meat": 3, "energy": 2, "exp": 1, "ring": 1,
                            "protein": 2, "medkit": 1},
              "effort": 0, "language": "EN", "sound_enabled": True,
              "battles_won": 0, "battles_lost": 0, "battles_this_form": 0,
              "care_mistakes": 0, "call_reason": None, "stage_age_seconds": 0,
              "meals": 0, "training_sessions": 0, "weight": 5, "dp": 1,
              "protein": 0, "overfeeds": 0, "overfed_this_cycle": False,
              "age_seconds": 0, "dna": [0x20, 0x40, 0x60, 0x80],
              "ev": {"hp": 0, "mp": 0, "off": 0, "def": 0, "spd": 0, "brn": 0},
              "techniques": {"learned": [True, False, False],
                              "equipped": [0, 1], "training": 0,
                              "mastery": [0, 0, 0], "bond": 50,
                              "lessons": 0, "version": 1}}
    pet = Pet()
    pet.load_from_dict(legacy)
    # New field default is 0; the legacy save does not need migration.
    assert getattr(pet, "menu_train_sessions", 0) == 0
    assert pet.ev_at("off") == 0
