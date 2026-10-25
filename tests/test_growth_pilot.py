"""Opt-in balance experiment; never changes the running pet formula."""
import copy
import json
from pathlib import Path
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_growth_anchor_points_and_half_up_rounding():
    from core.growth_pilot import point
    assert [point(10, 252, r)["cap"] for r in (1, 2, 3)] == [93, 187, 280]
    assert [point(0, 252, r)["cap"] for r in (1, 2, 3)] == [67, 133, 200]
    assert [point(15, 252, r)["cap"] for r in (1, 2, 3)] == [107, 213, 320]
    assert [point(10, 0, r)["cap_ev"] for r in (1, 2, 3)] == [84, 168, 252]
    assert point(1, 0, 2)["base"] == 16
    assert point(1, 0, 1, ranks=2)["cap"] == 104


@pytest.mark.parametrize("args", [(True, 0, 1), (16, 0, 1), (-1, 0, 1),
    (0, -1, 1), (0, 253, 1), (0, 1.5, 1), (0, 0, 0), (0, 0, 4),
    (0, 0, 1, 0), (0, 0, 1, 4), (0, 0, 2, 1)])
def test_growth_rejects_outside_supported_profile(args):
    from core.growth_pilot import point
    with pytest.raises(ValueError):
        point(*args)


def test_growth_monotonicity_and_no_silent_legacy_stat_loss():
    from core.growth_pilot import point
    from core.dna import legacy_combat_stat as combat_stat
    for iv in range(16):
        for ev in range(253):
            previous = 0
            for rank, role in enumerate(("rookie", "champion", "ultimate"), 1):
                p = point(iv, ev, rank)
                legacy = combat_stat([iv, 0, 0, 1], {"hp": ev}, "hp", role)
                assert legacy <= p["stat"] <= p["cap"]
                assert p["stat"] >= previous
                assert p["stored_ev"] == ev
                if ev < p["cap_ev"]:
                    assert point(iv, ev + 1, rank)["stat"] >= p["stat"]
                if iv < 15:
                    assert point(iv + 1, ev, rank)["stat"] >= p["stat"]
                previous = p["stat"]


def test_training_partial_bonus_and_legacy_over_cap_are_non_destructive():
    from core.growth_pilot import project_training
    partial = project_training(10, 82, 1)
    assert (partial["ev_added"], partial["after"]["stored_ev"], partial["energy_cost"]) == (2, 84, 8)
    assert project_training(10, 77, 1, requested=7)["after"]["stored_ev"] == 84
    for ev in (84, 168, 252):
        blocked = project_training(10, ev, 1)
        assert blocked["ev_added"] == blocked["energy_cost"] == 0
        assert blocked["before"] == blocked["after"]
        assert blocked["after"]["stored_ev"] == ev
    assert project_training(10, 84, 2)["ev_added"] == 6
    for invalid in (0, -1, 253, True, 1.5):
        with pytest.raises(ValueError):
            project_training(10, 0, 1, requested=invalid)


def test_cpp_candidate_matches_every_point_and_training_projection(tmp_path):
    from core.growth_pilot import point, project_training
    binary = tmp_path / "growth"
    core = ROOT / "firmware/t-display/lib/vpet_core/src"
    subprocess.run(["c++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
                    "-I" + str(core), str(ROOT / "tests/growth_pilot_trace.cpp"),
                    "-o", str(binary)], check=True)
    rows = subprocess.check_output([str(binary)], text=True).splitlines()
    expected = []
    for ranks in (1, 2, 3):
        for rank in range(1, ranks + 1):
            for iv in range(16):
                for ev in range(253):
                    p = point(iv, ev, rank, ranks)
                    for gain in (1, 6, 7, 252):
                        t = project_training(iv, ev, rank, gain, ranks)
                        expected.append(" ".join(map(str, (p["base"], p["cap"], p["cap_ev"],
                            p["stat"], p["active_ev"], p["stored_ev"], t["ev_added"],
                            t["energy_cost"], t["after"]["stat"], t["after"]["stored_ev"]))))
    assert rows == expected
    from scripts.growth_pilot import run_battle
    for player, rival in (((320,) * 6, (320,) * 6), ((264,) * 6, (25, 20, 24, 20, 22, 20)),
                          ((1,) * 6, (320,) * 6), ((320, 1, 1, 320, 1, 1),) * 2):
        trace = subprocess.check_output([str(binary), "battle"],
                                        input=" ".join(map(str, (*player, *rival))), text=True)
        actual = [list(map(int, row.split())) for row in trace.splitlines()]
        assert actual == run_battle(player, rival)["trace"]


