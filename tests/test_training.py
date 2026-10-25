import pytest

from core.pet import Pet
from core.training import TRAINING_TYPES, train_attribute, training_values, training_block_reason
from scripts.practice_session import PracticeSession
from scripts.training_session import TrainingSession


def firemon():
    pet = Pet()
    pet.complete_hatch("rookie", entropy=12345)
    return pet


@pytest.mark.parametrize("index", range(6))
def test_targeted_training_changes_only_chosen_ev_and_preserves_dna(index):
    pet = firemon()
    dna, ev, energy = list(pet.dna), dict(pet.ev), pet.get("e")
    before, after = training_values(pet, index)
    stat = TRAINING_TYPES[index]["stat"]
    assert train_attribute(pet, index)
    ev[stat] += 6
    assert pet.ev == ev and pet.dna == dna
    assert training_values(pet, index)[0] == after
    from core.growth_pilot import point
    delta = point(pet.iv_at(stat), 6, 1)["stat"] - point(pet.iv_at(stat), 0, 1)["stat"]
    assert after - before == delta * (2 if stat == "hp" else 1)
    assert pet.get("e") == energy - 8
    assert pet.training_sessions == 1
    assert pet.techniques.training == 0  # attribute sessions are not technique lessons
    restored = Pet()
    restored.load_from_dict(pet.to_dict())
    assert restored.ev == pet.ev and restored.dna == dna


@pytest.mark.parametrize("blocked", ["egg", "baby", "dead", "injured", "cold", "energy", "cap"])
def test_training_rejections_do_not_spend_or_save(blocked):
    pet = firemon()
    if blocked in ("egg", "baby"):
        pet.species = blocked
    elif blocked == "energy":
        pet.stats["e"] = 7
    elif blocked == "cap":
        pet.ev["off"] = 252
    else:
        setattr(pet, blocked, True)
    before = pet.to_dict()
    session = TrainingSession(pet, lambda _: pytest.fail("Rejected training must not save"))
    # Batched flow: ACTION in state A must surface the block reason
    # and leave the pet unchanged. No state transition happens.
    session.input("action", 0)
    assert session.message and pet.to_dict() == before
    assert session.state == "select"


@pytest.mark.parametrize("species", ["rookie", "champion", "ultimate"])
def test_evolved_forms_can_train_and_stats_scale_with_stage(species):
    pet = firemon()
    pet.species = species
    before, projected = training_values(pet, 0)
    assert training_block_reason(pet, 0) == ""
    assert projected >= before
    from core.dna import combat_stat
    assert pet.combat_stat("off") >= combat_stat(pet.dna, pet.ev, "off", "rookie")


def test_training_cap_invalid_input_and_no_repeat_during_animation():
    """Drive the batched flow A→B→C and verify the partial-last-rep
    policy at cap, the animation debounce, and the EV AL MAXIMO
    block on a follow-up rep. The pet is only mutated after CONFIRMAR
    in the confirm sub-state, so the assertions check the draft
    buffer during the session."""
    pet = firemon()
    pet.ev["off"] = 82
    saves = []
    s = TrainingSession(pet, lambda p: saves.append(p.to_dict()) or True)
    # A → B: pick ATAQUE (index 0).
    s.input("action", 0)
    assert s.state == "prepare"
    # B → C: INICIAR is the default focus.
    s.input("action", 0)
    assert s.state == "session"
    # START reserves one partial rep immediately, without mutation.
    assert s.reps == 1
    assert s.pending_ev == 2  # partial: 82 + 2 = 84, not 6
    assert s.energy_reserved == 8
    assert pet.ev_at("off") == 82  # pet unchanged in state C
    s.input(None, 100)
    assert s.reps == 1
    # After the animation window the next rep is blocked: the
    # draft already holds pending_ev=2 (cumulative projected = 252).
    # We do not allow zero-gain reps that would only cost energy.
    s.input(None, 9999)
    assert s.reps == 1
    assert s.train_block_reason() == "EV AL MAXIMO"
    s.input(None, 10000)
    assert s.state == "result"
    # The pet is mutated exactly once, on commit, with the partial EV.
    assert pet.ev_at("off") == 84
    assert pet.training_sessions == 1
    assert len(saves) == 1
    # Edge: training_block_reason and batch_block_reason agree on
    # the invalid index / invalid stat code.
    assert training_block_reason(pet, -1) == "TIPO INVALIDO"
    assert not train_attribute(pet, 99)


def test_only_dumbbell_has_lessons_and_back_returns_to_dumbbell():
    pet = firemon()
    training = TrainingSession(pet, lambda _: True)
    for _ in range(6):
        training.input("next", 0)
    training.input("action", 0)
    assert training.techniques.page == "tech"
    training.input("next", 0)  # locked flame
    training.input("action", 0)
    training.input("action", 0)
    assert pet.techniques.training == 1
    training.input("action", 0)
    assert pet.techniques.learned(1)
    training.input("back", 0)
    assert training.techniques.page == "tech"
    training.input("back", 0)
    assert training.techniques is None and training.index == 6
    assert not training.input("back", 0)
    battle = PracticeSession(pet, lambda _: True)
    assert battle.page == "battle"
    assert "ENTRENAR" not in battle.choices()


def test_training_reports_save_failure_without_awarding_twice():
    """The batched flow: a save failure during CONFIRMAR must roll
    back the pet, surface NO SE GUARDO, and keep the draft intact so
    the player can retry. The second ACTION on the same draft must
    not double-apply."""
    pet = firemon()
    saves = []
    def save(p):
        saves.append(p.to_dict())
        return False
    s = TrainingSession(pet, save)
    # Drive to RESULT through the batched flow.
    s.input("action", 0)  # A → B
    s.input("action", 0)  # B → C
    s.input(None, 10000)  # Automatic completion; save fails.
    assert s.state == "error"
    assert s.message == "NO SE GUARDO"
    # Pet is rolled back: no EV, full energy.
    assert pet.ev_at("off") == 0
    assert pet.training_sessions == 0
    assert len(saves) == 1
    # REINTENTAR (default focus "retry" on entry to error) → second
    # commit attempt. Save still fails, so the pet must remain at the
    # rolled-back state.
    s.input("action", 0)
    assert s.state == "error"
    assert pet.ev_at("off") == 0
    assert pet.training_sessions == 0
    assert len(saves) == 2
