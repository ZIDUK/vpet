from pathlib import Path
import subprocess
import pytest

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "firmware/t-display/lib/vpet_core/src"


def test_learning_scan_reuses_generation_streams_without_caching_validation(tmp_path):
    binary = tmp_path / "learning-io"
    result = subprocess.run([
        "c++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
        "-I", str(CORE), "-I", str(ROOT / "firmware/t-display/include"),
        str(ROOT / "tests/learning_repository_io.cpp"),
        str(ROOT / "firmware/t-display/src/LittleFsCollectionRepository.cpp"),
        *[str(CORE / "vpet" / (name + ".cpp")) for name in (
            "CollectionStore", "SettingsStore", "PetState", "Nutrition", "PracticeBattle")],
        "-o", str(binary),
    ], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    result = subprocess.run([str(binary), str(tmp_path)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_policy_files_atomic_refs_and_runtime_recovery(tmp_path):
    binary = tmp_path / "learning-runtime"
    result = subprocess.run([
        "c++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
        "-I", str(CORE), "-I", str(ROOT / "firmware/t-display/include"),
        str(ROOT / "tests/esp32_learning_runtime.cpp"),
        str(ROOT / "firmware/t-display/src/LearningRuntime.cpp"),
        str(ROOT / "firmware/t-display/src/LittleFsLearningRepository.cpp"),
        str(ROOT / "firmware/t-display/src/LittleFsCollectionRepository.cpp"),
        *[str(CORE / "vpet" / (name + ".cpp")) for name in (
            "CollectionStore", "SettingsStore", "PetState", "Nutrition", "PracticeBattle")],
        "-o", str(binary),
    ], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    result = subprocess.run([str(binary), str(tmp_path)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("compact", [False, True, "collection", "unreadable",
                                     "training_policy", "training_collection", "training_unreadable",
                                     "explore_policy", "explore_collection", "explore_unreadable",
                                     "async_success", "async_policy", "async_collection", "async_unreadable", "async_executor",
                                     "legacy_success", "legacy_reject", "legacy_pending", "legacy_destruct"])
def test_actual_esp32_app_learning_hooks_and_review_fixes(tmp_path, compact):
    binary = tmp_path / "learning-app"
    result = subprocess.run([
        "c++", "-std=c++17", "-include", str(ROOT / "tests/asset_stubs/Arduino.h"),
        "-I", str(ROOT / "tests/app_stubs"), "-I", str(ROOT / "tests/asset_stubs"),
        "-I", str(ROOT / "firmware/t-display/include"), "-I", str(CORE),
        str(ROOT / "tests/esp32_learning_app.cpp"),
        *[str(ROOT / "firmware/t-display/src" / (name + ".cpp")) for name in (
            "App", "CollectionPanel", "CollectionView", "LearningRuntime", "LittleFsLearningRepository", "LittleFsCollectionRepository")],
        *[str(CORE / "vpet" / (name + ".cpp")) for name in (
            "CollectionStore", "SettingsStore", "PetState", "Nutrition", "PracticeBattle",
            "Motion", "Navigation", "Evolution", "DateTimeMenu")],
        "-o", str(binary),
    ], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    result = subprocess.run([str(binary), str(tmp_path), *([str(compact)] if compact else [])], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_learning_arduino_adapter_and_host_stack_bounds(tmp_path):
    (tmp_path / "LittleFS.h").write_text(
        "#pragma once\n#include <stddef.h>\n"
        "struct LearningSpaceStub { size_t totalBytes(); size_t usedBytes(); };\n"
        "extern LearningSpaceStub LittleFS;\n", encoding="ascii")
    for name in ("LearningRuntime", "LittleFsLearningRepository"):
        for arduino in (False, True):
            output = tmp_path / (name + ("-arduino" if arduino else "") + ".o")
            result = subprocess.run([
                "c++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-O2", "-fstack-usage",
                *(["-DARDUINO=10819"] if arduino else []),
                "-I", str(tmp_path), "-I", str(CORE),
                "-I", str(ROOT / "firmware/t-display/include"), "-c",
                str(ROOT / "firmware/t-display/src" / (name + ".cpp")), "-o", str(output),
            ], capture_output=True, text=True)
            assert result.returncode == 0, result.stdout + result.stderr
            frames = [int(row.split("\t")[1]) for row in output.with_suffix(".su").read_text().splitlines()]
            assert frames and max(frames) <= 2048, (name, arduino, frames)
