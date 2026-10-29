"""Cancellation/fault injection against both real LittleFS storage adapters."""
from pathlib import Path
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
FIRMWARE = ROOT / "firmware/t-display"
CORE = FIRMWARE / "lib/vpet_core/src"


@pytest.fixture(scope="module")
def storage_interrupt_binary(tmp_path_factory):
    binary = tmp_path_factory.mktemp("storage-interrupt") / "host"
    result = subprocess.run([
        "c++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
        "-I", str(CORE), "-I", str(FIRMWARE / "include"),
        str(ROOT / "tests/storage_interrupt.cpp"),
        str(ROOT / "tests/storage_interrupt_stubs/collection.cpp"),
        str(ROOT / "tests/storage_interrupt_stubs/learning.cpp"),
        *[str(CORE / "vpet" / (name + ".cpp")) for name in (
            "CollectionStore", "SettingsStore", "PetState", "Nutrition", "PracticeBattle")],
        "-o", str(binary),
    ], capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    return binary


@pytest.mark.parametrize("case", [
    "collection_begin", "collection_read", "collection_write", "collection_prepared",
    "collection_validation", "collection_backup", "collection_before_publish",
    "collection_publish", "collection_rename_failure", "collection_write_failure",
    "collection_backup_rename_failure",
    "collection_read_failure", "collection_sync_failure", "collection_versions",
    "collection_fresh_validation", "callback_sampling", "policy_read", "policy_write",
    "policy_readback", "policy_before_publish", "policy_publish", "policy_rename_failure",
    "policy_write_failure", "policy_read_failure", "policy_sync_failure",
    "policy_directory_sync_failure", "policy_existing", "gc_current", "gc_previous",
    "gc_remove", "gc_corruption", "gc_future", "gc_versions", "cancel_sweep",
])
def test_real_storage_interrupt(storage_interrupt_binary, tmp_path, case):
    result = subprocess.run([str(storage_interrupt_binary), case, str(tmp_path)],
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.fixture(scope="module")
def checkpoint_interrupt_binary(tmp_path_factory):
    binary = tmp_path_factory.mktemp("checkpoint-interrupt") / "host"
    result = subprocess.run([
        "c++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
        "-include", str(ROOT / "tests/asset_stubs/Arduino.h"),
        "-I", str(ROOT / "tests/app_stubs"), "-I", str(ROOT / "tests/asset_stubs"),
        "-I", str(CORE), "-I", str(FIRMWARE / "include"),
        str(ROOT / "tests/storage_interrupt_stubs/checkpoint.cpp"),
        str(ROOT / "tests/storage_interrupt_stubs/collection.cpp"),
        str(ROOT / "tests/storage_interrupt_stubs/learning.cpp"),
        *[str(FIRMWARE / "src" / (name + ".cpp")) for name in (
            "CollectionPanel", "CollectionView", "LearningRuntime")],
        *[str(CORE / "vpet" / (name + ".cpp")) for name in (
            "CollectionStore", "SettingsStore", "PetState", "Nutrition", "PracticeBattle")],
        "-o", str(binary),
    ], capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    return binary


@pytest.mark.parametrize("case", ["load", "policy", "backup", "backup_publish", "publish"])
def test_checkpoint_interrupt_does_not_latch_error(checkpoint_interrupt_binary, tmp_path, case):
    result = subprocess.run([str(checkpoint_interrupt_binary), case, str(tmp_path)],
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
