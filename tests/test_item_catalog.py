"""Official metadata, bilingual C++ UI parity, exported sprites and save limits."""
import copy
import shutil
import subprocess
from pathlib import Path
import pytest
from PIL import Image
from core.item_catalog import ITEMS, ITEM_BY_ID
from core.inventory import inventory_name, inventory_blurb, inventory_icon
from core.pet import Pet
from scripts.export_item_catalog import export, validate

ROOT = Path(__file__).resolve().parents[1]


def test_exported_catalog_and_sprites_are_current():
    export(check=True)
    assert tuple(item["id"] for item in ITEMS) == ("meat", "energy", "exp", "ring", "protein", "medkit", "guide")
    for item in ITEMS:
        with Image.open(ROOT / "assets/ui/items" / (item["id"] + ".png")) as image:
            assert image.size == (32, 32) and image.mode == "RGBA"
            assert image.getpixel((0, 0))[3] == 0
            assert image.getbbox() is not None
        assert inventory_icon(item["index"]) == item["icon"]


def test_evolution_items_and_effects_are_rejected():
    bad = copy.deepcopy(ITEMS)
    bad[0]["category"] = "evolution"
    with pytest.raises(AssertionError, match="evolution excluded"):
        validate(bad)
    bad = copy.deepcopy(ITEMS)
    bad[0]["effects"][0]["target"] = "species"
    with pytest.raises(AssertionError, match="evolution excluded"):
        validate(bad)
    bad = copy.deepcopy(ITEMS)
    bad[0]["effects"][0]["kind"] = "evolve"
    with pytest.raises(AssertionError, match="evolution excluded"):
        validate(bad)


def test_amulet_changes_only_mood_and_preserves_legacy_id():
    from core.inventory import use_inventory_item
    p = Pet(species="rookie", state="live")
    before = dict(p.stats)
    assert use_inventory_item(p, 3) == "used"
    assert p.species == "rookie" and not any(p.ev.values())
    assert p.stats == {**before, "p": min(100, before["p"] + 15)}
    assert p.inventory["ring"] == 0
    assert inventory_name(3, True) == "AMULETO"
    assert inventory_name(3) == "AMULET"
    assert "ANIMO" in inventory_blurb(3, True)


def test_saved_item_counts_match_board_stack_limits():
    p = Pet(species="rookie", state="live")
    data = p.to_dict()
    data["inventory"].update(energy=1000, ring=-2, medkit="bad", evolution_stone=1)
    p.load_from_dict(data)
    assert p.inventory["energy"] == 99
    assert p.inventory["ring"] == 0
    assert p.inventory["medkit"] == 0
    assert "evolution_stone" not in p.inventory


@pytest.mark.parametrize("food", ["meat", "protein"])
def test_food_reports_actual_capped_weight_change(food):
    p = Pet(species="rookie", state="live")
    p.weight = 99
    assert p.use_food(food)["changed_fields"]["weight"] == 0


def test_cpp_bilingual_names_effect_blurbs_and_sprite_paths_match_python(tmp_path):
    compiler = shutil.which("c++")
    assert compiler
    binary = tmp_path / "catalog"
    subprocess.run([compiler, "-std=c++11", "-I", str(ROOT / "firmware/t-display/lib/vpet_core/src"),
                    str(ROOT / "tests/item_catalog_trace.cpp"), "-o", str(binary)], check=True)
    lines = subprocess.check_output([str(binary)], text=True).splitlines()
    expected = []
    for item in ITEMS:
        expected.append("|".join(map(str, (item["id"], item["index"],
            inventory_name(item["index"], True), inventory_name(item["index"], False),
            inventory_blurb(item["index"], True), inventory_blurb(item["index"], False),
            "/ui/icons/" + item["icon"].lower() + ".vpa",
            -1 if item["stack_max"] is None else item["stack_max"], int(item["firmware_available"])))))
    assert lines == expected + ["BACK|/ui/icons/back.vpa"]


def test_backpack_blurbs_fit_the_firmware_preview_width():
    for item in ITEMS:
        if item["category"] == "food":
            continue
        for language in ("ES", "EN"):
            assert len(item["blurbs"][language]) * 6 <= 88
