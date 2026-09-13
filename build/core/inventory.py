"""Small consumable inventory shared by the simulator and device runtime."""

INVENTORY_ITEMS = (
    ("MEAT", "meat", "h", 20),
    ("ENERGY", "energy", "e", 25),
    ("EXP", "exp", "effort", 8),
    ("FIRE RING", "ring", "p", 15),
)
INVENTORY_BACK_INDEX = len(INVENTORY_ITEMS)
INVENTORY_ENTRY_COUNT = INVENTORY_BACK_INDEX + 1
DEFAULT_INVENTORY = {"meat": 3, "energy": 2, "exp": 1, "ring": 1}


def item_visible(pet, index):
    if index == INVENTORY_BACK_INDEX:
        return True
    if index < 0 or index >= len(INVENTORY_ITEMS):
        return False
    _, key, _, _ = INVENTORY_ITEMS[index]
    return pet.inventory.get(key, 0) > 0


def visible_inventory_indexes(pet):
    return tuple(index for index in range(INVENTORY_ENTRY_COUNT) if item_visible(pet, index))


def next_visible_inventory_index(pet, index):
    for step in range(1, INVENTORY_ENTRY_COUNT + 1):
        candidate = (index + step) % INVENTORY_ENTRY_COUNT
        if item_visible(pet, candidate):
            return candidate
    return INVENTORY_BACK_INDEX


def clamp_visible_inventory_index(pet, index):
    return index if item_visible(pet, index) else next_visible_inventory_index(pet, index)


def use_inventory_item(pet, index):
    """Use one selected item; return 'used', 'empty', 'blocked', or 'back'."""
    if index == INVENTORY_BACK_INDEX:
        return "back"
    if index < 0 or index >= len(INVENTORY_ITEMS):
        return "empty"
    if getattr(pet, "species", None) == "egg" or getattr(pet, "state", None) == "egg":
        return "blocked"

    _, key, stat, amount = INVENTORY_ITEMS[index]
    count = pet.inventory.get(key, 0)
    if count <= 0:
        return "empty"
    pet.inventory[key] = count - 1
    if stat == "effort":
        pet.effort = min(100, getattr(pet, "effort", 0) + amount)
    else:
        pet.stats[stat] = min(100, pet.stats[stat] + amount)
    return "used"
