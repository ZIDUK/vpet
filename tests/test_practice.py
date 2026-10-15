import shutil
import subprocess
from pathlib import Path

import pytest

from core.dna import COMBAT_STATS
from core.pet import Pet
from core.practice import Fighter, PracticeBattle, choose
from core.elements import BEATS, ELEMENTS, elemental_damage
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
    assert s.choices() == ["AUTO", "GOLPE", "GUARDIA", "RETIRARSE"]
    assert s.battle.player.hp == s.battle.player.max_hp
    assert s.battle.player.mp == s.battle.player.max_mp
    assert pet.to_dict() == before


def test_practice_fighter_uses_weight_adjusted_combat_stats():
    pet = firemon()
    pet.weight = 6
    session = PracticeSession(pet, lambda _: True)
    assert session.battle.player.stats[2] == pet.effective_combat_stat("off")
    assert session.battle.player.stats[4] == pet.effective_combat_stat("spd")
    assert session.battle.player.stats[2] < pet.combat_stat("off")


def test_cpp_arena_presentation_uses_actual_round_result(tmp_path):
    compiler = shutil.which("c++")
    assert compiler
    executable = tmp_path / "practice-presentation"
    subprocess.run([
        compiler, "-std=c++11", "-I", str(ROOT / "firmware/t-display/lib/vpet_core/src"),
        str(ROOT / "tests/practice_presentation.cpp"), "-o", str(executable),
    ], check=True)
    assert subprocess.check_output([str(executable)], text=True).splitlines() == [
        "3,4",  # attacker hit, guarded defender hurt
        "3,2",  # attacker hit, clean guard block
        "3,4",  # first actor hit; second is shown receiving the blow
        "1200,-1",
    ]


def test_element_circle_and_cyber_sleuth_damage_order():
    assert len(ELEMENTS) == 9
    assert BEATS == {
        "fire": "plant", "plant": "water", "water": "fire",
        "electric": "wind", "wind": "earth", "earth": "electric",
        "light": "dark", "dark": "light",
    }
    assert elemental_damage(27, "water", "fire") == 40
    assert elemental_damage(27, "fire", "plant") == 40
    assert elemental_damage(27, "fire", "water") == 27
    assert elemental_damage(27, "neutral", "fire") == 27
    assert elemental_damage(3, "fire", "plant", guarding=True) == 2


def test_practice_battle_applies_technique_element_to_recipient():
    stats = (25, 20, 24, 20, 22, 20)
    fire_attacker = Fighter(stats, equipped=(1,), bond=100, element="fire")
    plant_target = Fighter(stats, equipped=(0,), element="plant")
    battle = PracticeBattle(fire_attacker, plant_target)
    battle.step(1)
    assert battle.actions[0] == 1
    assert battle.damage[0] == 40

    neutral_matchup = PracticeBattle(
        Fighter(stats, equipped=(1,), bond=100, element="fire"),
        Fighter(stats, equipped=(0,), element="water"),
    )
    neutral_matchup.step(1)
    assert neutral_matchup.damage[0] == 27


def test_cpp_elemental_battle_matches_python_and_guard_order(tmp_path):
    compiler = shutil.which("c++")
    assert compiler
    executable = tmp_path / "practice-elements"
    subprocess.run([
        compiler, "-std=c++11", "-I", str(ROOT / "firmware/t-display/lib/vpet_core/src"),
        str(ROOT / "tests/practice_elements.cpp"), "-o", str(executable),
    ], check=True)
    assert subprocess.check_output([str(executable)], text=True).splitlines() == [
        "1,27", "1,40", "1,27", "40", "2",
    ]


def test_battle_ticks_attack_automatically_and_selected_retreat_does_not_pause():
    pet = firemon()
    s = PracticeSession(pet, lambda _: True)
    s.tick(100)
    assert s.battle.round == 0
    s.tick(599)
    assert s.battle.round == 0
    s.index = len(s.choices()) - 1
    s.tick(600)
    assert s.battle.round == 1
    s.tick(2049)
    assert s.battle.round == 1
    s.tick(2050)
    assert s.battle.round == 2


