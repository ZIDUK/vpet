"""Small consumable inventory shared by the simulator and device runtime."""

INVENTORY_ITEMS = (
    ("MEAT", "meat", "h", 25),
    ("TONIC", "tonic", "e", 30),
    ("MEDKIT", "medkit", "hp", 30),
)
INVENTORY_BACK_INDEX = len(INVENTORY_ITEMS)
INVENTORY_ENTRY_COUNT = INVENTORY_BACK_INDEX + 1


def use_inventory_item(pet, index):
    """Use one selected item; return 'used', 'empty', or 'back'."""
    if index == INVENTORY_BACK_INDEX:
        return "back"
    if index < 0 or index >= len(INVENTORY_ITEMS):
        return "empty"

    _, key, stat, amount = INVENTORY_ITEMS[index]
    count = pet.inventory.get(key, 0)
    if count <= 0:
        return "empty"
    pet.inventory[key] = count - 1
    pet.stats[stat] = min(100, pet.stats[stat] + amount)
    return "used"