def test_report_reproducible_and_budget_means_active_time_not_wall_clock():
    from scripts.growth_pilot import build_report
    report = build_report()
    assert json.dumps(report, sort_keys=True) == json.dumps(build_report(), sort_keys=True)
    assert report["activated"] is True
    assert report["activation_scope"] == "local-code-not-board"
    assert report["matrix"]["points"] == 16 * 253 * 3
    assert report["matrix"]["legacy_stat_losses"] == 0
    assert report["matrix"]["evolution_losses"] == 0
    budgets = report["training"]
    assert [b["from_zero"]["reps"] for b in budgets] == [14, 28, 42]
    assert [b["from_previous_cap"]["reps"] for b in budgets] == [14, 14, 14]
    assert budgets[0]["from_zero"]["energy"] == 112
    assert budgets[0]["from_zero"]["active_ms"] == 140000
    assert budgets[2]["all_six_from_zero"]["energy"] == 2016
    assert report["item_probe"]["boost_reduces_candidate"] is False
    assert report["item_probe"]["recovery_stays_bounded"] is True
    assert all(1 <= b["rounds"] <= 30 and b["max_hp"] <= 680 for b in report["battles"])
    assert any(b["result"] == "EMPATE" for b in report["battles"])


def test_audit_does_not_mutate_pet_save_or_activate_new_formula():
    from scripts.growth_pilot import audit_pet, sandbox_fighter
    from core.pet import Pet, STATE_LIVE
    from core.practice import Fighter
    pet = Pet(species="rookie", state=STATE_LIVE)
    pet.restore_dna((0xAF, 0x38, 0xE1, 0x72))
    pet.restore_ev({s: 252 for s in ("hp", "mp", "off", "def", "spd", "brn")})
    before = copy.deepcopy(pet.to_dict())
    rows = audit_pet(pet)
    assert pet.to_dict() == before
    assert len(rows) == 6 and rows[0]["stored_ev"] == 252
    assert pet.combat_stat("hp") == 107
    assert Fighter((320,) * 6).stats == (320,) * 6
    assert sandbox_fighter((320,) * 6).max_hp == 680
    assert sandbox_fighter((320,) * 6).max_mp == 330
    for role in ("egg", "baby"):
        pet.species = role
        before = copy.deepcopy(pet.to_dict())
        with pytest.raises(ValueError):
            audit_pet(pet)
        assert pet.to_dict() == before


@pytest.mark.parametrize("stats", [(), (0,) * 6, (321,) * 6, (True,) * 6, (1.5,) * 6])
def test_sandbox_rejects_invalid_stats(stats):
    from scripts.growth_pilot import sandbox_fighter
    with pytest.raises(ValueError):
        sandbox_fighter(stats)


def test_cli_writes_only_requested_report_directory(tmp_path):
    out = tmp_path / "report"
    subprocess.run([str(ROOT / ".venv-platformio/bin/python"),
                    str(ROOT / "scripts/growth_pilot.py"), "--out", str(out)], check=True)
    assert sorted(p.name for p in out.iterdir()) == ["battles.csv", "report.json", "stats.csv"]
    report = json.loads((out / "report.json").read_text())
    assert len((out / "stats.csv").read_text().splitlines()) == 12145
    assert len((out / "battles.csv").read_text().splitlines()) == len(report["battles"]) + 1