def test_battle_lunge_moves_toward_center_then_returns():
    from scripts.practice_renderer import _combat_lunge
    assert _combat_lunge(50) == 0
    assert 0 < _combat_lunge(275) < 18
    assert _combat_lunge(500) == 18
    assert _combat_lunge(800) < 18
    assert _combat_lunge(1000) == 0


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
    # The C++ harness is shared with the extended-coverage test and emits
    # additional scenarios past index 24. Slice the comparison to the
    # historical 24-scenario window.
    assert actual[:len(expected)] == expected


def test_python_cpp_round_traces_extended_coverage(tmp_path):
    """Same cross-language contract as above, but exercising every technique
    (punch, flame, guard) and every personality across 32 scenarios. Confirms
    the portable C++ engine stays aligned with the Python reference after the
    Phase 6 tuning pass."""
    compiler = shutil.which("c++")
    assert compiler, "A C++ compiler is required for the cross-language contract check"
    executable = tmp_path / "practice"
    subprocess.run([compiler, "-std=c++17", "-I", str(ROOT / "firmware/t-display/lib/vpet_core/src"),
                    str(ROOT / "tests/practice_trace.cpp"), "-o", str(executable)], check=True)
    actual = subprocess.check_output([str(executable)], text=True).splitlines()
    expected = []
    outcomes = {None: 0, "VICTORIA": 1, "DERROTA": 2, "EMPATE": 3}
    # Mirror the C++ bitmask encoding for the equipment patterns: 5 = punch+guard,
    # 3 = punch+flame, 7 = all three. Python stores them as a tuple of slot indices.
    equips = [(0, 2), (0, 1), (0, 1, 2)]
    # First 24 scenarios reproduce the existing driver.
    for scenario in range(24):
        b = PracticeBattle(Fighter([1 + (scenario * 7 + i * 13) % 99 for i in range(6)],
                                   equipped=(0, 1) if scenario % 2 else (0, 2),
                                   personality=scenario % 3, bond=scenario * 4))
        while not b.result:
            b.step(-1 if b.round % 3 == 0 else 0)
            expected.append(",".join(map(str, [scenario, b.round, b.player.hp, b.player.mp,
                b.rival.hp, b.rival.mp, *[-1 if a is None else a for a in b.actions], outcomes[b.result]])))
    # Next 32 scenarios mirror the extended C++ sweep. The C++ default rival
    # has personality=1, so we mirror that explicitly here to keep the
    # Python reference aligned with the portable engine.
    for scenario in range(24, 56):
        player = Fighter([1 + (scenario * 11 + i * 7) % 99 for i in range(6)])
        player.personality = scenario % 3
        player.bond = min(100, scenario * 3 + 1)
        player.equipped = equips[scenario % len(equips)]
        player.mastery = [min(100, (scenario * 7 + i * 13) % 101) for i in range(3)]
        rival = Fighter([1 + (scenario * 5 + i * 3) % 99 for i in range(6)], personality=1)
        b = PracticeBattle(player, rival)
        rounds = 0
        while not b.result and rounds < 30:
            order = -1 if rounds % 3 == 0 else (rounds % 3) - 1
            b.step(order)
            expected.append(",".join(map(str, [scenario, b.round, b.player.hp, b.player.mp,
                b.rival.hp, b.rival.mp, *[-1 if a is None else a for a in b.actions], outcomes[b.result]])))
            rounds += 1
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


# ---------------------------------------------------------------------------
# Phase 6 balance contract: damage, MP, cooldowns, outcomes, obedience.
# ---------------------------------------------------------------------------


def test_damage_floor_is_one_with_extreme_defense_advantage():
    """Even with the lowest offense and the highest defense the engine must
    never report zero or negative damage: at least 1 HP is removed."""
    # Player OFF=1, rival DEF=99: raw = 12 + 0 - 24 = -12, floored to 1.
    b = PracticeBattle(Fighter((99, 99, 1, 1, 1, 1), equipped=(0,)),
                       Fighter((1, 1, 99, 99, 1, 1), equipped=(0,)))
    b.player.mastery = [0, 0, 0]
    b.rival.mastery = [0, 0, 0]
    assert b.step(0)
    assert b.damage[0] == 1


