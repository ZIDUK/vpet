import copy

import pytest

from config import EVOLUTION_REGISTRY
from core.pet import Pet


def progress(pet, selected=None, scale=1):
    from core.evolution_progress import evolution_progress
    return evolution_progress(pet, EVOLUTION_REGISTRY, selected, scale)


def test_rookie_shows_outgoing_rules_without_changing_pet():
    pet = Pet(species="rookie", state="live")
    pet.stage_age_seconds = 13 * 3600
    pet.weight = 10
    before = copy.deepcopy(pet.to_dict())
    data = progress(pet)
    assert data["state"] == "progress"
    assert data["name"] == "FIREMON"
    assert data["pages"] == 2
    assert [row["kind"] for row in data["rows"]] == ["time", "hunger", "energy", "mood", "health", "weight"]
    assert data["rows"][0]["remaining"] == 11 * 3600
    assert data["rows"][-1]["target"] == 8
    assert data["rows"][-1]["upper"] == 14
    assert pet.to_dict() == before


@pytest.mark.parametrize("age,scale,remaining", [(0, 1, 86400), (144, 600, 0), (143, 600, 1), (86401, 1, 0)])
def test_time_is_remaining_wall_time_with_scale(age, scale, remaining):
    pet = Pet(species="rookie", state="live")
    pet.stage_age_seconds = age
    assert progress(pet, scale=scale)["rows"][0]["remaining"] == remaining


@pytest.mark.parametrize("weight,met", [(7, False), (8, True), (14, True), (15, False)])
def test_weight_range_matches_runtime(weight, met):
    pet = Pet(species="rookie", state="live")
    pet.weight = weight
    assert progress(pet)["rows"][-1]["met"] is met


@pytest.mark.parametrize("wins,losses,met", [(0, 0, True), (8, 7, False), (9, 6, True), (10, 6, True)])
def test_champion_keeps_form_battles_separate_from_lifetime_ratio(wins, losses, met):
    pet = Pet(species="champion", state="live")
    pet.battles_this_form = 14
    pet.battles_won, pet.battles_lost = wins, losses
    rows = progress(pet)["rows"]
    assert [row["kind"] for row in rows] == ["time", "battles", "wins"]
    assert rows[1]["current"] == 14 and rows[1]["target"] == 15
    assert rows[1]["met"] is False
    assert rows[2]["met"] is met


def test_care_mistakes_are_an_upper_bound():
    pet = Pet(species="baby", state="live")
    pet.care_mistakes = 2
    row = progress(pet)["rows"][1]
    assert row["kind"] == "mistakes" and row["target"] == 1
    assert not row["met"]


@pytest.mark.parametrize("species,selected,state", [
    ("rookie", 1, "reached"), ("rookie", 3, "hidden"),
    ("ultimate", 4, "final"), ("egg", 0, "egg"),
])
def test_non_progress_states_do_not_mix_current_values_with_other_forms(species, selected, state):
    data = progress(Pet(species=species, state="egg" if species == "egg" else "live"), selected)
    assert data["state"] == state and data["rows"] == [] and data["pages"] == 1


def test_pagination_keeps_the_selected_form():
    from core.evolution_progress import next_detail_index
    pet = Pet(species="rookie", state="live")
    assert next_detail_index(pet, EVOLUTION_REGISTRY, 2) == 7
    assert next_detail_index(pet, EVOLUTION_REGISTRY, 7) == 2
    assert next_detail_index(pet, EVOLUTION_REGISTRY, 1) == 1


def test_real_app_pages_and_returns_without_writing_the_save(tmp_path):
    import subprocess
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    firmware = root / "firmware/t-display"
    core = firmware / "lib/vpet_core/src"
    binary = tmp_path / "app"
    subprocess.run(["c++", "-std=c++17", "-I" + str(root / "tests/app_stubs"),
                    "-I" + str(firmware / "include"), "-I" + str(core),
                    str(root / "tests/evolution_detail_app.cpp"), str(firmware / "src/App.cpp"),
                    *[str(core / "vpet" / (name + ".cpp")) for name in
                      ("PetState", "Nutrition", "SettingsStore", "PracticeBattle", "Motion", "Navigation", "Evolution", "DateTimeMenu")],
                    "-o", str(binary)], check=True)
    subprocess.run([str(binary)], check=True)


def test_labels_and_values_do_not_overlap_in_any_requirement_row():
    from scripts.evolution_renderer import LABELS, font, row_value
    for species in ("baby", "rookie", "champion"):
        pet = Pet(species=species, state="live")
        pet.battles_this_form = 65535
        for es in (False, True):
            for row in progress(pet)["rows"]:
                label = LABELS[row["kind"]][es]
                value = row_value(row, es)
                assert font().getlength(label, mode="1") + font().getlength(value, mode="1") + 8 <= 147
