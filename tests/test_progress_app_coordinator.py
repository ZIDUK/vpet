from pathlib import Path
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "firmware/t-display/lib/vpet_core/src/vpet"


@pytest.fixture(scope="module")
def coordinator(tmp_path_factory):
    binary = tmp_path_factory.mktemp("progress-coordinator") / "app"
    result = subprocess.run([
        "c++", "-std=c++17", "-include", str(ROOT / "tests/asset_stubs/Arduino.h"),
        "-I" + str(ROOT / "tests/progress_clock_stubs"),
        "-I" + str(ROOT / "tests/progress_app_stubs"),
        "-I" + str(ROOT / "tests/app_stubs"), "-I" + str(ROOT / "tests/asset_stubs"),
        "-I" + str(ROOT / "firmware/t-display/include"), "-I" + str(CORE.parent),
        str(ROOT / "tests/progress_app_coordinator.cpp"),
        *[str(ROOT / "firmware/t-display/src" / (name + ".cpp")) for name in (
            "App", "CollectionPanel", "CollectionView", "LearningRuntime")],
        *[str(CORE / (name + ".cpp")) for name in (
            "CollectionStore", "PetState", "Nutrition", "SettingsStore", "PracticeBattle",
            "Motion", "Navigation", "Evolution", "DateTimeMenu")],
        "-o", str(binary),
    ], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    return binary


@pytest.mark.parametrize("scenario", ["settings", "training_queue", "queue", "overflow", "care",
                                     "care_reject", "food_repeat", "food_repeat_reject",
                                     "settings_reject", "training_reject",
                                     "accepted_pending", "maintenance", "sleep", "collection",
                                     "capacity", "stress", "explore", "explore_reject", "battle",
                                     "battle_reject", "clock", "clock_reject", "warning", "legacy",
                                     "permanent_back_rejected_idle", "permanent_back_rejected_retry",
                                     "permanent_back_accepted_idle", "permanent_back_accepted_retry"])
def test_progress_coordinator_uses_one_worker_and_replays_inputs(coordinator, scenario):
    result = subprocess.run([str(coordinator), scenario], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == "PROGRESS_COORDINATOR_OK"