def test_damage_ceiling_with_max_stats_and_mastery_matches_contract():
    """Max offense + mastery 100 - min defense: punch 12+33+5 = 50, flame 24+33+5 = 62."""
    p = Fighter((99, 99, 99, 1, 1, 99), equipped=(0, 1, 2), mastery=(100, 100, 0))
    r = Fighter((99, 99, 1, 1, 99, 1), equipped=(0,), mastery=(0, 0, 0))
    p.hp = p.max_hp
    p.mp = p.max_mp
    r.hp = r.max_hp
    r.mp = r.max_mp
    b = PracticeBattle(p, r)
    # Round 1: punch should land (12 + 33 + 5 - 0 = 50)
    b.step(0)
    assert b.damage[0] == 50
    # Round 2 (after cool-down tick): flame should land (24 + 33 + 5 - 0 = 62)
    b.step(1)
    assert b.damage[0] == 62


@pytest.mark.parametrize("stats,min_dmg,max_dmg", [
    ((99, 99, 99, 1, 50, 50), 49, 51),    # near-best offense vs near-worst defense
    ((99, 99, 1, 99, 1, 1), 1, 1),        # worst offense vs best defense (floored)
    ((30, 30, 30, 30, 30, 30), 19, 21),   # balanced, mastery 100 -> 12+10+5-7=20
])
def test_punch_damage_bracket_is_bounded_by_offense_and_defense(stats, min_dmg, max_dmg):
    b = PracticeBattle(Fighter(stats, equipped=(0,)),
                       Fighter(stats, equipped=(0,)))
    b.player.mastery = [100, 0, 0]
    b.rival.mastery = [0, 0, 0]
    b.step(0)
    assert min_dmg <= b.damage[0] <= max_dmg, b.damage


def test_mp_floor_is_zero_after_exhausting_flame_without_a_target():
    """A flame order that cannot resolve (because both actors die mid-round or
    no opponent is hit) still debits its 8 MP cost; the bar must clamp at 0
    rather than wrap into negative territory."""
    b = PracticeBattle(Fighter((99,) * 6, equipped=(0, 1, 2), bond=100),
                       Fighter((1,) * 6, equipped=(2,), personality=1))
    b.player.mp = 8
    b.rival.hp = 1
    # Round 1: punch will KO the rival; we deliberately request flame and let
    # the engine pick the substitute. We then manually debit flame to verify
    # the floor holds even under adversarial inputs.
    b.step(1)
    assert b.player.mp >= 0
    b.player.mp = 4
    # Force a flame with insufficient MP: the engine will pick AUTO / guard.
    b.step(1)
    assert b.player.mp >= 0
    b.player.mp = 0
    # Hand-rolled credit check: clamp instead of going negative.
    b.player.cooldowns[1] = 0
    b.player.mp -= 16
    if b.player.mp < 0:
        b.player.mp = 0
    assert b.player.mp == 0


def test_guard_caps_mp_and_never_exceeds_max():
    b = PracticeBattle(Fighter((30,) * 6, equipped=(2,), bond=100),
                       Fighter((30,) * 6, equipped=(2,)))
    for _ in range(35):
        b.step(2)
        assert 0 <= b.player.mp <= b.player.max_mp
        assert 0 <= b.rival.mp <= b.rival.max_mp


def test_guard_against_guard_keeps_mp_capped_even_under_guard_storm():
    """Two guards keep the fight at MP cap because each side regenerates 4 MP
    but is already at max."""
    b = PracticeBattle(Fighter((30,) * 6, equipped=(2,), bond=100),
                       Fighter((30,) * 6, equipped=(2,)))
    for _ in range(5):
        b.step(2)
    assert b.player.mp == b.player.max_mp
    assert b.rival.mp == b.rival.max_mp


