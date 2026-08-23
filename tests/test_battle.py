"""Tests for the battle system."""
import pytest


@pytest.fixture
def pet():
    from core.pet import Pet
    p = Pet()
    p.stats["h"] = 100
    p.stats["e"] = 100
    p.stats["p"] = 100
    p.stats["hp"] = 100
    return p


def test_battle_initializes(pet):
    from core.battle import Battle
    npc = {"name": "Test", "hp": 50, "attack": 10}
    b = Battle(pet, npc)
    assert b.pet_hp == 100
    assert b.npc_hp == 50
    assert not b.over


def test_pet_attack_reduces_npc_hp(pet):
    from core.battle import Battle
    npc = {"name": "Test", "hp": 500, "attack": 10}
    b = Battle(pet, npc)
    b.pet_attack()
    assert b.npc_hp < 500
    assert not b.over


def test_battle_ends_when_npc_dies(pet):
    from core.battle import Battle
    npc = {"name": "Weak", "hp": 1, "attack": 1}
    b = Battle(pet, npc)
    b.pet_attack()
    assert b.npc_hp == 0
    assert b.over
    assert b.won
    assert pet.battles_won == 1


def test_battle_defeat_reduces_happiness(pet):
    from core.battle import Battle
    npc = {"name": "Tank", "hp": 1000, "attack": 1000}
    b = Battle(pet, npc)
    b.npc_attack()
    b.commit_to_pet()
    assert pet.get("hp") == 0
    assert b.over
    assert not b.won
    assert pet.get("p") < 100  # happiness reduced


def test_commit_to_pet_writes_hp_back(pet):
    from core.battle import Battle
    npc = {"name": "Weak", "hp": 1, "attack": 1}
    b = Battle(pet, npc)
    b.pet_attack()
    b.npc_attack()
    b.commit_to_pet()
    assert pet.get("hp") == b.pet_hp
