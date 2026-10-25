import copy
import json
from pathlib import Path
import subprocess
import shutil
import io
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


def builtin():
    from scripts.content_definitions import load_definition
    return load_definition(ROOT / "src/data/content/firemon.json")


def test_definition_resolves_all_views_and_legacy_fallbacks():
    definition = builtin()
    assert definition.name("ultimate", "battle") == "DRAGFIRE"
    assert definition.clip("ultimate", "walk")["atlas"].endswith("/dragfiremon_fly_atlas.bmp")
    assert definition.clip("champion", "hit", "battle")["path"] == "/battle/champion_punch.vpa"
    assert definition.clip("baby", "punch", "training")["path"] == "/training/sparkmon_idle.vpa"
    assert definition.clip("rookie", "walk", "exploration")["path"] == "/exploration/firemon_walk44.vpa"
    assert definition.stage("rookie")["portrait"] == "/UIEvolution/Firemon.bmp"
    assert definition.clip("ultimate", "sleep")["loop"] == [11, 14]


def test_alternative_definition_does_not_require_species_names():
    from core.content import PetDefinition
    document = copy.deepcopy(builtin().document)
    document["id"] = "test.other"
    stage = document["stages"]["rookie"]
    stage.update(name="AQUAMON", short_name="AQUA", battle_name="AQUAMON",
                 stem="aquamon", atlas_root="other/Rookie", home_root="/packs/test/rookie",
                 portrait="/portraits/aquamon.bmp", portrait_asset="/packs/test/aquamon.vpa")
    stage["actions"]["idle"].update(frames=7, interval_ms=150)
    definition = PetDefinition(document)
    assert definition.name("rookie") == "AQUAMON"
    clip = definition.clip("rookie", "idle")
    assert (clip["frames"], clip["interval_ms"]) == (7, 150)
    assert clip["path"] == "/packs/test/rookie/aquamon_idle.vpa"
    assert "firemon" not in json.dumps(clip)
    assert builtin().name("rookie") == "FIREMON"


@pytest.mark.parametrize("mutation", ["missing_role", "path_escape", "zero_frames", "bad_loop", "unknown_action", "profile"])
def test_invalid_definitions_are_rejected(mutation):
    from core.content import PetDefinition
    document = copy.deepcopy(builtin().document)
    if mutation == "missing_role":
        del document["stages"]["baby"]
    elif mutation == "path_escape":
        document["stages"]["rookie"]["atlas_root"] = "../outside"
    elif mutation == "zero_frames":
        document["stages"]["rookie"]["actions"]["idle"]["frames"] = 0
    elif mutation == "bad_loop":
        document["stages"]["rookie"]["actions"]["sleep"]["loop"] = [14, 30]
    elif mutation == "unknown_action":
        document["stages"]["rookie"]["aliases"]["walk"] = "execute_script"
    else:
        document["profile"] = "other-screen"
    with pytest.raises(ValueError):
        PetDefinition(document)


def test_generated_definitions_are_current_and_deterministic(tmp_path):
    from scripts.content_definitions import export, cpp_header, python_module
    definition = builtin()
    assert cpp_header(definition) == cpp_header(definition)
    assert python_module(definition) == python_module(definition)
    export(check=True)
    export(tmp_path)
    export(tmp_path, check=True)


def test_budget_counts_shared_art_once_and_requires_staging():
    from scripts.content_budget import budget
    report = budget(shared_bytes=100, package_bytes=[200, 300], individual_bytes=1024,
                    slots=4, journal_bytes=4096, fs_capacity=9000, reserve_bytes=1000)
    assert report["individual_bytes"] == 4096
    assert report["installed_bytes"] == 600
    assert report["staging_bytes"] == 300
    assert report["required_bytes"] == 10092
    assert not report["fits"]


def other_definition():
    from core.content import PetDefinition
    document = copy.deepcopy(builtin().document)
    document["id"] = "test.water"
    for role, stage in document["stages"].items():
        stage.update(name="WATER" + role.upper()[:5], short_name="WATER", battle_name="WATER",
                     stem="water" + role, atlas_root="water/" + role,
                     home_root="/water/home/" + role, training_prefix="/water/training/" + role,
                     battle_prefix="/water/battle/" + role, exploration_prefix="/water/travel/" + role,
                     portrait="/water/" + role + ".bmp", portrait_asset="/water/" + role + ".vpa")
    document["stages"]["rookie"]["actions"]["idle"].update(frames=7, interval_ms=150)
    document["stages"]["rookie"]["actions"]["sleep"].update(frames=6, interval_ms=100, loop=[2, 4])
    return PetDefinition(document)