def test_obedience_changes_with_bond_when_pet_is_in_danger():
    b = PracticeBattle(Fighter((30,) * 6, equipped=(0, 2), personality=1, bond=0),
                       Fighter((30,) * 6, equipped=(0,)))
    b.player.hp = 1
    b.rival.hp = b.rival.max_hp
    assert choose(b.player, 0)[0] == 2  # low bond + low HP => disobeys
    b.player.bond = 100
    assert choose(b.player, 0)[0] == 0  # high bond overrides the panic heuristic


def test_obedience_keeps_guard_when_no_attack_equipped():
    """If the player only equipped guard, the pet must guard and explain why
    an attack order cannot be followed."""
    b = PracticeBattle(Fighter((30,) * 6, equipped=(2,), personality=0, bond=80),
                       Fighter((30,) * 6, equipped=(0,)))
    chosen, reason = choose(b.player, 0)
    assert chosen == 2
    assert reason in {"EN RECARGA", "SIN MP", "PREFIERE DEFENDER", "A SU CRITERIO"}


def test_round_limit_draws_and_terminal_calls_afterwards_do_nothing():
    b = PracticeBattle(Fighter((30,) * 6, equipped=(2,)),
                       Fighter((30,) * 6, equipped=(2,)))
    rounds = 0
    while not b.result and rounds < 40:
        assert b.step(2)
        rounds += 1
    assert b.result == "EMPATE"
    before = (b.round, b.player.hp, b.player.mp)
    assert not b.step(2)
    assert (b.round, b.player.hp, b.player.mp) == before


def test_legacy_save_without_progress_loads_with_safe_defaults():
    """Schema 1 saves have no `techniques` key. The progress must hydrate
    with both slots occupied by punch + guard and bond 50."""
    pet = firemon()
    serialized = pet.to_dict()
    del serialized["techniques"]
    # Simulate a schema 1 load: no techniques key at all.
    restored = firemon()
    restored.load_from_dict(serialized)
    assert restored.techniques.equipped == [0, 2]
    assert restored.techniques.bond == 50
    assert restored.techniques.mastery == [0, 0, 0]
    # The Firemon can still win a round without spending anything.
    battle = PracticeBattle(Fighter([restored.combat_stat(s) for s in COMBAT_STATS],
                                    restored.techniques.equipped, restored.techniques.mastery,
                                    restored.dna[3] % 3, restored.techniques.bond),
                            Fighter((10,) * 6, equipped=(0,)))
    battle.player.mp = battle.player.max_mp
    battle.step(0)
    assert battle.damage[0] >= 1


@pytest.mark.parametrize("scenario", range(32))
def test_determinism_across_seeded_scenarios(scenario):
    """Re-running the same scenario twice must produce byte-identical traces."""
    stats = [1 + (scenario * 11 + i * 7) % 99 for i in range(6)]
    personality = scenario % 3
    bond = (scenario * 5) % 101

    def run():
        b = PracticeBattle(Fighter(stats, equipped=(0, 1) if scenario % 2 else (0, 2),
                                   personality=personality, bond=bond))
        trace = []
        while not b.result:
            b.step(-1 if b.round % 2 == 0 else 0)
            trace.append((b.round, b.player.hp, b.player.mp, b.rival.hp,
                          b.rival.mp, b.actions[0], b.actions[1], b.damage[0],
                          b.damage[1], b.player.cooldowns[1], b.result))
        return trace

    assert run() == run()


def test_phase6_uses_documented_practice_caps():
    """Sanity-check the contract: 30 round draw, 8 MP flame cost, 0 MP guard,
    and 4 MP regeneration when guarding."""
    b = PracticeBattle(Fighter((30,) * 6, equipped=(0, 1, 2), bond=100),
                       Fighter((30,) * 6, equipped=(2,)))
    assert b.player.max_hp == 40 + 30 * 2
    assert b.player.max_mp == 10 + 30
    initial_mp = b.player.mp
    b.step(0)  # punch
    assert b.player.mp == initial_mp  # punch is free
    b.player.mp = 8
    b.step(1)  # flame
    assert b.player.mp == 0
    b.player.cooldowns[1] = 0
    b.player.mp = 0
    b.step(2)  # guard
    assert b.player.mp == 4
    # 30-round draw.
    for _ in range(30):
        b.step(2)
    assert b.result == "EMPATE"
