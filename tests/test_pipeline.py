"""Integration tests for the build and deploy pipeline."""
import ast
import importlib.util
import json
import os
import shutil
import subprocess
from collections import namedtuple
from pathlib import Path
from types import SimpleNamespace

from PIL import Image

from scripts import build as build_script
from scripts import deploy as deploy_script


ROOT = Path(__file__).parent.parent


def test_makefile_keeps_explicit_pico_compatibility_targets():
    makefile = (ROOT / "Makefile").read_text()

    assert "deploy-pico:" in makefile
    assert "sim-pico:" in makefile
    assert "build-pico:" in makefile
    assert "build-tdisplay:" in makefile
    assert "scripts/sim.py --profile tdisplay --build-dir build-tdisplay" in makefile
    assert "scripts/deploy.py" in makefile


def _prepare_project(tmp_path, monkeypatch):
    project = tmp_path / "project"
    shutil.copytree(ROOT / "src", project / "src")
    shutil.copytree(ROOT / "assets", project / "assets")
    (project / "settings.toml").write_text("# test settings\n")

    monkeypatch.setattr(build_script, "ROOT", project)
    monkeypatch.setattr(build_script, "SRC", project / "src")
    monkeypatch.setattr(build_script, "BUILD", project / "build")
    monkeypatch.setattr(build_script, "ASSETS", project / "assets")
    return project


