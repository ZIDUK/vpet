"""Inventory behavior shared by simulator and device."""

from core.inventory import INVENTORY_BACK_INDEX, use_inventory_item
from core.pet import Pet, STATE_LIVE


def test_consumable_updates_stat_and_decrements_quantity():
    pet = Pet(species="rookie", state=STATE_LIVE)
    pet.stats["e"] = 40

    assert use_inventory_item(pet, 1) == "used"
    assert pet.stats["e"] == 70
    assert pet.inventory["tonic"] == 1


def test_empty_consumable_does_not_change_stats():
    pet = Pet(species="rookie", state=STATE_LIVE)
    pet.inventory["medkit"] = 0
    before = dict(pet.stats)

    assert use_inventory_item(pet, 2) == "empty"
    assert pet.stats == before


def test_back_entry_closes_without_using_an_item():
    pet = Pet(species="rookie", state=STATE_LIVE)
    before = dict(pet.inventory)

    assert use_inventory_item(pet, INVENTORY_BACK_INDEX) == "back"
    assert pet.inventory == before