def test_same_cpp_resolver_accepts_other_names_paths_and_motion(tmp_path):
    from core.content import ACTIONS, CONTEXTS, LEGACY_ROLES
    from scripts.content_definitions import cpp_header
    other = other_definition()
    (tmp_path / "OtherPet.h").write_text(cpp_header(other, "other_content", "otherDefinition"))
    core = ROOT / "firmware/t-display/lib/vpet_core/src"
    binary = tmp_path / "trace"
    subprocess.run(["c++", "-std=c++17", "-I" + str(core), "-I" + str(tmp_path),
                    str(ROOT / "tests/content_definition_trace.cpp"), str(core / "vpet/Motion.cpp"),
                    "-o", str(binary)], check=True)
    for index, definition in enumerate((builtin(), other)):
        lines = subprocess.check_output([str(binary), str(index)], text=True).splitlines()
        expected = []
        for role in LEGACY_ROLES:
            for context in CONTEXTS:
                for action in ACTIONS:
                    clip = definition.clip(role, action, context)
                    expected.append("%s %d %d %d %d %d" % (clip["path"], clip["frames"],
                                    clip["interval_ms"], *clip["loop"], clip["canvas"]))
        assert lines == expected


@pytest.fixture(scope="module")
def other_views(tmp_path_factory):
    from core.content import ACTIONS, CONTEXTS, ROLES
    from scripts.content_definitions import cpp_header
    from scripts import build_tdisplay
    from PIL import Image
    root = tmp_path_factory.mktemp("content-views")
    original, other = builtin(), other_definition()
    data, sim = root / "data", root / "sim"
    shutil.copytree(ROOT / "build-tdisplay", sim)
    for role in ROLES:
        for action in other.stage(role)["actions"]:
            src = sim / original.clip(role, action)["atlas"].lstrip("/")
            clip = other.clip(role, action)
            dst = sim / clip["atlas"].lstrip("/")
            dst.parent.mkdir(parents=True, exist_ok=True)
            with Image.open(src) as image:
                image.crop((0, 0, image.height * clip["frames"], image.height)).save(dst)
        src = sim / original.stage(role)["portrait"].lstrip("/")
        dst = sim / other.stage(role)["portrait"].lstrip("/")
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
    shutil.rmtree(sim / "digimon1")
    (sim / "content.json").write_text(json.dumps(other.document))
    build_tdisplay.build(ROOT, sim, data, root / "include/generated", definition=other)
    (root / "OtherPet.h").write_text(cpp_header(other, "other_content", "otherDefinition"))
    core = ROOT / "firmware/t-display/lib/vpet_core/src"
    binary = root / "views"
    subprocess.run(["c++", "-std=c++17", "-O1", "-ffunction-sections", "-fdata-sections",
                    "-Wl,-dead_strip" if sys.platform == "darwin" else "-Wl,--gc-sections",
                    "-I" + str(root), "-I" + str(ROOT / "tests/asset_stubs"),
                    "-I" + str(root / "include"), "-I" + str(ROOT / "firmware/t-display/include"), "-I" + str(core),
                    str(ROOT / "tests/content_views.cpp"),
                    *[str(ROOT / "firmware/t-display/src" / (n + ".cpp")) for n in ("Panels", "Renderer", "AssetStore")],
                    *[str(core / "vpet" / (n + ".cpp")) for n in ("PetState", "Nutrition", "Navigation", "DateTimeMenu", "Evolution", "Motion")],
                    "-o", str(binary)], check=True)
    yield data, binary, other, sim
    from PIL import ImageDraw
    views = ("home", "status", "training", "arena", "exploration", "tree", "detail")
    gallery = Image.new("RGB", (980, len(views) * 290), "#e4e6e8")
    draw = ImageDraw.Draw(gallery)
    for row, view in enumerate(views):
        for col, kind in enumerate(("sim", "firmware")):
            path = root / (view + "-" + kind + ".png")
            if path.is_file():
                draw.text((col * 490, row * 290), view + " " + kind, fill="black")
                with Image.open(path) as image:
                    gallery.paste(image.resize((480, 270), Image.Resampling.NEAREST), (col * 490, row * 290 + 18))
    gallery.save(root / "gallery.png")


@pytest.mark.parametrize("view,context", [("home", "home"), ("status", "home"),
    ("training", "training"), ("arena", "battle"), ("exploration", "exploration"),
    ("tree", "portrait"), ("detail", "portrait")])
def test_real_views_resolve_alternative_content_without_changing_save(other_views, view, context):
    from PIL import Image
    data, binary, other, _ = other_views
    action = "punch" if view == "training" else "idle"
    wanted = other.stage("rookie")["portrait_asset"] if context == "portrait" else other.clip("rookie", action, context)["path"]
    image = Image.open(io.BytesIO(subprocess.check_output([str(binary), str(data), view, wanted]))).convert("RGB")
    assert image.size == (240, 135)
    assert len(image.getcolors(240 * 135)) > 20
    image.save(data.parent / (view + "-firmware.png"))