def test_build_produces_complete_modular_runtime(tmp_path, monkeypatch):
    project = _prepare_project(tmp_path, monkeypatch)

    build_script.main()

    output = project / "build"
    expected = {
        "code.py",
        "boot.py",
        "app.py",
        "hal.py",
        "config.py",
        "core/device_services.py",
        "core/menu.py",
        "core/motion.py",
        "core/evolution.py",
        "core/inventory.py",
        "core/options.py",
        "core/pet.py",
        "core/save.py",
        "ui/sprites.py",
        "ui/status.py",
        "Background/background.bmp",
        "Background/background_night.bmp",
        "UIIcons/Status.bmp",
        "UIEvolution/Egg.bmp",
        "UIEvolution/Sparkmon.bmp",
        "UIEvolution/Firemon.bmp",
        "UIEvolution/Flamemon.bmp",
        "UIEvolution/Dragfiremon.bmp",
        "digimon1/Egg/egg_idle_atlas.bmp",
        "digimon1/Baby/sparkmon_idle_atlas.bmp",
        "digimon1/Baby/sparkmon_walk_atlas.bmp",
        "digimon1/Baby/sparkmon_eat_atlas.bmp",
        "digimon1/Baby/sparkmon_sleep_atlas.bmp",
        "digimon1/Rookie/firemon_idle_atlas.bmp",
        "digimon1/Rookie/firemon_walk_atlas.bmp",
        "digimon1/Rookie/firemon_eat_atlas.bmp",
        "digimon1/Rookie/firemon_punch_atlas.bmp",
        "digimon1/Rookie/firemon_sleep_atlas.bmp",
        "digimon1/Rookie/firemon_cast_atlas.bmp",
        "digimon1/Rookie/firemon_evolution_atlas.bmp",
        "digimon1/Champion/flamemon_idle_atlas.bmp",
        "digimon1/Champion/flamemon_walk_atlas.bmp",
        "digimon1/Champion/flamemon_eat_atlas.bmp",
        "digimon1/Champion/flamemon_punch_atlas.bmp",
        "digimon1/Champion/flamemon_sleep_atlas.bmp",
        "digimon1/Champion/flamemon_cast_atlas.bmp",
        "digimon1/Champion/flamemon_evolution_atlas.bmp",
        "digimon1/Ultimate/dragfiremon_idle_atlas.bmp",
        "digimon1/Ultimate/dragfiremon_fly_atlas.bmp",
        "digimon1/Ultimate/dragfiremon_eat_atlas.bmp",
        "digimon1/Ultimate/dragfiremon_punch_atlas.bmp",
        "digimon1/Ultimate/dragfiremon_sleep_atlas.bmp",
        "digimon1/Ultimate/dragfiremon_cast_atlas.bmp",
        "settings.toml",
        ".vpet-manifest.json",
    }
    files = {
        str(path.relative_to(output))
        for path in output.rglob("*")
        if path.is_file()
    }
    assert expected <= files
    assert "core/battle.py" not in files
    assert "data/digimon/egg.json" not in files
    assert (output / "code.py").read_text() == "from app import run\n\nrun()\n"
    for module_path in output.rglob("*.py"):
        compile(module_path.read_text(), str(module_path), "exec")
    app_tree = ast.parse((output / "app.py").read_text())
    config_imports = {
        alias.name
        for node in app_tree.body
        if isinstance(node, ast.ImportFrom) and node.module == "config"
        for alias in node.names
    }
    assert "PET_EAT_IMAGE_PATH" in config_imports

    with Image.open(output / "Background" / "background.bmp") as day_opened:
        day = day_opened.convert("RGB")
    with Image.open(output / "Background" / "background_night.bmp") as night_opened:
        night = night_opened.convert("RGB")
    assert night.size == day.size == (128, 128)
    assert sum(night.resize((1, 1)).getpixel((0, 0))) < sum(
        day.resize((1, 1)).getpixel((0, 0))
    )

    with Image.open(output / "digimon1" / "Rookie" / "firemon_idle_atlas.bmp") as atlas:
        assert atlas.mode == "P"
        assert atlas.size == (19 * 64, 64)
        for frame_index in range(19):
            tile = atlas.crop((frame_index * 64, 0, (frame_index + 1) * 64, 64))
            assert tile.getpixel((0, 0)) == 0
            assert tile.getbbox() is not None
    with Image.open(output / "digimon1" / "Rookie" / "firemon_walk_atlas.bmp") as atlas:
        assert atlas.mode == "P"
        assert atlas.size == (22 * 64, 64)

    with Image.open(output / "digimon1" / "Rookie" / "firemon_eat_atlas.bmp") as atlas:
        assert atlas.mode == "P"
        assert atlas.size == (25 * 64, 64)
        assert atlas.getpixel((0, 0)) == 0

    with Image.open(output / "digimon1" / "Rookie" / "firemon_punch_atlas.bmp") as atlas:
        assert atlas.mode == "P"
        assert atlas.size == (15 * 64, 64)
        assert atlas.getpixel((0, 0)) == 0

    with Image.open(output / "digimon1" / "Rookie" / "firemon_sleep_atlas.bmp") as atlas:
        assert atlas.mode == "P"
        assert atlas.size == (15 * 64, 64)
        assert atlas.getpixel((0, 0)) == 0

    with Image.open(output / "digimon1" / "Rookie" / "firemon_cast_atlas.bmp") as atlas:
        assert atlas.mode == "P"
        assert atlas.size == (15 * 64, 64)
        assert atlas.getpixel((0, 0)) == 0

    with Image.open(output / "digimon1" / "Rookie" / "firemon_evolution_atlas.bmp") as atlas:
        assert atlas.mode == "P"
        assert atlas.size == (15 * 112, 112)
        assert atlas.getpixel((0, 0)) == 0

    with Image.open(output / "digimon1" / "Champion" / "flamemon_idle_atlas.bmp") as atlas:
        assert atlas.mode == "P"
        assert atlas.size == (15 * 64, 64)

    with Image.open(output / "digimon1" / "Champion" / "flamemon_walk_atlas.bmp") as atlas:
        assert atlas.mode == "P"
        assert atlas.size == (15 * 64, 64)

    with Image.open(output / "digimon1" / "Champion" / "flamemon_eat_atlas.bmp") as atlas:
        assert atlas.mode == "P"
        assert atlas.size == (25 * 64, 64)
        assert atlas.getpixel((0, 0)) == 0

    with Image.open(output / "digimon1" / "Champion" / "flamemon_punch_atlas.bmp") as atlas:
        assert atlas.mode == "P"
        assert atlas.size == (15 * 64, 64)
        assert atlas.getpixel((0, 0)) == 0

    with Image.open(output / "digimon1" / "Champion" / "flamemon_sleep_atlas.bmp") as atlas:
        assert atlas.mode == "P"
        assert atlas.size == (15 * 64, 64)
        assert atlas.getpixel((0, 0)) == 0

    with Image.open(output / "digimon1" / "Champion" / "flamemon_cast_atlas.bmp") as atlas:
        assert atlas.mode == "P"
        assert atlas.size == (15 * 64, 64)
        assert atlas.getpixel((0, 0)) == 0

    with Image.open(output / "digimon1" / "Champion" / "flamemon_evolution_atlas.bmp") as atlas:
        assert atlas.mode == "P"
        assert atlas.size == (15 * 112, 112)

    ultimate_atlases = {
        "dragfiremon_idle_atlas.bmp": 15,
        "dragfiremon_fly_atlas.bmp": 22,
        "dragfiremon_eat_atlas.bmp": 25,
        "dragfiremon_punch_atlas.bmp": 15,
        "dragfiremon_sleep_atlas.bmp": 15,
        "dragfiremon_cast_atlas.bmp": 15,
    }
    for name, count in ultimate_atlases.items():
        with Image.open(output / "digimon1" / "Ultimate" / name) as atlas:
            assert atlas.mode == "P"
            assert atlas.size == (count * 64, 64)
            assert atlas.getpixel((0, 0)) == 0

    for name in ("Egg.bmp", "Sparkmon.bmp", "Firemon.bmp", "Flamemon.bmp", "Dragfiremon.bmp"):
        with Image.open(output / "UIEvolution" / name) as portrait:
            assert portrait.mode == "P"
            assert portrait.size == (32, 32)
            assert portrait.getpixel((0, 0)) == 0
            assert portrait.getbbox() is not None

    manifest = json.loads((output / ".vpet-manifest.json").read_text())
    assert sorted(manifest["files"]) == sorted(files - {".vpet-manifest.json"})


