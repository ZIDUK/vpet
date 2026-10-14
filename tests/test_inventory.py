"""Inventory behavior shared by simulator and device."""

from core.inventory import (
    INVENTORY_ICONS,
    INVENTORY_BACK_INDEX,
    INVENTORY_WINDOW,
    clamp_visible_inventory_index,
    inventory_blurb,
    inventory_name,
    inventory_window,
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

    assert use_inventory_item(pet, 0) == "blocked"
    assert pet.inventory["meat"] == 3
    assert pet.stats["h"] == 80
    assert use_inventory_item(pet, 1) == "used"
    assert pet.inventory["energy"] == 1
    assert pet.stats["e"] == 100
    assert use_inventory_item(pet, 2) == "used"
    assert pet.inventory["exp"] == 0
    assert pet.effort == 8
    assert use_inventory_item(pet, 3) == "used"
    assert pet.inventory["ring"] == 0
    assert pet.stats["p"] == 95


def test_energy_item_matches_training_energy_and_does_not_waste_at_full():
    pet = Pet(species="champion", state=STATE_LIVE)
    pet.stats["e"] = 75
    assert use_inventory_item(pet, 1) == "used"
    assert pet.stats["e"] == 100
    assert use_inventory_item(pet, 1) == "blocked"
    assert pet.inventory["energy"] == 1


def test_empty_and_egg_do_not_change_stats():
    pet = Pet(species="egg", state=STATE_EGG)
    assert use_inventory_item(pet, 0) == "blocked"
    assert pet.inventory["meat"] == 3
    assert use_inventory_item(pet, INVENTORY_BACK_INDEX) == "back"

    pet = Pet(species="rookie", state=STATE_LIVE)
    pet.inventory = {"meat": 0, "energy": 0, "exp": 0, "ring": 0}
    before = dict(pet.stats)
    assert use_inventory_item(pet, 0) == "blocked"
    assert pet.stats == before


def test_inventory_window_keeps_selection_visible():
    visible = (1, 2, 3, 5, 6)
    assert INVENTORY_WINDOW == 3
    assert inventory_window(visible, 1) == (1, 2, 3)
    assert inventory_window(visible, 3) == (2, 3, 5)
    assert inventory_window(visible, 6) == (3, 5, 6)
    assert inventory_window((1, 6), 6) == (1, 6)


def test_inventory_preview_has_a_short_blurb():
    assert inventory_name(0, spanish=False) == "MEAT"
    assert inventory_name(0, spanish=True) == "CARNE"
    assert "20" in inventory_blurb(0, spanish=False)
    assert inventory_name(INVENTORY_BACK_INDEX, spanish=False) == "BACK"


def test_inventory_uses_back_arrow_for_return_entry():
    assert INVENTORY_ICONS == (
        "ItemMeat", "ItemEnergy", "ItemExp", "ItemRing",
        "ItemProtein", "ItemMedkit", "Back",
    )


def test_empty_items_disappear_from_inventory_list():
    pet = Pet(species="rookie", state=STATE_LIVE)
    pet.inventory = {"meat": 3, "energy": 0, "exp": 1, "ring": 0}
    assert visible_inventory_indexes(pet) == (2, 6)
    assert next_visible_inventory_index(pet, 1) == 2
    assert next_visible_inventory_index(pet, 2) == 6
    assert next_visible_inventory_index(pet, 6) == 2
    assert clamp_visible_inventory_index(pet, 1) == 2

    assert use_inventory_item(pet, 2) == "used"
    assert visible_inventory_indexes(pet) == (6,)
    assert clamp_visible_inventory_index(pet, 2) == 6
