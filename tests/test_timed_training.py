import pytest

from core.pet import Pet
from scripts.training_session import TrainingSession


def session(energy=8):
    pet = Pet()
    pet.complete_hatch("rookie", entropy=12345)
    pet.stats["e"] = energy
    saves = []
    s = TrainingSession(pet, lambda p: saves.append(p.to_dict()) or True)
    s.input("action", 100)
    s.input("action", 100)
    return s, saves


def test_start_trains_immediately_and_commits_once_after_ten_seconds():
    s, saves = session()
    assert s.busy(100)
    assert s.pending_ev == 6
    assert s.energy_reserved == 8
    s.input(None, 10099)
    assert s.state == "session"
    assert s.pet.ev_at("off") == 0
    assert s.pet.get("e") == 8
    assert not saves
    s.input(None, 10100)
    assert s.state == "result"
    assert s.pet.ev_at("off") == 6
    assert s.pet.get("e") == 0
    s.input(None, 30100)
    assert len(saves) == 1


def test_cancel_confirmation_pauses_time_and_resume_keeps_progress():
    s, saves = session()
    s.input("action", 4100)
    assert s.state == "cancel"
    s.input(None, 24100)
    assert not saves
    s.input("action", 24100)
    assert s.state == "session"
    s.input(None, 30099)
    assert not saves
    s.input(None, 30100)
    assert len(saves) == 1


def test_cancel_discards_without_charging_or_saving():
    s, saves = session()
    s.input("back", 5100)
    s.input("next", 5100)
    s.input("action", 5100)
    s.input(None, 20100)
    assert s.state == "select"
    assert s.pet.get("e") == 8
    assert s.pet.ev_at("off") == 0
    assert not saves


def test_next_cannot_finish_early():
    s, saves = session()
    s.input("next", 200)
    s.input(None, 10099)
    assert s.state == "session"
    assert not saves


def test_failed_save_rolls_back_and_retry_does_not_repeat_timer():
    s, saves = session()
    s.save = lambda p: False
    s.input(None, 10100)
    assert s.state == "error"
    assert s.pet.get("e") == 8
    assert s.pet.ev_at("off") == 0
    s.save = lambda p: saves.append(p.to_dict()) or True
    s.input("action", 10101)
    assert s.state == "result"
    assert len(saves) == 1
    assert s.pet.ev_at("off") == 6


@pytest.mark.parametrize("index,stat", enumerate(("off", "def", "spd", "hp", "mp", "brn")))
def test_all_attributes_finish_once_with_partial_ev_cap(index, stat):
    pet = Pet()
    pet.complete_hatch("rookie", entropy=42)
    pet.stats["e"] = 80
    pet.ev[stat] = pet.ev_limit() - 2
    saves = []
    s = TrainingSession(pet, lambda p: saves.append(p.to_dict()) or True)
    s.index = index
    s.input("action", 0)
    s.input("action", 0)
    assert s.pending_ev == 2
    s.input(None, 10000)
    assert pet.ev_at(stat) == pet.ev_limit()
    assert pet.get("e") == 72
    assert len(saves) == 1
    assert s._focus == "back"


def test_repeat_prepares_new_session_without_charging_again():
    s, saves = session(16)
    s.input(None, 10100)
    s.input("action", 10101)
    assert s.state == "prepare"
    assert s.pet.get("e") == 8
    s.input("action", 10200)
    s.input(None, 20199)
    assert len(saves) == 1
    s.input(None, 20200)
    assert len(saves) == 2
    assert s.pet.get("e") == 0
    assert s.pet.ev_at("off") == 12
    assert s._focus == "back"


def test_interrupted_session_does_not_grant_or_charge_on_reentry():
    s, saves = session()
    s.input(None, 9000)
    reopened = TrainingSession(s.pet, s.save)
    reopened.input(None, 20000)
    assert reopened.state == "select"
    assert s.pet.get("e") == 8
    assert s.pet.ev_at("off") == 0
    assert not saves