def test_build_produces_tdisplay_sized_visual_assets(tmp_path):
    output = tmp_path / "build-tdisplay"

    build_script.main(profile_name="tdisplay", output_dir=output)

    with Image.open(output / "Background" / "background.bmp") as background:
        assert background.size == (240, 135)
    with Image.open(output / "UIIcons" / "Status.bmp") as icon:
        assert icon.size == (20, 20)
    with Image.open(output / "UIEvolution" / "Firemon.bmp") as portrait:
        assert portrait.size == (36, 36)
    with Image.open(output / "digimon1" / "Rookie" / "firemon_idle_atlas.bmp") as atlas:
        assert atlas.size == (19 * 88, 88)


def test_transparent_quantization_does_not_create_a_dark_alpha_halo():
    source = Image.new("RGBA", (2, 1))
    source.putdata([(255, 32, 0, 128), (0, 0, 0, 0)])

    converted = build_script._quantize_rgba_with_transparency(source)
    color_index = converted.getpixel((0, 0))
    palette = converted.getpalette()

    assert color_index != 0
    assert palette[color_index * 3] > 220
    assert converted.getpixel((1, 0)) == 0

def test_build_rejects_missing_runtime_asset(tmp_path, monkeypatch):
    project = _prepare_project(tmp_path, monkeypatch)
    for image in (project / "assets" / "backgrounds").iterdir():
        if image.suffix.lower() in {".bmp", ".png"}:
            image.unlink()

    try:
        build_script.main()
    except FileNotFoundError as exc:
        assert "background" in str(exc).lower()
    else:
        raise AssertionError("build accepted a missing background")


