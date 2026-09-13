"""Small consumable inventory shared by the simulator and device runtime."""

INVENTORY_ITEMS = (
    ("MEAT", "meat", "h", 20),
    ("ENERGY", "energy", "e", 25),
    ("EXP", "exp", "effort", 8),
    ("FIRE RING", "ring", "p", 15),
    ("PROTEIN", "protein", "e", 20),
    ("MEDKIT", "medkit", "hp", 20),
)
INVENTORY_BACK_INDEX = len(INVENTORY_ITEMS)
INVENTORY_ENTRY_COUNT = INVENTORY_BACK_INDEX + 1
DEFAULT_INVENTORY = {"meat": 3, "energy": 2, "exp": 1, "ring": 1, "protein": 2, "medkit": 1}
INVENTORY_WINDOW = 3
INVENTORY_ICONS = ("Feed", "Energy", "Training", "Items", "Protein", "Medkit", "Options")
INVENTORY_NAMES = (
    ("MEAT", "CARNE"),
    ("ENERGY", "ENERGIA"),
    ("EXP", "EXP"),
    ("RING", "ANILLO"),
    ("PROTEIN", "PROTEINA"),
    ("MEDKIT", "BOTIQUIN"),
    ("BACK", "ATRAS"),
)
INVENTORY_BLURBS = (
    ("+20 HUN", "+20 HAM"),
    ("+25 ENE", "+25 ENE"),
    ("+8 EFF", "+8 ESF"),
    ("+15 POW", "+15 POD"),
    ("+20 ENE", "+20 ENE"),
    ("HEAL HURT", "CURA"),
    ("CLOSE BAG", "CERRAR"),
)


def inventory_name(index, spanish=False):
    names = INVENTORY_NAMES[INVENTORY_BACK_INDEX if index >= INVENTORY_BACK_INDEX else index]
    return names[1] if spanish else names[0]


def inventory_blurb(index, spanish=False):
    blurbs = INVENTORY_BLURBS[INVENTORY_BACK_INDEX if index >= INVENTORY_BACK_INDEX else index]
    return blurbs[1] if spanish else blurbs[0]


def inventory_icon(index):
    if index < 0 or index >= len(INVENTORY_ICONS):
        return INVENTORY_ICONS[-1]
    return INVENTORY_ICONS[index]


def inventory_window(visible, current, size=INVENTORY_WINDOW):
    items = tuple(visible)
    if not items:
        return ()
    if current not in items:
        current = items[0]
    pos = items.index(current)
    start = pos - 1
    if start < 0:
        start = 0
    if start + size > len(items):
        start = max(0, len(items) - size)
    return items[start : start + size]


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
    if getattr(pet, "dead", False):
        return "blocked"
    if index == 0 and not pet.can_feed():
        return "blocked"
    if index == 5 and not getattr(pet, "injured", False):
        return "blocked"

    _, key, stat, amount = INVENTORY_ITEMS[index]
    count = pet.inventory.get(key, 0)
    if count <= 0:
        return "empty"
    pet.inventory[key] = count - 1
    if key == "meat":
        pet.feed(from_item=True)
        return "used"
    if key == "protein":
        pet.use_protein()
        pet.gain_ev("off", 2)
        return "used"
    if key == "medkit":
        pet.use_medkit()
        return "used"
    if stat == "effort":
        pet.effort = min(100, getattr(pet, "effort", 0) + amount)
        pet.gain_ev("brn", 2)
    elif key == "energy":
        pet.stats[stat] = min(100, pet.stats[stat] + amount)
        pet.gain_ev("mp", 2)
    else:
        pet.stats[stat] = min(100, pet.stats[stat] + amount)
    return "used"
