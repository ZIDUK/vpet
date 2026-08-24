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


def test_full_evolution_chain():
    """The custom line has 6 stages: egg → baby → rookie → champion → ultimate → mega."""
    digimon_dir = DATA / "digimon"
    forms = [json.loads(p.read_text()) for p in digimon_dir.glob("*.json")]
    STAGE_ORDER = ["egg", "baby", "rookie", "champion", "ultimate", "mega"]
    chain = sorted(
        [d for d in forms if d["line"] == "custom_line"],
        key=lambda d: STAGE_ORDER.index(d["stage"]),
    )
    assert len(chain) == 6
    assert [d["stage"] for d in chain] == STAGE_ORDER
    # Each stage evolves to the next
    for i in range(len(chain) - 1):
        assert chain[i]["evolves_to"] == chain[i + 1]["stage"]
    # Final stage has no evolution
    assert chain[-1]["evolves_to"] is None


def test_mega_is_final_form():
    """Mega is the final stage and has no further evolution."""
    digimon_dir = DATA / "digimon"
    mega = json.loads((digimon_dir / "mega.json").read_text())
    assert mega["stage"] == "mega"
    assert mega["evolves_to"] is None


def test_egg_is_present():
    """The starter form (egg) should always exist so Pet() can default to it."""
    digimon_dir = DATA / "digimon"
    egg = digimon_dir / "egg.json"
    assert egg.exists(), "egg.json must exist (starter form)"
    data = json.loads(egg.read_text())
    assert data["name"] == "Egg"
    assert data["stage"] == "egg"
    assert data["evolves_to"] == "baby"


def test_requirements_increase_through_stages():
    """Each non-final stage should require more than the previous (final = no reqs)."""
    digimon_dir = DATA / "digimon"
    forms = [json.loads(p.read_text()) for p in digimon_dir.glob("*.json")]
    # Group by line
    by_line = {}
    for f in forms:
        by_line.setdefault(f["line"], []).append(f)
    STAGE_ORDER = ["egg", "baby", "rookie", "champion", "ultimate", "mega"]
    for line_name, stages in by_line.items():
        stages.sort(key=lambda d: STAGE_ORDER.index(d["stage"]))
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
