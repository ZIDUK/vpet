"""Production growth, not a sandbox fighter or a rewritten battle engine."""
import copy
from pathlib import Path
import subprocess

import pytest
from core.pet import Pet, STATE_LIVE
from core.dna import COMBAT_STATS
from core.training import batch_apply, batch_commit, batch_projected_value, BatchSaveError
from core.adopted_items import use_care_item, use_combat_item
from core.practice import Fighter

ROOT = Path(__file__).resolve().parents[1]


def pet(role="rookie", ev=0):
    p = Pet(species=role, state=STATE_LIVE)
    p.restore_dna((0xFA, 0x38, 0xE1, 0x72))
    p.restore_ev({s: ev for s in COMBAT_STATS})
    p.stats.update(e=100, h=80, p=80, hp=100)
    p.weight = {"rookie": 10, "champion": 20, "ultimate": 35}.get(role, 5)
    return p


@pytest.mark.parametrize("role,cap,ceiling", [("rookie", 84, 93), ("champion", 168, 187), ("ultimate", 252, 280)])
def test_real_pet_stat_and_ev_caps(role, cap, ceiling):
    p = pet(role, 252)
    assert p.ev_limit() == cap
    assert p.stat_limit("hp") == ceiling
    assert p.combat_stat("hp") == ceiling
    dna = list(p.dna)
    p.gain_ev("hp", 8)
    assert p.ev_at("hp") == 252 and p.dna == dna
    saved = copy.deepcopy(p.to_dict())
    restored = Pet()
    restored.load_from_dict(saved)
    assert restored.ev == p.ev and restored.dna == p.dna
    assert restored.combat_stat("hp") == ceiling


def test_each_stat_uses_own_gene_and_evolution_unlocks_without_reset():
    p = pet(ev=84)
    assert p.combat_stat("hp") != p.combat_stat("mp")
    original = list(p.dna)
    p.gain_ev("spd", 9)
    assert p.ev_at("spd") == 84
    p.species = "champion"
    p.gain_ev("spd", 9)
    assert p.ev_at("spd") == 93 and p.dna == original


def test_partial_batch_costs_only_real_rep_and_does_not_waste_bonus():
    p = pet(ev=82)
    p.adopted_inventory["training_manual"] = 1
    before, after = batch_projected_value(p, "hp", 7)
    assert after > before and after == 40 + p.stat_limit("hp") * 2
    summary = batch_apply(p, "hp", 12)
    assert summary["reps"] == 1 and summary["ev_added"] == 2
    assert summary["energy_charged"] == 8 and p.get("e") == 92
    assert p.adopted_inventory["training_manual"] == 1
    snapshot = p.to_dict()
    assert batch_apply(p, "hp", 12)["energy_charged"] == 0
    assert p.to_dict() == snapshot


def test_partial_training_save_failure_restores_legacy_snapshot_and_bonus():
    p = pet(ev=80)
    p.ev["off"] = 252
    p.adopted_inventory["training_manual"] = 1
    before = p.to_dict()
    with pytest.raises(BatchSaveError):
        batch_commit(p, "hp", 1, lambda _: False)
    assert p.to_dict() == before
    result = batch_commit(p, "hp", 1, lambda _: True)
    assert result["ev_added"] == 4
    assert p.ev_at("off") == 252


def test_chip_and_guide_not_consumed_when_stage_is_full():
    p = pet(ev=84)
    stock = {"off_chip": 1}
    assert not use_care_item(p, stock, "off_chip") and stock["off_chip"] == 1
    p.exploration.guide = True
    assert p.exploration.use_guide(p, "off") == 0 and p.exploration.guide
    p.species = "champion"
    assert use_care_item(p, stock, "off_chip") and p.ev_at("off") > 84


def test_exploration_receipt_never_has_negative_or_unearned_ev():
    for ev in (83, 84, 200, 252):
        p = pet(ev=ev)
        assert p.exploration.start(p, "jornada", "off", 100000)
        reward = p.exploration.preview(p, 128800)
        assert reward["ev"] == (1 if ev == 83 else 0)
        assert p.exploration.claim(p, 128800)["ev"] == reward["ev"]
        assert p.ev_at("off") == max(ev, 84)
        assert p.exploration.claim(p, 128800) is None


