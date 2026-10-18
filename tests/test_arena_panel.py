import subprocess
import sys
from pathlib import Path

import pytest

from scripts import build, build_tdisplay

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def arena_binary(tmp_path_factory):
    root = tmp_path_factory.mktemp("arena-panel")
    sim, data, include = root / "sim", root / "data", root / "include"
    build.main(profile_name="tdisplay", output_dir=sim)
    build_tdisplay.build(ROOT, sim, data, include / "generated")
    binary = root / "arena-panel"
    core = ROOT / "firmware/t-display/lib/vpet_core/src"
    subprocess.run([
        "c++", "-std=c++17", "-O1", "-ffunction-sections", "-fdata-sections",
        "-Wl,-dead_strip" if sys.platform == "darwin" else "-Wl,--gc-sections",
        "-I" + str(ROOT / "tests/asset_stubs"), "-I" + str(include),
        "-I" + str(ROOT / "firmware/t-display/include"), "-I" + str(core),
        str(ROOT / "tests/arena_panel.cpp"), str(ROOT / "firmware/t-display/src/Panels.cpp"),
        str(ROOT / "firmware/t-display/src/AssetStore.cpp"),
        str(core / "vpet/PetState.cpp"), str(core / "vpet/Nutrition.cpp"), "-o", str(binary),
    ], check=True)
    return binary, data


@pytest.mark.parametrize("language", ["ES", "EN"])
@pytest.mark.parametrize("species", [0, 1, 2])  # Stable NVS ids: rookie, champion, ultimate.
@pytest.mark.parametrize("result", [0, 1, 2, 3])
def test_real_panels_draws_battle_and_full_animated_result(arena_binary, language, species, result):
    binary, data = arena_binary
    assert subprocess.check_output([str(binary), str(data), str(result), str(species), language],
                                   text=True).strip() == "ARENA_PANEL_OK"
