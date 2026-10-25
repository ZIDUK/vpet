import io
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image, ImageChops

from config import EVOLUTION_REGISTRY
from core.evolution_progress import evolution_progress
from core.pet import Pet
from display_profiles import get_display_profile
from scripts import build, build_tdisplay
from scripts.sim_renderer import render_frame
from scripts.verify_training_pixels import quantized

ROOT = Path(__file__).resolve().parents[1]
SPECIES = [(3, "egg", 0), (4, "baby", 1), (0, "rookie", 2),
           (1, "champion", 3), (2, "ultimate", 4)]


@pytest.fixture(scope="module")
def evolution_pixels(tmp_path_factory):
    root = tmp_path_factory.mktemp("evolution-progress")
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
        str(ROOT / "tests/evolution_progress.cpp"),
        *[str(ROOT / "firmware/t-display/src" / (name + ".cpp")) for name in ("Panels", "AssetStore")],
        *[str(core / "vpet" / (name + ".cpp")) for name in ("PetState", "Nutrition", "Navigation", "DateTimeMenu", "Evolution")],
        "-o", str(binary),
    ], check=True)
    return sim, data, binary


def fixture_pet(species, language, met, age=46800, weight=10):
    pet = Pet(species=species, state="egg" if species == "egg" else "live")
    pet.language = language
    pet.stats.update(h=80 if met else 40, e=70, p=60, hp=90)
    pet.stage_age_seconds, pet.weight = age, weight
    pet.battles_this_form = 15 if met else 14
    pet.battles_won, pet.battles_lost = (9, 6) if met else (8, 7)
    pet.care_mistakes = 1 if met else 2
    return pet


@pytest.mark.parametrize("species_id,species,stage", SPECIES)
@pytest.mark.parametrize("language", ["ES", "EN"])
@pytest.mark.parametrize("met", [False, True])
def test_production_panel_matches_simulator_without_mutating_state(evolution_pixels, species_id, species, stage, language, met):
    sim, data, binary = evolution_pixels
    pet = fixture_pet(species, language, met)
    for selected in {stage, 0, 4}:
        info = evolution_progress(pet, EVOLUTION_REGISTRY, selected)
        for page in range(info["pages"]):
            raw = subprocess.check_output([str(binary), str(data), str(species_id), str(selected),
                                           str(page), language, str(int(met)), "46800", "10", "pixels"])
            actual = Image.open(io.BytesIO(raw)).convert("RGB")
            expected = quantized(render_frame(sim, pet, panel_mode="evolution_detail",
                                              panel_index=selected + page * 5,
                                              profile=get_display_profile("tdisplay")))
            assert ImageChops.difference(actual.crop((0, 24, 240, 135)), expected.crop((0, 24, 240, 135))).getbbox() is None
            assert actual.getpixel((239, 134)) == quantized(Image.new("RGB", (1, 1), (19, 23, 27))).getpixel((0, 0))


@pytest.mark.parametrize("species_id,species,stage", SPECIES)
@pytest.mark.parametrize("met", [False, True])
def test_cpp_and_python_progress_rows_match(evolution_pixels, species_id, species, stage, met):
    _, data, binary = evolution_pixels
    states = ("progress", "reached", "hidden", "final", "egg", "unavailable")
    kinds = ("time", "mistakes", "battles", "wins", "hunger", "energy", "mood", "health", "weight")
    for age in (0, 43799, 43800, 86399, 86400, 129600):
        for weight in (7, 8, 14, 15):
            pet = fixture_pet(species, "ES", met, age, weight)
            info = evolution_progress(pet, EVOLUTION_REGISTRY, stage)
            lines = subprocess.check_output([str(binary), str(data), str(species_id), str(stage), "0", "ES",
                                              str(int(met)), str(age), str(weight), "model"], text=True).splitlines()
            assert list(map(int, lines[0].split())) == [states.index(info["state"]), len(info["rows"]), info["pages"]]
            for actual, row in zip(lines[1:], info["rows"]):
                assert list(map(int, actual.split())) == [kinds.index(row["kind"]), row["current"], row["target"],
                                                          row["upper"], row["remaining"], int(row["met"])]
