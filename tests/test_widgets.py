"""Tests for the data layer (JSON files).

The data model is now: any number of digimon JSONs, each defines a form
in an evolution chain. Tests verify the JSON files are well-formed and
the chain is consistent.
"""
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


def test_final_forms_have_no_evolution():
    digimon_dir = DATA / "digimon"
    forms = [json.loads(p.read_text()) for p in digimon_dir.glob("*.json")]
    final = [d for d in forms if d["stage"] == "mega"]
    for d in final:
        assert d["evolves_to"] is None


def test_placeholder_digimon_is_present():
    """The starter form should always exist so Pet() can default to it."""
    digimon_dir = DATA / "digimon"
    placeholder = digimon_dir / "placeholder.json"
    assert placeholder.exists(), "placeholder.json must exist (starter form)"
    data = json.loads(placeholder.read_text())
    # The JSON's filename (without .json) is the species id
    assert data["name"] == "Placeholder"
    # Placeholder doesn't evolve yet (single-form game until you add more)
    assert data["evolves_to"] is None


def test_requirements_increase_through_stages():
    """Each non-final stage should require more than the previous (final = no reqs)."""
    digimon_dir = DATA / "digimon"
    forms = [json.loads(p.read_text()) for p in digimon_dir.glob("*.json")]
    # Group by line
    by_line = {}
    for f in forms:
        by_line.setdefault(f["line"], []).append(f)
    for line_name, stages in by_line.items():
        stages.sort(key=lambda d: ["rookie", "champion", "ultimate", "mega"].index(d["stage"]))
        prev_sum = 0
        for stage in stages:
            if stage["evolves_to"] is None:
                continue  # skip final forms
            cur_sum = sum(stage.get("requirements", {}).values())
            assert cur_sum >= prev_sum, (
                f"{stage['name']} requires less than previous in {line_name}"
            )
            prev_sum = cur_sum


def test_npcs_have_required_fields():
    npcs_dir = DATA / "npcs"
    if not npcs_dir.exists():
        return  # NPCs optional
    for path in npcs_dir.glob("*.json"):
        data = json.loads(path.read_text())
        if "wild" not in data:
            continue
        for npc in data["wild"]:
            assert {"id", "name", "hp", "attack", "sprite"} <= set(npc.keys()), (
                f"{path.name} -> {npc.get('id', '?')} missing fields"
            )
            assert npc["hp"] > 0
            assert npc["attack"] > 0
