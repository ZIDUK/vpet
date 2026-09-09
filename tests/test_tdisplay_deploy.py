"""Safe deployment checks for the classic ESP32 T-Display."""
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.deploy_tdisplay import deploy
from scripts.tdisplay_device import (
    BoardInfo,
    BuildReport,
    ReadyTelemetry,
    classify_memory,
    ensure_backup,
    parse_ready_line,
)


class FakeRunner:
    def __init__(self):
        self.calls = []

    def __call__(self, command, **kwargs):
        self.calls.append(list(map(str, command)))
        if "read_flash" in command:
            target = Path(command[-1])
            with target.open("wb") as handle:
                handle.truncate(int(str(command[-2]), 16))
        return SimpleNamespace(returncode=0, stdout="", stderr="")


def test_first_deploy_reads_flash_before_upload(tmp_path):
    board = BoardInfo("/dev/cu.test", "ESP32", "aabbcc", 16 << 20)
    runner = FakeRunner()

    deploy(
        board=board,
        output=tmp_path,
        runner=runner,
        build_report=BuildReport(100, 1000, 100, 1000, 100, 1000),
        telemetry_reader=lambda *_: ReadyTelemetry(100000, 80000, 16 << 20, 100, 1000, "1"),
    )

    read_index = next(i for i, call in enumerate(runner.calls) if "read_flash" in call)
    upload_index = next(i for i, call in enumerate(runner.calls) if "upload" in call)
    assert read_index < upload_index
    assert "115200" in runner.calls[read_index]


@pytest.mark.parametrize(
    ("build", "ready", "code"),
    [
        (BuildReport(91, 100, 10, 100, 10, 100), None, "FLASH_OVERFLOW"),
        (BuildReport(10, 100, 91, 100, 10, 100), None, "ASSET_STORAGE_OVERFLOW"),
        (BuildReport(10, 100, 10, 100, 101, 100), None, "STATIC_RAM_OVERFLOW"),
        (BuildReport(10, 100, 10, 100, 10, 100), ReadyTelemetry(65535, 60000, 0, 0, 0, "1"), "HEAP_STARTUP_LOW"),
    ],
)
def test_memory_failures_are_specific(build, ready, code):
    assert classify_memory(build, ready)[0].code == code


def test_ready_telemetry_parser():
    ready = parse_ready_line(
        "VPET_READY heap_free=121000 heap_min=99000 flash=16777216 "
        "fs_used=2921985 fs_total=12451840 manifest=1"
    )
    assert ready.heap_free == 121000
    assert ready.flash_size == 16 << 20
    assert ready.manifest == "1"


def test_firmware_presents_complete_frames_from_a_sprite_buffer():
    root = Path(__file__).parent.parent / "firmware" / "t-display"
    main = (root / "src" / "main.cpp").read_text()
    renderer = (root / "src" / "Renderer.cpp").read_text()
    panels = (root / "src" / "Panels.cpp").read_text()

    assert "TFT_eSprite framebuffer" in main
    assert "createSprite(240, 135)" in main
    assert "canvas_.pushSprite(0, 0)" in renderer
    assert "display_.pushSprite(0, 0)" in panels


def test_physical_buttons_use_left_for_next_and_right_for_action():
    source = (
        Path(__file__).parent.parent
        / "firmware" / "t-display" / "src" / "BoardInput.cpp"
    ).read_text()

    assert "kNextPin = 0" in source
    assert "kActionPin = 35" in source


def test_tdisplay_options_render_all_actions_and_wifi_result():
    source = (
        Path(__file__).parent.parent
        / "firmware" / "t-display" / "src" / "Panels.cpp"
    ).read_text()

    assert '\"DATE\", \"TIME\", \"BACK\"' in source
    assert "index < 8" in source
    assert 'wifi = \"WIFI: ONLINE\"' in source
    assert 'wifi = \"WIFI: NO INTERNET\"' in source