def test_deploy_syncs_manifest_and_preserves_device_data(tmp_path):
    source = tmp_path / "build"
    target = tmp_path / "CIRCUITPY"
    source.mkdir()
    target.mkdir()

    (source / "Background").mkdir()
    (source / "Background" / "background.bmp").write_bytes(b"new background")
    (source / "boot.py").write_text("new boot")
    (source / "code.py").write_text("new code")
    files = ["Background/background.bmp", "boot.py", "code.py"]
    (source / ".vpet-manifest.json").write_text(json.dumps({"files": files}))

    (target / "Background").mkdir()
    (target / "Background" / "jungle.bmp").write_bytes(b"stale")
    (target / "digimon1" / "Rookie").mkdir(parents=True)
    (target / "digimon1" / "Rookie" / "rookie_screenshot.bmp").write_bytes(b"stale")
    (target / "data" / "digimon").mkdir(parents=True)
    (target / "data" / "npcs").mkdir()
    (target / "pet_save.json").write_text("saved pet")
    (target / "wifi_config.json").write_text("saved wifi")
    (target / "boot_out.txt").write_text("firmware info")

    deploy_script.sync_build(source, target)

    assert not (target / "Background" / "jungle.bmp").exists()
    assert not (target / "digimon1" / "Rookie" / "rookie_screenshot.bmp").exists()
    assert not (target / "data").exists()
    assert (target / "Background" / "background.bmp").read_bytes() == b"new background"
    assert (target / "boot.py").read_text() == "new boot"
    assert (target / "code.py").read_text() == "new code"
    assert (target / "pet_save.json").read_text() == "saved pet"
    assert (target / "wifi_config.json").read_text() == "saved wifi"
    assert (target / "boot_out.txt").read_text() == "firmware info"


def test_deploy_copy_does_not_create_metadata_sidecars(tmp_path, monkeypatch):
    source = tmp_path / "source.bmp"
    target = tmp_path / "target.bmp"
    source.write_bytes(b"runtime asset")
    target.write_bytes(b"old asset with inherited metadata")
    monkeypatch.setattr(
        deploy_script.shutil,
        "copy2",
        lambda *_: (_ for _ in ()).throw(AssertionError("copy2 preserves metadata")),
    )
    monkeypatch.setattr(
        deploy_script.shutil,
        "copyfile",
        lambda *_: (_ for _ in ()).throw(AssertionError("copyfile kept FAT metadata")),
    )
    cleared_metadata = []
    monkeypatch.setattr(
        deploy_script,
        "clear_extended_attributes",
        lambda path: cleared_metadata.append(path),
        raising=False,
    )

    deploy_script.safe_copy2(source, target)

    assert target.read_bytes() == b"runtime asset"
    assert cleared_metadata == [target]


def test_deploy_skips_identical_build_files(tmp_path, monkeypatch):
    source = tmp_path / "build"
    target = tmp_path / "CIRCUITPY"
    source.mkdir()
    target.mkdir()
    (source / "code.py").write_text("same code")
    (target / "code.py").write_text("same code")
    manifest = json.dumps({"files": ["code.py"]})
    (source / ".vpet-manifest.json").write_text(manifest)
    (target / ".vpet-manifest.json").write_text(manifest)
    monkeypatch.setattr(
        deploy_script,
        "safe_copy2",
        lambda *_: (_ for _ in ()).throw(AssertionError("identical file was copied")),
    )

    assert deploy_script.sync_build(source, target) == 0


def test_simulator_has_shared_frame_renderer():
    assert importlib.util.find_spec("scripts.sim_renderer") is not None