@pytest.mark.parametrize("view", ["home", "status", "training", "arena", "exploration", "tree", "detail"])
def test_simulator_uses_second_pack_with_no_legacy_atlas_files(other_views, view):
    from core.pet import Pet
    from display_profiles import get_display_profile
    from scripts.sim_renderer import render_frame
    from scripts.training_renderer import render_training
    from scripts.practice_renderer import render_practice
    from scripts.training_session import TrainingSession
    from scripts.practice_session import PracticeSession
    from scripts.exploration_renderer import draw_exploration
    from PIL import Image
    _, _, _, sim = other_views
    pet = Pet(species="rookie", state="live")
    before = pet.to_dict()
    if view == "training":
        image = render_training(sim, TrainingSession(pet, lambda _: pytest.fail("Rendering cannot save")))
    elif view == "arena":
        session = PracticeSession(pet, lambda _: pytest.fail("Rendering cannot save"))
        image = render_practice(sim, session)
    elif view == "exploration":
        from scripts.exploration_session import ExplorationSession
        image = Image.new("RGB", (240,135))
        session = ExplorationSession(pet, lambda _: pytest.fail("Rendering cannot save"), lambda: 1791979200)
        session.page = "confirm"
        draw_exploration(image, sim, pet, session, 1791979200)
    else:
        mode = {"home": None, "status": "status", "tree": "evolution", "detail": "evolution_detail"}[view]
        image = render_frame(sim, pet, panel_mode=mode, panel_index=2,
                             profile=get_display_profile("tdisplay"))
    assert image.size == (240,135)
    assert len(image.convert("RGB").getcolors(240*135)) > 20
    assert pet.to_dict() == before
    image.save(sim.parent / (view + "-sim.png"))


def test_preflight_preserves_previous_output_if_sources_are_missing(tmp_path):
    from scripts import build_tdisplay
    data = tmp_path / "data"
    data.mkdir()
    (data / "keep.txt").write_text("previous working content")
    with pytest.raises(ValueError, match="Missing content"):
        build_tdisplay.build(ROOT, tmp_path / "empty", data, tmp_path / "include")
    assert (data / "keep.txt").read_text() == "previous working content"


@pytest.fixture(scope="module")
def definition_build(tmp_path_factory):
    from scripts import build_tdisplay
    root = tmp_path_factory.mktemp("definition-build")
    manifest = build_tdisplay.build(ROOT, ROOT / "build-tdisplay", root / "data", root / "include")
    return root, manifest


def test_manifest_records_definition_and_existing_weight_rule(definition_build):
    root, manifest = definition_build
    assert manifest["content_definition"] == builtin().document
    rule = next(r for r in manifest["evolution"] if r["from"] == "rookie")
    assert (rule["min_weight"], rule["max_weight"]) == (8, 14)
    assert "kEvolutionWeights" in (root / "include/catalog.h").read_text()


def test_budget_reports_two_lines_not_four_copies_of_every_asset(definition_build):
    from scripts.content_budget import from_manifest
    root, _ = definition_build
    report = from_manifest(root / "data/manifest.json")
    assert len(report["package_bytes"]) == 2
    assert report["individual_bytes"] == 4 * 4096
    assert report["staging_bytes"] > 0
    assert not report["fits"]


@pytest.mark.parametrize("document", [None, [], {"schema": True, "profile": "tdisplay-240x135"}])
def test_malformed_documents_raise_validation_errors(document):
    from core.content import PetDefinition
    with pytest.raises(ValueError):
        PetDefinition(document)


def test_duplicate_json_keys_are_not_silently_accepted(tmp_path):
    from scripts.content_definitions import load_definition
    target = tmp_path / "duplicate.json"
    target.write_text('{"schema":1,"schema":2}')
    with pytest.raises(ValueError, match="Duplicate"):
        load_definition(target)


def test_conflicting_output_paths_are_rejected():
    from core.content import PetDefinition
    document = copy.deepcopy(builtin().document)
    document["stages"]["champion"]["training_prefix"] = document["stages"]["rookie"]["training_prefix"]
    with pytest.raises(ValueError, match="Conflicting"):
        PetDefinition(document)


def test_motion_uses_definition_frames_and_sleep_loop_without_touching_pet():
    from core.motion import PetMotion
    definition = other_definition()
    motion = PetMotion(now=0, definition=definition, species="rookie")
    motion.set_tired(True, 0)
    motion.update(9 * .150)
    assert motion.frame == 2
    motion.start_sleep(0)
    motion.update(3)
    assert 2 <= motion.frame <= 4
