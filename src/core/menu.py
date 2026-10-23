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
from core.training import (MENU_TRAIN_ENERGY_COST, MENU_TRAIN_STATS, train_menu,
                            menu_train_block_reason)


def tdisplay_menu_available(species, index):
    if index in (2, 3, 4):
        return species not in ("egg", "baby")
    if index in (1, 5):
        return species != "egg"
    return True


def next_tdisplay_menu(species, index):
    for _ in range(9):
        index = (index + 1) % 9
        if tdisplay_menu_available(species, index):
            return index
    return 0


def activate_menu_item(pet, motion, menu_index, now, hour=12,
                        menu_train_stat=None):
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
        # v1 balance: menu training costs MENU_TRAIN_ENERGY_COST and
        # grants +1 EV in the chosen stat. The caller passes
        # ``menu_train_stat`` (one of MENU_TRAIN_STATS); the default
        # falls back to the first stat if the caller does not pick.
        target = menu_train_stat if menu_train_stat in MENU_TRAIN_STATS else MENU_TRAIN_STATS[0]
        if menu_train_block_reason(pet):
            return False
        if not train_menu(pet, target):
            return False
        motion.start_punch(now)
    elif menu_index == MENU_REST_INDEX:
        pet.answer_lights()
        pet.restore_dp()
        motion.start_sleep(now)
    return True
