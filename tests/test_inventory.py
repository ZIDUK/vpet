"""Inventory behavior shared by simulator and device."""

from core.inventory import (
    INVENTORY_BACK_INDEX,
    clamp_visible_inventory_index,
    next_visible_inventory_index,
    use_inventory_item,
    visible_inventory_indexes,
)
from core.pet import Pet, STATE_EGG, STATE_LIVE


def test_use_item_spends_stock_and_applies_plate_stats():
    pet = Pet(species="rookie", state=STATE_LIVE)
    pet.stats["h"] = 80
    pet.stats["e"] = 80
    pet.stats["p"] = 80
    pet.effort = 0

    assert use_inventory_item(pet, 0) == "used"
    assert pet.inventory["meat"] == 2
    assert pet.stats["h"] == 100
    assert use_inventory_item(pet, 1) == "used"
    assert pet.inventory["energy"] == 1
    assert pet.stats["e"] == 100
    assert use_inventory_item(pet, 2) == "used"
    assert pet.inventory["exp"] == 0
    assert pet.effort == 8
    assert use_inventory_item(pet, 3) == "used"
    assert pet.inventory["ring"] == 0
    assert pet.stats["p"] == 95


def test_empty_and_egg_do_not_change_stats():
    pet = Pet(species="egg", state=STATE_EGG)
    assert use_inventory_item(pet, 0) == "blocked"
    assert pet.inventory["meat"] == 3
    assert use_inventory_item(pet, INVENTORY_BACK_INDEX) == "back"

    pet = Pet(species="rookie", state=STATE_LIVE)
    pet.inventory = {"meat": 0, "energy": 0, "exp": 0, "ring": 0}
    before = dict(pet.stats)
    assert use_inventory_item(pet, 0) == "empty"
    assert pet.stats == before


def test_empty_items_disappear_from_inventory_list():
    pet = Pet(species="rookie", state=STATE_LIVE)
    pet.inventory = {"meat": 3, "energy": 0, "exp": 1, "ring": 0}
    assert visible_inventory_indexes(pet) == (0, 2, 4)
    assert next_visible_inventory_index(pet, 0) == 2
    assert next_visible_inventory_index(pet, 2) == 4
    assert next_visible_inventory_index(pet, 4) == 0
    assert clamp_visible_inventory_index(pet, 1) == 2

    assert use_inventory_item(pet, 2) == "used"
    assert visible_inventory_indexes(pet) == (0, 4)
    assert clamp_visible_inventory_index(pet, 2) == 4
