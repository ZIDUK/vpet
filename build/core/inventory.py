"""Small consumable inventory shared by the simulator and device runtime."""
from core.item_catalog import DEFAULT_STOCK, ITEM_BY_ID, LEGACY_ITEMS, effect_amount, item_at
from core.adopted_items import (ITEMS as ADOPTED, MENU_OFFSET, menu_item,
                               item_name, item_blurb, use_care_item)

INVENTORY_ITEMS = tuple((item["names"]["EN"], item["id"],
                         item["effects"][0]["target"], item["effects"][0]["amount"])
                        for item in LEGACY_ITEMS)
INVENTORY_BACK_INDEX = len(INVENTORY_ITEMS)
INVENTORY_GUIDE_INDEX = INVENTORY_BACK_INDEX + 1
INVENTORY_ENTRY_COUNT = MENU_OFFSET + len(ADOPTED)
DEFAULT_INVENTORY = dict(DEFAULT_STOCK)
INVENTORY_WINDOW = 3
INVENTORY_ICONS = tuple(item["icon"] for item in LEGACY_ITEMS) + ("Back", ITEM_BY_ID["guide"]["icon"])
INVENTORY_NAMES = tuple((item["names"]["EN"], item["names"]["ES"]) for item in LEGACY_ITEMS) + (("BACK", "ATRAS"),)
INVENTORY_BLURBS = tuple((item["blurbs"]["EN"], item["blurbs"]["ES"]) for item in LEGACY_ITEMS) + (("CLOSE BAG", "CERRAR"),)


def inventory_name(index, spanish=False):
    adopted = menu_item(index)
    if adopted:
        return item_name(adopted, spanish)
    item = item_at(index)
    return item["names"]["ES" if spanish else "EN"] if item else ("ATRAS" if spanish else "BACK")


def inventory_blurb(index, spanish=False):
    adopted = menu_item(index)
    if adopted:
        return item_blurb(adopted, spanish)
    item = item_at(index)
    return item["blurbs"]["ES" if spanish else "EN"] if item else ("CERRAR" if spanish else "CLOSE BAG")


def inventory_icon(index):
    adopted = menu_item(index)
    if adopted:
        return 'Adopted:' + adopted['id']
    if index < 0 or index >= len(INVENTORY_ICONS):
        return "Back"
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
    adopted = menu_item(index)
    if adopted:
        return not adopted['unlimited'] and pet.adopted_inventory.get(adopted['id'], 0) > 0
    if index == INVENTORY_GUIDE_INDEX:
        return pet.exploration.guide
    if index == INVENTORY_BACK_INDEX:
        return True
    if index < 0 or index >= len(INVENTORY_ITEMS):
        return False
    if index in (0, 4):
        return False
    _, key, _, _ = INVENTORY_ITEMS[index]
    return pet.inventory.get(key, 0) > 0


def visible_inventory_indexes(pet):
    order = (*range(len(INVENTORY_ITEMS)), *range(MENU_OFFSET, INVENTORY_ENTRY_COUNT),
             INVENTORY_GUIDE_INDEX, INVENTORY_BACK_INDEX)
    return tuple(index for index in order if item_visible(pet, index))


def next_visible_inventory_index(pet, index):
    visible = visible_inventory_indexes(pet)
    if index in visible:
        return visible[(visible.index(index) + 1) % len(visible)]
    for candidate in visible:
        if candidate > index:
            return candidate
    return INVENTORY_BACK_INDEX


def clamp_visible_inventory_index(pet, index):
    return index if item_visible(pet, index) else next_visible_inventory_index(pet, index)


def use_inventory_item(pet, index):
    """Use one selected item; return 'used', 'empty', 'blocked', or 'back'."""
    if index == INVENTORY_BACK_INDEX:
        return "back"
    if getattr(getattr(pet, 'sleep', None), 'asleep', False):
        return "blocked"
    if index == INVENTORY_GUIDE_INDEX:
        return "train" if pet.exploration.guide and not pet.exploration.away else "blocked"
    if pet.exploration.away:
        return "blocked"
    adopted = menu_item(index)
    if adopted:
        if pet.is_egg or pet.dead or getattr(pet, 'cold', False):
            return 'blocked'
        if adopted['id'] == 'training_manual':
            return 'train' if pet.adopted_inventory.get('training_manual', 0) else 'empty'
        return 'used' if use_care_item(pet, pet.adopted_inventory, adopted['id']) else 'blocked'
    if index < 0 or index >= len(INVENTORY_ITEMS):
        return "empty"
    if index in (0, 4):
        return "blocked"
    if getattr(pet, "species", None) == "egg" or getattr(pet, "state", None) == "egg":
        return "blocked"
    if getattr(pet, "dead", False):
        return "blocked"
    if index == 0 and not pet.can_feed():
        return "blocked"
    if index == 5 and not getattr(pet, "injured", False):
        return "blocked"
    if index == 1 and pet.get("e") >= 100:
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
        pet.gain_ev("brn", effect_amount("exp", "ev", "brn"))
    elif key == "energy":
        pet.stats[stat] = min(100, pet.stats[stat] + amount)
        pet.gain_ev("mp", effect_amount("energy", "ev", "mp"))
    else:
        pet.stats[stat] = min(100, pet.stats[stat] + amount)
    return "used"
