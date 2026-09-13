"""Apply menu commands consistently on the board and in the simulator."""
from config import (
    BABY_SPECIES,
    MENU_ACTIONS,
    MENU_BATTLE_INDEX,
    MENU_FEED_INDEX,
    MENU_REST_INDEX,
    MENU_TRAINING_INDEX,
)
from core.motion import MOTION_SLEEP


def activate_menu_item(pet, motion, menu_index, now, hour=12):
    if motion.state == MOTION_SLEEP:
        if menu_index != MENU_REST_INDEX:
            return False
        motion.wake(now)
        pet.note_wake(hour)
        pet.gain_ev("mp", 2)
        pet.gain_ev("def", 1)
        return True
    if pet.species == BABY_SPECIES and menu_index in (MENU_TRAINING_INDEX, MENU_BATTLE_INDEX):
        return False
    if menu_index == MENU_BATTLE_INDEX:
        if not pet.can_battle():
            return False
        pet.finish_battle()
        motion.start_cast(now)
        return True
    if menu_index == MENU_FEED_INDEX:
        if not pet.feed():
            return False
        motion.start_eat(now)
        return True
    action = MENU_ACTIONS.get(menu_index)
    if action is None:
        return False
    pet.apply_action(action)
    if menu_index == MENU_TRAINING_INDEX:
        pet.training_sessions = getattr(pet, "training_sessions", 0) + 1
        pet.gain_ev("off", 2)
        pet.gain_ev("spd", 1)
        motion.start_punch(now)
    elif menu_index == MENU_REST_INDEX:
        pet.answer_lights()
        pet.restore_dp()
        motion.start_sleep(now)
    return True