def test_all_incoming_ev_sources_obey_stage_cap_and_never_reduce_legacy():
    p = pet(ev=83)
    for stat in COMBAT_STATS:
        p.gain_ev(stat, 20)
        assert p.ev_at(stat) == 84
        p.ev[stat] = 200
        p.gain_ev(stat, 1)
        assert p.ev_at(stat) == 200


def test_boosts_keep_wide_base_replace_without_stacking_and_recover_wide_pools():
    fighter = Fighter((320,) * 6)
    assert fighter.stats == (320,) * 6
    assert (fighter.max_hp, fighter.max_mp) == (680, 330)
    stock = {"off_disk": 2, "super_off_disk": 2, "super_recovery": 2}
    assert use_combat_item(fighter, stock, "off_disk") and fighter.stats[2] == 384
    assert not use_combat_item(fighter, stock, "off_disk") and stock["off_disk"] == 1
    assert use_combat_item(fighter, stock, "super_off_disk") and fighter.stats[2] == 448
    assert not use_combat_item(fighter, stock, "off_disk")
    fighter.hp = 1
    assert use_combat_item(fighter, stock, "super_recovery") and fighter.hp == 680
    assert not use_combat_item(fighter, stock, "super_recovery")


def test_weight_penalties_are_wide_and_do_not_change_genes_or_base():
    p = pet("ultimate", 252)
    p.weight = 70
    before = p.combat_stat("hp")
    assert before == 280 and p.effective_combat_stat("hp") == 280
    assert 99 < p.effective_combat_stat("mp") <= 320
    assert 0 < p.effective_combat_stat("spd") < p.combat_stat("spd")


def test_arena_rival_scales_by_stage_not_player_training():
    from scripts.practice_session import PracticeSession
    a, b = pet(), pet("ultimate")
    first = PracticeSession(a, lambda _: True).battle.rival.stats
    high = PracticeSession(b, lambda _: True).battle.rival.stats
    assert high[0] > first[0]
    a.restore_ev({s: 84 for s in COMBAT_STATS})
    assert PracticeSession(a, lambda _: True).battle.rival.stats == first


def test_legacy_exp_item_does_not_consume_when_effort_and_stage_ev_full():
    from core.inventory import use_inventory_item
    p = pet(ev=84)
    p.effort = 100
    before = p.to_dict()
    assert use_inventory_item(p, 2) == "blocked"
    assert p.to_dict() == before


def test_training_at_stage_cap_never_calls_save_or_spends():
    p = pet(ev=84)
    before = p.to_dict()
    result = batch_commit(p, "off", 1, lambda _: pytest.fail("No-op must not save"))
    assert result["reps"] == 0 and p.to_dict() == before


def test_production_cpp_matches_python_stats_caps_and_gains(tmp_path):
    from core.growth_pilot import point
    from core.dna import combat_stat
    binary = tmp_path / "growth-live"
    core = ROOT / "firmware/t-display/lib/vpet_core/src"
    subprocess.run(["c++", "-std=c++17", "-I" + str(core),
                    str(ROOT / "tests/growth_integration.cpp"),
                    str(core / "vpet/PetState.cpp"), str(core / "vpet/Nutrition.cpp"),
                    str(core / "vpet/SettingsStore.cpp"),
                    "-o", str(binary)], check=True)
    rows = subprocess.check_output([str(binary)], text=True).splitlines()
    expected = []
    for rank in (1, 2, 3):
        for iv in range(16):
            for ev in range(253):
                p = point(iv, ev, rank)
                for index, stat in enumerate(COMBAT_STATS):
                    dna = [0, 0, 0, 1]
                    dna[index // 2] = iv << (4 * (index % 2))
                    assert combat_stat(dna, {stat: ev}, stat,
                                       ("rookie", "champion", "ultimate")[rank - 1]) == p["stat"]
                after = max(ev, min(p["cap_ev"], ev + 6))
                expected.append(f'{p["stat"]} {p["cap"]} {p["cap_ev"]} {after}')
    assert rows == expected
