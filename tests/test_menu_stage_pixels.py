import io
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image

from core.pet import Pet
from display_profiles import get_display_profile
from scripts import build, build_tdisplay
from scripts.sim_renderer import render_frame

ROOT = Path(__file__).resolve().parents[1]
SPECIES = [(0, "rookie"), (1, "champion"), (2, "ultimate"), (3, "egg"), (4, "baby")]


@pytest.fixture(scope="module")
def menu_stage_pixels(tmp_path_factory):
    root = tmp_path_factory.mktemp("menu-stage-pixels")
    sim, data, include = root / "sim", root / "data", root / "include"
    build.main(profile_name="tdisplay", output_dir=sim)
    build_tdisplay.build(ROOT, sim, data, include / "generated")
    core = ROOT / "firmware/t-display/lib/vpet_core/src"
    binary = root / "render"
    subprocess.run([
        "c++", "-std=c++17", "-O1", "-ffunction-sections", "-fdata-sections",
        "-Wl,-dead_strip" if sys.platform == "darwin" else "-Wl,--gc-sections",
        "-I" + str(ROOT / "tests/asset_stubs"), "-I" + str(include),
        "-I" + str(ROOT / "firmware/t-display/include"), "-I" + str(core),
        str(ROOT / "tests/menu_stage_pixels.cpp"),
        *[str(ROOT / "firmware/t-display/src" / (name + ".cpp"))
          for name in ("Renderer", "Panels", "AssetStore")],
        *[str(core / "vpet" / (name + ".cpp"))
          for name in ("Motion", "PetState", "Nutrition", "Navigation", "DateTimeMenu", "Evolution")],
        "-o", str(binary),
    ], check=True)
    return sim, data, binary


def locked_icons(species):
    return {1, 2, 3, 4, 5} if species == "egg" else {2, 3, 4} if species == "baby" else set()


def expected_bar(baseline, species, board):
    image = baseline.crop((0, 0, 240, 24))
    for index in locked_icons(species):
        x = (index * 240 // 9 + ((index + 1) * 240 // 9 - index * 240 // 9 - 20) // 2
             if board else index * 26 + 3)
        for y in range(2, 22):
            for px in range(x, x + 20):
                color = image.getpixel((px, y))
                if board:
                    dim = tuple((round(c * levels / 255) >> 1) * 255 // levels
                                for c, levels in zip(color, (31, 63, 31)))
                else:
                    dim = tuple(c >> 1 for c in color)
                image.putpixel((px, y), dim)
    return image


@pytest.mark.parametrize("species_id,species", SPECIES)
@pytest.mark.parametrize("view", ["home", "status", "explore", "explore-uncached"])
def test_real_board_dims_only_stage_locked_icons_and_refreshes_after_evolution(menu_stage_pixels, species_id, species, view):
    _, data, binary = menu_stage_pixels
    for selected in range(9):
        def frame(stage):
            return Image.open(io.BytesIO(subprocess.check_output([
                str(binary), str(data), str(stage), view, str(selected)]))).convert("RGB")
        actual, baseline = frame(species_id), frame(0)
        assert actual.crop((0, 0, 240, 24)).tobytes() == expected_bar(baseline, species, True).tobytes()


@pytest.mark.parametrize("species_id,species", SPECIES)
@pytest.mark.parametrize("panel", [None, "status", "explore"])
def test_simulator_stage_icons_preserve_colors_selection_and_unlocked_menus(menu_stage_pixels, species_id, species, panel):
    sim, _, _ = menu_stage_pixels
    for selected in range(9):
        def frame(stage):
            pet = Pet(species=stage, state="egg" if stage == "egg" else "live")
            pet.stats.update(h=80, e=80, p=80)
            return render_frame(sim, pet, menu_index=selected, panel_mode=panel,
                                profile=get_display_profile("tdisplay"))
        actual, baseline = frame(species), frame("rookie")
        assert actual.crop((0, 0, 240, 24)).tobytes() == expected_bar(baseline, species, False).tobytes()


@pytest.mark.parametrize("species_id,species", SPECIES)
@pytest.mark.parametrize("language", ["ES", "EN"])
def test_board_evolution_current_text_uses_dark_ink(menu_stage_pixels, species_id, species, language):
    from core.evolution import evolution_current_stage
    _, data, binary = menu_stage_pixels
    pet = Pet(species=species, state="egg" if species == "egg" else "live")
    subprocess.run([str(binary), str(data), str(species_id), "evolution",
                    str(evolution_current_stage(pet)), language], check=True, stdout=subprocess.DEVNULL)


@pytest.mark.parametrize("species_id,species", SPECIES)
@pytest.mark.parametrize("language", ["ES", "EN"])
def test_simulator_evolution_current_text_uses_dark_ink(menu_stage_pixels, species_id, species, language):
    from core.evolution import EVO_CHIP, evolution_current_stage, evolution_tree_xy, evolution_window
    sim, _, _ = menu_stage_pixels
    pet = Pet(species=species, state="egg" if species == "egg" else "live")
    pet.language = language
    current = evolution_current_stage(pet)
    frame = render_frame(sim, pet, menu_index=7, panel_mode="evolution", panel_index=current,
                         profile=get_display_profile("tdisplay"))
    x, _ = evolution_tree_xy(current, evolution_window(current)[0])
    for bounds in ((x - 10, 92, x + EVO_CHIP + 10, 104), (0, 104, 240, 119)):
        colors = set(frame.crop(bounds).getdata())
        assert any(max(color) < 110 for color in colors)
        assert (66, 190, 140) not in colors
    assert frame.getpixel((12, 125)) == (66, 190, 140)  # Progress color is unchanged.
