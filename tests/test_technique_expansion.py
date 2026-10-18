import subprocess
from pathlib import Path

import pytest

from core.pet import Pet
from core.techniques import TECHNIQUES
from core.practice import Fighter, PracticeBattle
from scripts.practice_session import PracticeSession

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('species,capacity', [('rookie', 2), ('champion', 3), ('ultimate', 4)])
def test_equipment_capacity_and_stage_gates(species, capacity):
    pet = Pet(species=species, state='live')
    pet.techniques.training = 6
    assert pet.techniques.capacity(species) == capacity
    assert pet.techniques.equipped == [0, 2]
    for i in (1, 3, 4):
        assert pet.techniques.equip(i, species) == (i <= capacity)
    assert len(pet.techniques.equipped) == capacity
    restored = Pet()
    restored.load_from_dict(pet.to_dict())
    assert restored.techniques.to_dict() == pet.techniques.to_dict()


def test_stage_learning_and_evolution_never_auto_equip():
    pet = Pet(species='champion', state='live')
    pet.techniques.training = 3
    assert not pet.techniques.learned(3, pet.species)
    assert pet.techniques.train(pet, 3)
    assert pet.techniques.learned(3, pet.species)
    assert pet.techniques.equipped == [0, 2]
    assert not pet.techniques.train(pet, 4)
    pet.species = 'ultimate'
    assert not pet.techniques.learned(4, pet.species)
    assert pet.techniques.train(pet, 4)
    assert pet.techniques.train(pet, 4)
    assert pet.techniques.learned(4, pet.species)
    assert pet.techniques.equipped == [0, 2]


@pytest.mark.parametrize('action,mp,cooldown', [(3, 12, 1), (4, 18, 2)])
def test_new_actions_have_cost_cooldown_and_element(action, mp, cooldown):
    assert len(TECHNIQUES) == 5
    source = Fighter((99,) * 6, equipped=(action,), bond=100)
    target = Fighter((99,) * 6, equipped=(2,), element='plant')
    battle = PracticeBattle(source, target)
    before = source.mp
    assert battle.step(action)
    assert battle.actions[0] == action
    assert source.mp == before - mp
    assert source.cooldowns[action] == cooldown
    base = TECHNIQUES[action]['power'] + 99 // 3 - 99 // 4
    assert battle.damage[0] == max(1, (base * 3 // 2) // 2)
    assert not source.valid(action)


def test_equipment_save_failure_rolls_back_and_new_commands_are_reachable():
    pet = Pet(species='ultimate', state='live')
    pet.techniques.training = 6
    session = PracticeSession(pet, lambda _: False, training=True)
    session.page, session.tech, session.index = 'detail', 4, 1
    before = pet.techniques.to_dict()
    session.input('action', 0)
    assert pet.techniques.to_dict() == before
    assert session.message == 'ERROR AL GUARDAR'
    session.save = lambda _: True
    session.input('action', 1)
    assert 4 in pet.techniques.equipped
    session.page = 'tech'
    assert len(session.choices()) == 6


def test_user_can_train_equip_four_reload_and_select_them_in_arena():
    pet = Pet(species='ultimate', state='live')
    pet.stats['e'] = 100
    saves = []
    session = PracticeSession(pet, lambda p: saves.append(p.to_dict()) or True, training=True)

    def choose_technique(index):
        while session.index != index:
            session.input('next', 0)
        session.input('action', 0)

    for technique in (1, 3, 4):
        choose_technique(technique)
        session.input('action', 0)
        session.input('action', 0)
        assert pet.techniques.learned(technique, pet.species)
        assert technique not in pet.techniques.equipped
        session.input('next', 0)
        session.input('action', 0)
        session.input('back', 0)
        if technique == 1:
            choose_technique(2)
            session.input('next', 0)
            session.input('action', 0)
            session.input('back', 0)
    assert pet.techniques.equipped == [0, 1, 3, 4]
    assert pet.get('e') == 76
    loaded = Pet()
    loaded.load_from_dict(saves[-1])
    assert loaded.techniques.equipped == [0, 1, 3, 4]
    arena = PracticeSession(loaded, lambda _: True)
    assert len(arena.choices()) == 7
    for technique in loaded.techniques.equipped:
        arena.input('next', 0)
        assert loaded.techniques.equipped[arena.index - 1] == technique
    arena.input('next', 0)
    assert arena.choices()[arena.index] == 'MOCHILA'
    arena.input('next', 0)
    assert not arena.input('action', 0)


def test_cpp_expanded_progress_battle_and_persistence(tmp_path):
    core = ROOT / 'firmware/t-display/lib/vpet_core/src'
    binary = tmp_path / 'techniques'
    subprocess.run(['c++', '-std=c++17', '-I' + str(core),
                    str(ROOT / 'tests/technique_expansion.cpp'),
                    *[str(core / 'vpet' / (name + '.cpp')) for name in
                      ('PetState', 'Nutrition', 'SettingsStore', 'Exploration')],
                    '-o', str(binary)], check=True)
    subprocess.run([str(binary)], check=True)


def test_expanded_techniques_match_cpp_every_round(tmp_path):
    core = ROOT / 'firmware/t-display/lib/vpet_core/src'
    binary = tmp_path / 'trace'
    subprocess.run(['c++', '-std=c++17', '-I' + str(core),
                    str(ROOT / 'tests/expanded_technique_trace.cpp'), '-o', str(binary)], check=True)
    expected = []
    outcomes = {None: 0, 'VICTORIA': 1, 'DERROTA': 2, 'EMPATE': 3}
    for scenario in range(48):
        source = Fighter([1 + (scenario * 7 + i * 11) % 99 for i in range(6)],
                         equipped=(0, 1, 3, 4) if scenario % 2 else (0, 2, 3, 4),
                         mastery=[(scenario * 3 + i * 17) % 101 for i in range(5)],
                         personality=scenario % 3, bond=100, element='fire')
        target = Fighter((25, 20, 24, 20, 22, 20), personality=1,
                         element=('plant', 'water', 'fire')[scenario % 3])
        battle = PracticeBattle(source, target)
        while not battle.result:
            order = -1 if battle.round % 3 == 0 else 3 if battle.round % 2 else 4
            battle.step(order)
            expected.append(','.join(map(str, [scenario, battle.round, source.hp, source.mp,
                            target.hp, target.mp, *[-1 if a is None else a for a in battle.actions],
                            *battle.damage, source.cooldowns[3], source.cooldowns[4], outcomes[battle.result]])))
    assert subprocess.check_output([str(binary)], text=True).splitlines() == expected
