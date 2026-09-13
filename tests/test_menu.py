"""Menu actions shared by the simulator and CircuitPython app."""
import importlib.util

from core.motion import MOTION_CAST, MOTION_EAT, MOTION_PUNCH, MOTION_SLEEP, PetMotion
from core.pet import Pet, STATE_LIVE


def test_feed_menu_applies_food_and_starts_eat_animation():
    assert importlib.util.find_spec("core.menu") is not None
    from core.menu import activate_menu_item

    pet = Pet(species="rookie", state=STATE_LIVE)
    pet.stats["h"] = 50
    motion = PetMotion(now=0)

    assert activate_menu_item(pet, motion, menu_index=1, now=0.5)
    assert pet.stats["h"] == 75
    assert motion.state == MOTION_EAT


def test_status_menu_does_not_start_an_action():
    assert importlib.util.find_spec("core.menu") is not None
    from core.menu import activate_menu_item

    pet = Pet(species="rookie", state=STATE_LIVE)
    motion = PetMotion(now=0)

    assert not activate_menu_item(pet, motion, menu_index=0, now=0.5)


def test_training_menu_applies_training_and_starts_punch_animation():
    from core.menu import activate_menu_item

    pet = Pet(species="rookie", state=STATE_LIVE)
    pet.stats["p"] = 50
    motion = PetMotion(now=0)

    assert activate_menu_item(pet, motion, menu_index=2, now=0.5)
    assert pet.stats["p"] == 65
    assert motion.state == MOTION_PUNCH


def test_rest_menu_recovers_pet_and_starts_sleep_animation():
    from core.menu import activate_menu_item

    pet = Pet(species="rookie", state=STATE_LIVE)
    pet.stats["e"] = 50
    pet.stats["hp"] = 50
    motion = PetMotion(now=0)

    assert activate_menu_item(pet, motion, menu_index=4, now=0.5)
    assert pet.stats["e"] == 80
    assert pet.stats["hp"] == 60
    assert motion.state == MOTION_SLEEP

    assert not activate_menu_item(pet, motion, menu_index=1, now=1)
    assert motion.state == MOTION_SLEEP

    assert activate_menu_item(pet, motion, menu_index=4, now=1.5)
    assert motion.state != MOTION_SLEEP


def test_overfeed_once_when_full_is_not_a_care_mistake():
    from core.menu import activate_menu_item

    pet = Pet(species="rookie", state=STATE_LIVE)
    pet.stats["h"] = 100
    motion = PetMotion(now=0)

    assert activate_menu_item(pet, motion, menu_index=1, now=0.5)
    assert pet.stats["h"] == 100
    assert pet.overfeeds == 1
    assert pet.care_mistakes == 0
    assert pet.weight == 6
    assert not activate_menu_item(pet, motion, menu_index=1, now=1.0)
    assert pet.overfeeds == 1
    assert motion.state == MOTION_EAT


def test_wake_at_night_adds_care_mistake():
    from core.menu import activate_menu_item

    pet = Pet(species="rookie", state=STATE_LIVE)
    motion = PetMotion(now=0)
    assert activate_menu_item(pet, motion, menu_index=4, now=0.5, hour=22)
    assert activate_menu_item(pet, motion, menu_index=4, now=1.5, hour=22)
    assert pet.care_mistakes == 1
    assert motion.state != MOTION_SLEEP


def test_battle_menu_starts_cast_when_dp_available():
    from core.menu import activate_menu_item

    pet = Pet(species="rookie", state=STATE_LIVE)
    pet.dp = 1
    pet.battle_roll = 0
    motion = PetMotion(now=0)

    assert activate_menu_item(pet, motion, menu_index=3, now=0.5)
    assert pet.dp == 0
    assert pet.last_battle_won
    assert motion.state == MOTION_CAST
    assert not activate_menu_item(pet, motion, menu_index=3, now=1.0)