def test_simulator_cli_renders_headless_frames():
    candidates = [
        shutil.which("python3"),
        "/usr/local/bin/python3",
        "/Library/Frameworks/Python.framework/Versions/3.13/bin/python3",
    ]
    python = None
    for candidate in candidates:
        if not candidate or not Path(candidate).exists():
            continue
        check = subprocess.run(
            [candidate, "-c", "import pygame, PIL"],
            capture_output=True,
        )
        if check.returncode == 0:
            python = candidate
            break
    if python is None:
        return

    environment = dict(os.environ)
    environment.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    result = subprocess.run(
        [python, str(ROOT / "scripts" / "sim.py"), "--max-frames", "2"],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_make_deploy_runs_tests_before_writing_board():
    result = subprocess.run(
        ["make", "-n", "deploy"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.index("pytest") < result.stdout.index("scripts/deploy_tdisplay.py")


def test_capacity_preflight_reports_flash_shortage(tmp_path, monkeypatch):
    source = tmp_path / "build"
    target = tmp_path / "CIRCUITPY"
    source.mkdir()
    target.mkdir()
    (source / "large.bmp").write_bytes(b"x" * 4096)
    (source / "code.py").write_text("run")
    files = ["large.bmp", "code.py"]
    (source / ".vpet-manifest.json").write_text(json.dumps({"files": files}))

    Usage = namedtuple("Usage", "total used free")
    monkeypatch.setattr(deploy_script.shutil, "disk_usage", lambda _: Usage(8192, 7680, 512))

    try:
        deploy_script.check_capacity(source, target, block_size=512, safety_margin=1024)
    except deploy_script.DeploymentSpaceError as exc:
        assert "flash" in str(exc).lower()
        assert "required" in str(exc).lower()
    else:
        raise AssertionError("capacity preflight accepted an oversized build")


def test_capacity_preflight_uses_fat_allocation_unit(tmp_path, monkeypatch):
    source = tmp_path / "build"
    target = tmp_path / "CIRCUITPY"
    source.mkdir()
    target.mkdir()
    (source / "code.py").write_text("run")
    (source / ".vpet-manifest.json").write_text(json.dumps({"files": ["code.py"]}))

    Usage = namedtuple("Usage", "total used free")
    monkeypatch.setattr(deploy_script.os, "statvfs", lambda _: SimpleNamespace(f_frsize=512))
    monkeypatch.setattr(deploy_script.shutil, "disk_usage", lambda _: Usage(520192, 0, 416256))

    capacity = deploy_script.check_capacity(source, target)

    assert capacity["required"] == 16 * 1024 + 2 * 512


def test_capacity_preflight_reclaims_partial_target_files(tmp_path, monkeypatch):
    source = tmp_path / "build"
    target = tmp_path / "CIRCUITPY"
    source.mkdir()
    target.mkdir()
    (source / "large.bmp").write_bytes(b"x" * 4096)
    (source / "code.py").write_text("run")
    files = ["large.bmp", "code.py"]
    (source / ".vpet-manifest.json").write_text(json.dumps({"files": files}))
    (target / "large.bmp").write_bytes(b"partial" * 512)
    (target / "code.py").write_text("old")

    Usage = namedtuple("Usage", "total used free")
    monkeypatch.setattr(deploy_script.shutil, "disk_usage", lambda _: Usage(8192, 5632, 2560))

    capacity = deploy_script.check_capacity(source, target, block_size=512, safety_margin=1024)

    assert capacity["reclaimable"] >= 4096


def test_capacity_preflight_does_not_budget_unchanged_files(tmp_path, monkeypatch):
    source = tmp_path / "build"
    target = tmp_path / "CIRCUITPY"
    source.mkdir()
    target.mkdir()
    (source / "large.bmp").write_bytes(b"same" * 1024)
    (target / "large.bmp").write_bytes(b"same" * 1024)
    files = ["large.bmp"]
    (source / ".vpet-manifest.json").write_text(json.dumps({"files": files}))

    Usage = namedtuple("Usage", "total used free")
    monkeypatch.setattr(deploy_script.shutil, "disk_usage", lambda _: Usage(8192, 7168, 1024))

    capacity = deploy_script.check_capacity(source, target, block_size=512, safety_margin=1024)

    assert capacity["required"] == 1024


def test_verify_deploy_detects_changed_file(tmp_path):
    source = tmp_path / "build"
    target = tmp_path / "CIRCUITPY"
    source.mkdir()
    target.mkdir()
    (source / "code.py").write_text("new")
    (source / ".vpet-manifest.json").write_text(json.dumps({"files": ["code.py"]}))
    (target / "code.py").write_text("old")

    try:
        deploy_script.verify_deploy(source, target)
    except deploy_script.DeploymentVerificationError as exc:
        assert "code.py" in str(exc)
    else:
        raise AssertionError("verification accepted a changed file")


def test_runtime_health_classifies_memory_and_traceback_errors():
    memory = deploy_script.runtime_error("Traceback\nMemoryError: allocation failed")
    generic = deploy_script.runtime_error("Traceback (most recent call last):\nValueError: bad")

    assert "ram" in memory.lower()
    assert "runtime" in generic.lower()
