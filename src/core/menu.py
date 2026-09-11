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


def activate_menu_item(pet, motion, menu_index, now):
    if motion.state == MOTION_SLEEP:
        if menu_index != MENU_REST_INDEX:
            return False
        motion.wake(now)
        return True
    if pet.species == BABY_SPECIES and menu_index in (MENU_TRAINING_INDEX, MENU_BATTLE_INDEX):
        return False
    if menu_index == MENU_BATTLE_INDEX:
        motion.start_cast(now)
        return True
    action = MENU_ACTIONS.get(menu_index)
    if action is None:
        return False
    pet.apply_action(action)
    if menu_index == MENU_FEED_INDEX:
        motion.start_eat(now)
    elif menu_index == MENU_TRAINING_INDEX:
        motion.start_punch(now)
    elif menu_index == MENU_REST_INDEX:
        motion.start_sleep(now)
    return True
