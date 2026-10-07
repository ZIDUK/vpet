import shutil
import subprocess
from pathlib import Path

import pytest

from core.pet import Pet
from core.practice import Fighter, PracticeBattle, choose
from core.techniques import TechniqueProgress
from scripts.practice_session import PracticeSession

ROOT = Path(__file__).resolve().parents[1]


def firemon():
    pet = Pet()
    pet.complete_hatch("rookie", entropy=12345)
    return pet


def test_battle_entry_starts_at_round_zero_without_spending_or_saving():
    pet = firemon()
    before = pet.to_dict()
    s = PracticeSession(pet, lambda _: pytest.fail("Opening battle must not save"))
    assert s.page == "battle"
    assert s.battle.round == 0
    assert s.choices() == ["A TU CRITERIO", "GOLPE", "GUARDIA", "RETIRARSE"]
    assert s.battle.player.hp == s.battle.player.max_hp
    assert s.battle.player.mp == s.battle.player.max_mp
    assert pet.to_dict() == before


@pytest.mark.parametrize("result", [None, "VICTORIA", "DERROTA", "EMPATE"])
def test_battle_exit_returns_home_without_preparation_menu(result):
    s = PracticeSession(firemon(), lambda _: True)
    assert s.page == "battle"
    s.battle.result = result
    s.index = len(s.choices()) - 1
    assert not s.input("action", 0)


def test_old_save_and_roundtrip_keep_genome_and_progress():
    pet = firemon()
    old = pet.to_dict()
    old.pop("techniques")
    other = Pet()
    other.load_from_dict(old)
    assert other.dna == pet.dna
    assert other.techniques.equipped == [0, 2]
    assert other.techniques.train(other, 1)
    assert not other.techniques.learned(1)
    assert other.techniques.train(other, 1)
    assert other.techniques.learned(1)
    assert other.techniques.equip(1)
    loaded = Pet()
    loaded.load_from_dict(other.to_dict())
    assert loaded.techniques.to_dict() == other.techniques.to_dict()
    assert loaded.dna == pet.dna
    loaded.reset_after_evolution()
    assert loaded.techniques.learned(1)
    loaded.reset_to_egg()
    assert not loaded.techniques.learned(1)


@pytest.mark.parametrize("data", [None, [], {"equipped": None, "mastery": []},
                                {"training": -1, "equipped": ["flame", "unknown"]},
                                {"version": 999}])
def test_progress_sanitizes_missing_invalid_and_unknown_data(data):
    progress = TechniqueProgress(data)
    assert progress.equipped
    assert all(progress.learned(i) for i in progress.equipped)
    assert not progress.equip(99)


def test_invalid_order_does_not_advance_or_spend():
    b = PracticeBattle(Fighter([30] * 6, equipped=(0, 2)))
    assert not b.step(1)
    assert not b.step(99)
    assert b.round == 0 and b.player.mp == 40


def test_flame_cooldown_blocks_one_full_round_and_mp_never_negative():
    b = PracticeBattle(Fighter([99] * 6, bond=100))
    b.rival.hp = b.rival.max_hp = 1000
    b.step(1)
    assert b.actions[0] == 1 and b.player.mp == 101
    b.step(1)
    assert b.actions[0] != 1 and b.reason == "EN RECARGA"
    b.step(1)
    assert b.actions[0] == 1
    b.player.mp = 0
    b.player.cooldowns[1] = 0
    b.step(1)
    assert b.reason == "SIN MP" and b.player.mp >= 0


def test_dead_actor_cannot_attack_and_result_is_terminal():
    b = PracticeBattle(Fighter([99] * 6, bond=100))
    b.rival.hp = 1
    assert b.step(0)
    assert b.result == "VICTORIA" and b.actions[1] is None
    before = b.player.hp
    assert not b.step(0)
    assert b.round == 1 and b.player.hp == before


def test_personality_and_bond_change_choice_reproducibly():
    cautious = Fighter([30] * 6, personality=1, bond=0)
    cautious.hp = 1
    assert choose(cautious, 0)[0] == 2
    cautious.bond = 100
    assert choose(cautious, 0)[0] == 0
    cautious.hp = cautious.max_hp
    cautious.equipped = (0, 2)
    cautious.bond = 0
    assert choose(cautious)[0] == 2
    cautious.personality = 0
    assert choose(cautious)[0] == 0


def test_practice_rewards_once_and_does_not_change_care_or_official_counters():
    pet = firemon()
    saves = []
    s = PracticeSession(pet, lambda p: saves.append(p.to_dict()) or True)
    initial = (pet.dp, pet.battles_won, pet.battles_lost, dict(pet.stats))
    while not s.battle.result:
        s.index = 1
        s.input("action", 0)
    assert len(saves) == 1
    assert initial == (pet.dp, pet.battles_won, pet.battles_lost, pet.stats)
    assert not s.input("action", 1)
    assert len(saves) == 1


