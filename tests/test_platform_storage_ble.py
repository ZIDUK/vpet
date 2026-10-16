"""Bounded host checks of the real platform adapters, without PlatformIO."""
from pathlib import Path
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
ADAPTERS = ROOT / "tests/platform_adapters"


@pytest.fixture(scope="module")
def adapter_host(tmp_path_factory):
    binary = tmp_path_factory.mktemp("platform-adapters") / "host"
    firmware = ROOT / "firmware/t-display"
    command = [
        "c++", "-std=c++17", "-pthread", "-Wall", "-Wextra", "-Werror",
        "-I", str(ADAPTERS), "-I", str(firmware / "include"),
        "-I", str(firmware / "lib/vpet_core/src"),
        str(ADAPTERS / "host.cpp"), str(firmware / "src/NvsKeyValueStore.cpp"),
        str(firmware / "src/BleService.cpp"),
        *[str(firmware / "lib/vpet_core/src/vpet" / name) for name in
          ("SettingsStore.cpp", "PetState.cpp", "Nutrition.cpp", "PracticeBattle.cpp")],
        "-o", str(binary),
    ]
    subprocess.run(command, check=True, capture_output=True, text=True, timeout=60)
    return binary


@pytest.mark.parametrize("case", [
    "nvs_nonempty", "nvs_empty", "nvs_failures", "nvs_namespace",
    "nvs_pending", "nvs_pending_empty", "nvs_pending_int", "nvs_rejected", "nvs_handle_ownership",
    "settings_pending", "settings_pending_reboot_old", "settings_pending_reboot_new",
    "settings_mirror_pending", "settings_mirror_reboot", "settings_clear_pending",
    "settings_save_pending", "settings_save_mirror_pending", "settings_save_mirror_reboot",
    "settings_items_pending", "settings_items_mirror_pending", "settings_items_mirror_reboot",
    "swap_marker_reboot_old", "swap_marker_reboot_new",
    "swap_stage_live_volatile", "swap_stage_live_durable",
    "swap_stage_back_volatile", "swap_stage_back_durable",
    "swap_backup_coordinator", "swap_backup_reboot",
    "ble_lifecycle", "ble_stop_callbacks", "ble_start_callback",
    "ble_name", "ble_failures", "ble_deinit_failure", "ble_stress",
])
def test_real_platform_adapters(adapter_host, case):
    result = subprocess.run([str(adapter_host), case], capture_output=True,
                            text=True, timeout=10)
    assert result.returncode == 0, result.stdout + result.stderr
