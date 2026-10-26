import pytest

from core.pet import Pet
from core.training import batch_commit, BatchSaveError


def adult():
    pet = Pet(species="rookie", state="live")
    pet.stats = {"h": 90, "e": 90, "p": 90, "hp": 100}
    pet.roll_dna(42)
    pet.learning
    return pet


def test_pet_policy_roundtrip_and_legacy_does_not_change_genes():
    pet = adult()
    genes = list(pet.dna)
    assert pet.learning.record(1, 0, 0, 0, 80)
    restored = Pet()
    restored.load_from_dict(pet.to_dict())
    assert restored.learning.encode() == pet.learning.encode()
    assert restored.dna == genes
    data = pet.to_dict()
    del data["learning"]
    restored.load_from_dict(data)
    assert restored.learning.last_sequence == 0 and restored.dna == genes


def test_training_effect_and_experience_commit_or_rollback_together():
    pet = adult()
    before = pet.to_dict()
    with pytest.raises(BatchSaveError):
        batch_commit(pet, "spd", 1, lambda _: False)
    assert pet.to_dict() == before
    saved = []
    result = batch_commit(pet, "spd", 1, lambda p: saved.append(p.to_dict()) or True)
    assert result["ev_added"] > 0
    assert pet.learning.last_sequence == 1
    event = pet.learning.history[-1]
    assert (event.domain, event.context, event.action) == (0, 0, 2)
    assert saved[-1]["learning"] == pet.learning.encode()


def test_auto_learns_only_legal_actions_and_manual_orders_keep_original_rules():
    from core.learning import LearningState
    from core.practice import Fighter, choose
    fighter = Fighter((30,) * 6, equipped=(0, 1), bond=100)
    fighter.learning = LearningState()
    assert fighter.learning.record(1, 1, 0, 0, 100)
    assert choose(fighter)[0] == 0
    assert choose(fighter, 1)[0] == 1
    fighter.mp = 0
    assert choose(fighter)[0] == 0


def test_arena_award_retries_do_not_duplicate_experience():
    from scripts.practice_session import PracticeSession
    pet = adult()
    accepted = [False]
    session = PracticeSession(pet, lambda _: accepted[0])
    session.battle.result = "VICTORIA"
    session.battle.uses[0] = 3
    assert not session._award_result()
    assert pet.learning.last_sequence == 0 and pet.battles_won == 0
    accepted[0] = True
    assert session._award_result()
    count = pet.learning.last_sequence
    assert count > 0
    assert session._award_result()
    assert pet.learning.last_sequence == count and pet.battles_won == 1


def test_exploration_claim_records_experience_once_and_no_extra_ev():
    from scripts.exploration_session import ExplorationSession
    pet = adult()
    now = [1700000000]
    assert pet.exploration.start(pet, "patio", "off", now[0])
    now[0] += 1800
    session = ExplorationSession(pet, lambda _: True, lambda: now[0])
    session._transaction(True)
    assert pet.learning.last_sequence == 1
    event = pet.learning.history[-1]
    assert (event.domain, event.context, event.action) == (2, 0, 0)
    before = pet.to_dict()
    session._transaction(True)
    assert pet.to_dict() == before


def test_opening_activity_views_does_not_create_experience_or_change_save():
    from scripts.training_session import TrainingSession
    from scripts.practice_session import PracticeSession
    from scripts.exploration_session import ExplorationSession
    for factory in (lambda p: TrainingSession(p, lambda _: True),
                    lambda p: PracticeSession(p, lambda _: True),
                    lambda p: ExplorationSession(p, lambda _: True, lambda: 1700000000)):
        pet = Pet(species="rookie", state="live")
        before = pet.to_dict()
        factory(pet)
        assert pet.to_dict() == before


def test_technique_training_learns_only_after_a_saved_lesson():
    from scripts.practice_session import PracticeSession
    pet = adult()
    accepted = [False]
    session = PracticeSession(pet, lambda _: accepted[0], training=True)
    session.input("action", 0)
    before = pet.to_dict()
    session.input("action", 0)
    assert pet.to_dict() == before
    accepted[0] = True
    session.input("action", 0)
    event = pet.learning.history[-1]
    assert (event.domain, event.context, event.action) == (1, 1, 0)
    assert event.reward > 0
