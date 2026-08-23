"""Tests for the data layer (JSON files)."""
import json
from pathlib import Path


DATA = Path(__file__).parent.parent / "src" / "data"


def test_all_digimon_have_required_fields():
    required = {"name", "line", "stage", "sprite", "evolves_to"}
    digimon_dir = DATA / "digimon"
    for path in sorted(digimon_dir.glob("*.json")):
        data = json.loads(path.read_text())
        missing = required - set(data.keys())
        assert not missing, f"{path.name} missing: {missing}"


def test_evolution_chain_is_consistent():
    """Each form's evolves_to must point to a real JSON file."""
    digimon_dir = DATA / "digimon"
    forms = {p.stem: json.loads(p.read_text()) for p in digimon_dir.glob("*.json")}
    for name, data in forms.items():
        if data["evolves_to"]:
            assert data["evolves_to"] in forms, (
                f"{name} evolves_to '{data['evolves_to']}' but no such file"
            )


STAGE_ORDER = ["rookie", "champion", "ultimate", "mega"]


def test_agumon_line_has_4_forms():
    digimon_dir = DATA / "digimon"
    agumon_line = [
        json.loads(p.read_text())
        for p in digimon_dir.glob("*.json")
    ]
    agumon_line = [d for d in agumon_line if d["line"] == "agumon_line"]
    agumon_line.sort(key=lambda d: STAGE_ORDER.index(d["stage"]))
    assert len(agumon_line) == 4
    names = [d["name"] for d in agumon_line]
    assert names == ["Agumon", "Greymon", "MetalGreymon", "WarGreymon"]


def test_gabumon_line_has_4_forms():
    digimon_dir = DATA / "digimon"
    forms = [
        json.loads(p.read_text())
        for p in digimon_dir.glob("*.json")
    ]
    gabumon_line = [d for d in forms if d["line"] == "gabumon_line"]
    gabumon_line.sort(key=lambda d: STAGE_ORDER.index(d["stage"]))
    assert len(gabumon_line) == 4
    names = [d["name"] for d in gabumon_line]
    assert names == ["Gabumon", "Garurumon", "WereGarurumon", "MetalGarurumon"]


def test_final_forms_have_no_evolution():
    digimon_dir = DATA / "digimon"
    forms = [json.loads(p.read_text()) for p in digimon_dir.glob("*.json")]
    final = [d for d in forms if d["stage"] == "mega"]
    assert len(final) == 2  # WarGreymon + MetalGarurumon
    for d in final:
        assert d["evolves_to"] is None


def test_requirements_increase_through_stages():
    """Each non-final stage should require more than the previous (final = no reqs)."""
    digimon_dir = DATA / "digimon"
    forms = [json.loads(p.read_text()) for p in digimon_dir.glob("*.json")]
    for line in ("agumon_line", "gabumon_line"):
        stages = [d for d in forms if d["line"] == line]
        stages.sort(key=lambda d: STAGE_ORDER.index(d["stage"]))
        # Only check non-final stages (final = no evolution possible, reqs = {})
        prev_sum = 0
        for stage in stages:
            if stage["evolves_to"] is None:
                # Final form, skip
                continue
            cur_sum = sum(stage.get("requirements", {}).values())
            assert cur_sum >= prev_sum, (
                f"{stage['name']} requires less than previous stage in {line}"
            )
            prev_sum = cur_sum


def test_npcs_have_required_fields():
    npcs_dir = DATA / "npcs"
    for path in npcs_dir.glob("*.json"):
        data = json.loads(path.read_text())
        assert "wild" in data
        for npc in data["wild"]:
            assert {"id", "name", "hp", "attack", "sprite"} <= set(npc.keys()), (
                f"{path.name} -> {npc.get('id', '?')} missing fields"
            )
            assert npc["hp"] > 0
            assert npc["attack"] > 0
