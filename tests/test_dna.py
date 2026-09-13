"""DNA / IV / EV — same contract as the T-Display firmware spec."""

from core.dna import (
    HELIX_TURNS,
    combat_stat,
    format_dna_id,
    helix_color565,
    helix_sample,
    helix_spin,
    helix_x,
    iv_at,
    mix_entropy,
)
from core.inventory import use_inventory_item
from core.menu import activate_menu_item
from core.motion import PetMotion
from core.pet import Pet, STATE_LIVE


def test_roll_dna_differs_and_is_never_zero():
    a = Pet()
    b = Pet()
    a.roll_dna(1)
    b.roll_dna(2)
    assert a.has_dna()
    assert b.has_dna()
    assert a.dna != b.dna


def test_ivs_read_dna_nibbles():
    pet = Pet()
    pet.restore_dna((0x21, 0x43, 0x65, 0x87))
    assert pet.iv_at("hp") == 1
    assert pet.iv_at("mp") == 2
    assert pet.iv_at("off") == 3
    assert pet.iv_at("def") == 4
    assert pet.iv_at("spd") == 5
    assert pet.iv_at("brn") == 6
    assert iv_at((0x21, 0x43, 0x65, 0x87), "hp") == 1


def test_combat_stat_uses_iv_ev_formula():
    pet = Pet()
    pet.restore_dna((0x0F, 0x00, 0x00, 0x01))
    pet.restore_ev({"hp": 252})
    assert pet.combat_stat("mp") == 10
    assert pet.combat_stat("hp") == 97
    assert combat_stat((0x0F, 0x00, 0x00, 0x01), {"hp": 252}, "hp") == 97


def test_care_and_items_gain_ev():
    pet = Pet(species="rookie", state=STATE_LIVE)
    pet.stats.update({"h": 40, "e": 80, "p": 80, "hp": 80})
    pet.dp = 3
    pet.battle_roll = 0
    motion = PetMotion(now=0)
    assert activate_menu_item(pet, motion, 1, 0.5)
    assert pet.ev_at("hp") == 2
    assert activate_menu_item(pet, motion, 2, 1.0)
    assert pet.ev_at("off") == 2
    assert pet.ev_at("spd") == 1
    assert activate_menu_item(pet, motion, 3, 1.5)
    assert pet.ev_at("off") == 3
    assert pet.ev_at("brn") == 1
    assert activate_menu_item(pet, motion, 4, 2.0)
    assert pet.ev_at("mp") == 0
    assert activate_menu_item(pet, motion, 4, 2.5)
    assert pet.ev_at("mp") == 2
    assert pet.ev_at("def") == 1
    assert use_inventory_item(pet, 0) == "used"
    assert pet.ev_at("hp") == 4
    assert use_inventory_item(pet, 1) == "used"
    assert pet.ev_at("mp") == 4
    assert use_inventory_item(pet, 2) == "used"
    assert pet.ev_at("brn") == 3
    assert use_inventory_item(pet, 4) == "used"
    assert pet.ev_at("off") == 5
    before = pet.ev_at("hp")
    assert use_inventory_item(pet, 3) == "used"
    assert pet.ev_at("hp") == before


def test_overfeed_does_not_gain_ev():
    pet = Pet(species="rookie", state=STATE_LIVE)
    pet.stats["h"] = 100
    motion = PetMotion(now=0)
    assert activate_menu_item(pet, motion, 1, 0.5)
    assert pet.ev_at("hp") == 0
    assert pet.overfeeds == 1


def test_reset_to_egg_clears_dna_and_hatch_rolls():
    pet = Pet(species="rookie", state=STATE_LIVE)
    pet.roll_dna(9)
    pet.restore_ev({"hp": 8})
    pet.reset_to_egg()
    assert not pet.has_dna()
    assert pet.ev_at("hp") == 0
    pet.complete_hatch("baby", entropy=11)
    assert pet.has_dna()
    assert pet.dna == mix_entropy(11)


def test_evolution_keeps_dna_and_ev():
    from core.evolution import Evolution

    pet = Pet(species="baby", state=STATE_LIVE)
    pet.roll_dna(11)
    pet.restore_ev({"hp": 6, "off": 4})
    dna = list(pet.dna)
    Evolution._apply(pet, "rookie")
    assert pet.species == "rookie"
    assert pet.dna == dna
    assert pet.ev_at("hp") == 6
    assert pet.ev_at("off") == 4


def test_save_roundtrip_and_schema2_migrate():
    saved = Pet(species="rookie", state=STATE_LIVE)
    saved.roll_dna(42)
    saved.restore_ev({"hp": 10, "brn": 12})
    restored = Pet()
    restored.load_from_dict(saved.to_dict())
    assert restored.dna == saved.dna
    assert restored.ev_at("hp") == 10
    assert restored.ev_at("brn") == 12

    old = Pet(species="rookie", state=STATE_LIVE)
    old.born_at = old.born_at  # age from fake? use load payload
    payload = {"species": "rookie", "state": "live", "age_seconds": 40, "battles_won": 0}
    first = Pet()
    first.load_from_dict(payload)
    second = Pet()
    second.load_from_dict(payload)
    assert first.has_dna()
    assert first.dna == second.dna
    expected = Pet()
    expected.roll_dna((40 * 2654435761 + 0) & 0xFFFFFFFF)
    assert first.dna == expected.dna


def test_helix_uses_one_stretched_turn():
    assert HELIX_TURNS == 1.0


def test_dna_id_keeps_readable_byte_gaps():
    assert format_dna_id((0x66, 0x21, 0xAB, 0xD3)) == "DNA: 66-21-AB-D3"
    assert format_dna_id((0, 0, 0, 0)) == "DNA: -- -- -- --"


def test_helix_helpers_match_firmware():
    dna = (0x12, 0x34, 0x56, 0x78)
    assert helix_color565(dna, 0) == 0x1234
    assert helix_color565(dna, 1) == 0x5678
    assert helix_color565((0, 0, 0, 0), 0) == 0x7BEF
    assert helix_x(0, 0, 28) != helix_x(1, 0, 28)
    assert helix_sample(0, 0.125, 32) > helix_sample(1, 0.125, 32)
    assert helix_sample(0, 0.0, 32) == helix_sample(1, 0.0, 32)
    assert helix_sample(0, 0.0, 32, spin=0) != helix_sample(0, 0.0, 32, spin=1.5708)
    assert helix_spin(0) == 0
    assert helix_spin(1200) != helix_spin(0)
