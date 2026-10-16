"""Compile the portable board domain and compare rewards with the simulator."""
import subprocess
from pathlib import Path

import pytest

from core.pet import Pet

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "firmware/t-display/lib/vpet_core/src"
NOW = 1791979200


@pytest.fixture(scope="module")
def exploration_binary(tmp_path_factory):
    binary = tmp_path_factory.mktemp("exploration") / "board"
    subprocess.run(["c++", "-std=c++11", "-Wall", "-Wextra", "-I" + str(CORE),
                    str(ROOT / "tests/exploration_board.cpp"),
                    *[str(CORE / "vpet" / name) for name in
                      ("Exploration.cpp", "PetState.cpp", "Nutrition.cpp", "SettingsStore.cpp")],
                    "-o", str(binary)], check=True, capture_output=True, text=True)
    return binary


@pytest.mark.parametrize("case", ["rules", "codec", "persistence", "training", "interruptions"])
def test_exploration_contract(exploration_binary, case):
    result = subprocess.run([str(exploration_binary), case], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("route", ["patio", "jornada", "noche"])
@pytest.mark.parametrize("elapsed", [0, 900, 1799, 1800, 14399, 14400, 28799, 28800, 999999])
@pytest.mark.parametrize("good", [False, True])
@pytest.mark.parametrize("profile", ["fresh", "capped", "mastery"])
def test_python_reward_vectors(exploration_binary, route, elapsed, good, profile):
    p = Pet(species="rookie", state="live")
    p.stats.update(h=70 if good else 0, e=70, p=70)
    if profile == "capped":
        p.ev["off"] = 251
        p.exploration.week = (NOW + 259200) // 604800
        p.exploration.week_ev = 7
        p.exploration.guide = True
        p.techniques.training = 2
        p.techniques.mastery[1] = 99
    elif profile == "mastery":
        p.techniques.training = 2
        p.exploration.week = (NOW + 259200) // 604800
        p.exploration.week_mastery = 3
    assert p.exploration.start(p, route, "off", NOW)
    reward = p.exploration.preview(p, NOW + elapsed)
    result = subprocess.run([str(exploration_binary), "vector", route, str(elapsed), str(int(good)), profile],
                            capture_output=True, text=True, check=True)
    fields = ("elapsed", "full", "energy", "ev", "mastery", "learning", "guide", "learned")
    assert list(map(int, result.stdout.split())) == [int(reward[key]) for key in fields]