def test_retreat_and_held_back_do_not_award_progress():
    pet = firemon()
    s = PracticeSession(pet, lambda _: pytest.fail("Retreat must not save rewards"))
    s.index = 1
    s.input("action", 0)
    s.input("back", 0)
    assert s.page == "battle"
    s.index = len(s.choices()) - 1
    assert not s.input("action", 0)
    assert pet.techniques.mastery == [0, 0, 0]


def test_python_cpp_round_traces_match(tmp_path):
    compiler = shutil.which("c++")
    assert compiler, "A C++ compiler is required for the cross-language contract check"
    executable = tmp_path / "practice"
    subprocess.run([compiler, "-std=c++17", "-I", str(ROOT / "firmware/t-display/lib/vpet_core/src"),
                    str(ROOT / "tests/practice_trace.cpp"), "-o", str(executable)], check=True)
    actual = subprocess.check_output([str(executable)], text=True).splitlines()
    expected = []
    outcomes = {None: 0, "VICTORIA": 1, "DERROTA": 2, "EMPATE": 3}
    for scenario in range(24):
        b = PracticeBattle(Fighter([1 + (scenario * 7 + i * 13) % 99 for i in range(6)],
                                   equipped=(0, 1) if scenario % 2 else (0, 2),
                                   personality=scenario % 3, bond=scenario * 4))
        while not b.result:
            b.step(-1 if b.round % 3 == 0 else 0)
            expected.append(",".join(map(str, [scenario, b.round, b.player.hp, b.player.mp,
                b.rival.hp, b.rival.mp, *[-1 if a is None else a for a in b.actions], outcomes[b.result]])))
    assert actual == expected


def test_guard_halves_damage_and_restores_mp_with_cap():
    b = PracticeBattle(Fighter([30] * 6, equipped=(2,), bond=100),
                       Fighter([30] * 6, equipped=(0,)))
    b.player.mp = b.player.max_mp - 1
    b.step(2)
    assert b.damage[1] == (12 + 30 // 3 - 30 // 4) // 2
    assert b.player.mp == b.player.max_mp


def test_guard_only_encounter_draws_at_thirty_rounds():
    b = PracticeBattle(Fighter([30] * 6, equipped=(2,)), Fighter([30] * 6, equipped=(2,)))
    for _ in range(30):
        assert b.step(2)
        assert b.player.mp <= b.player.max_mp
    assert b.result == "EMPATE" and not b.step(2)


def test_equal_speed_alternates_first_actor():
    b = PracticeBattle(Fighter([30] * 6, equipped=(0,)), Fighter([30] * 6, equipped=(0,)))
    b.step(0)
    b.player.hp = b.rival.hp = 1
    b.step(0)
    assert b.result == "DERROTA" and b.actions == (None, 0)


def test_session_keeps_requested_order_separate_from_executed_action():
    pet = firemon()
    pet.techniques.training = 2
    pet.techniques.equipped = [0, 1]
    s = PracticeSession(pet, lambda _: True)
    s.battle.player.mp = 0
    s.index = 2
    s.input("action", 1000)
    assert s.last_order == 1
    assert s.battle.actions[0] != s.last_order
    assert s.battle.reason == "SIN MP"
    s.input("next", 1100)
    assert s.last_order == 1  # browsing does not replace the previous order
    s.index = len(s.choices()) - 1
    assert not s.input("action", 1200)
    fresh = PracticeSession(pet, lambda _: True)
    assert fresh.last_order is None and fresh.battle.round == 0


def test_detail_back_preserves_catalog_selection_and_equip_label():
    s = PracticeSession(firemon(), lambda _: True, training=True)
    s.input("next", 0)
    s.input("next", 0)
    s.input("action", 0)
    assert s.choices() == ["ENTRENAR", "QUITAR", "VOLVER"]
    s.input("next", 0)
    s.input("action", 0)
    assert s.choices()[1] == "EQUIPAR"
    s.input("back", 0)
    assert (s.page, s.index) == ("tech", 2)


def test_training_feedback_distinguishes_unlock_progress_and_exhaustion():
    s = PracticeSession(firemon(), lambda _: True, training=True)
    s.input("next", 0)
    s.input("action", 0)
    s.input("action", 0)
    assert s.message == "ENTRENAMIENTO 1/2"
    s.input("action", 0)
    assert s.message == "LLAMA APRENDIDA"
    s.pet.stats["e"] = 0
    s.input("action", 0)
    assert s.message == "FALTA ENERGIA"
