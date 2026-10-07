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
    assert after - before == (2 if stat == "hp" else 1)
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
    session.input("action", 0)
    assert session.message and pet.to_dict() == before


def test_training_cap_invalid_input_and_no_repeat_during_animation():
    pet = firemon()
    pet.ev["off"] = 250
    saves = []
    s = TrainingSession(pet, lambda p: saves.append(p.to_dict()) or True)
    s.input("action", 0)
    assert pet.ev["off"] == 252 and len(saves) == 1
    s.input("action", 100)
    s.input("next", 100)
    assert pet.training_sessions == 1 and s.index == 0
    s.input("action", 1500)
    assert s.message == "NIVEL MAXIMO" and len(saves) == 1
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
    pet = firemon()
    s = TrainingSession(pet, lambda _: False)
    s.input("action", 0)
    assert s.message == "ERROR AL GUARDAR"
    s.input("action", 0)
    assert pet.training_sessions == 1
