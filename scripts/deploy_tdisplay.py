#!/usr/bin/env python3
"""Safely back up, validate, flash and verify the LILYGO T-Display."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.tdisplay_device import (
    BoardInfo,
    BuildReport,
    READY_TIMEOUT_SECONDS,
    ReadyTelemetry,
    classify_memory,
    detect_board,
    ensure_critical_backup,
    parse_ready_line,
)


FIRMWARE = ROOT / "firmware" / "t-display"
PIO = ROOT / ".venv-platformio" / "bin" / "pio"
BACKUPS = ROOT / "out" / "board-backups"
APP_CAPACITY = 0x400000
FS_CAPACITY = 0xBE0000
RAM_CAPACITY = 327680


def _run(runner, command):
    result = runner(command, capture_output=True, text=True, check=False)
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout or "command failed").strip())
    return (result.stdout or "") + (result.stderr or "")


def inspect_build(runner=subprocess.run):
    firmware_bin = FIRMWARE / ".pio" / "build" / "tdisplay" / "firmware.bin"
    manifest_path = FIRMWARE / "data" / "manifest.json"
    if not firmware_bin.is_file() or not manifest_path.is_file():
        raise RuntimeError("Build artifacts missing; run make firmware first")
    output = _run(runner, [str(PIO), "run", "-d", str(FIRMWARE), "-e", "tdisplay"])
    matches = re.findall(r"used\s+(\d+)\s+bytes\s+from\s+(\d+)\s+bytes", output)
    static_used, static_capacity = (map(int, matches[0]) if matches else (0, RAM_CAPACITY))
    app_used = int(matches[1][0]) if len(matches) > 1 else firmware_bin.stat().st_size
    manifest = json.loads(manifest_path.read_text())
    fs_used = sum(item["bytes"] for item in manifest["assets"]) + manifest_path.stat().st_size
    return BuildReport(
        app_used,
        APP_CAPACITY,
        fs_used,
        FS_CAPACITY,
        static_used,
        static_capacity,
    )


def read_ready(port, timeout=READY_TIMEOUT_SECONDS):
    try:
        import serial
    except ImportError as error:
        raise RuntimeError("pyserial is required; run make bootstrap-pio") from error
    deadline = time.monotonic() + timeout
    lines = []
    with serial.Serial(port, 115200, timeout=0.2) as connection:
        connection.dtr = False
        connection.rts = False
        while time.monotonic() < deadline:
            raw = connection.readline()
            if not raw:
                continue
            line = raw.decode("utf-8", errors="replace").strip()
            lines.append(line)
            if line.startswith("VPET_READY "):
                return parse_ready_line(line)
    raise RuntimeError("No VPET_READY line after reset. Serial output:\n" + "\n".join(lines[-20:]))


def _fail_on_diagnostics(report, telemetry=None):
    diagnostics = classify_memory(report, telemetry)
    if diagnostics:
        raise RuntimeError("\n".join(f"{item.code}: {item.message}" for item in diagnostics))


def deploy(
    port=None,
    upload_speed=115200,
    board=None,
    output=BACKUPS,
    runner=subprocess.run,
    build_report=None,
    telemetry_reader=read_ready,
):
    board = board or detect_board(port, runner=runner)
    if board.flash_size != 16 * 1024 * 1024:
        raise RuntimeError(f"Expected 16 MB flash, detected {board.flash_size} bytes")
    report = build_report or inspect_build(runner)
    _fail_on_diagnostics(report)
    if upload_speed != 115200:
        raise RuntimeError(
            "UPLOAD_SPEED must match firmware/t-display/platformio.ini (115200)"
        )
    backup = ensure_critical_backup(board, output, runner=runner)
    print(f"Board: {board.chip} id={board.chip_id} flash={board.flash_size} port={board.port}")
    print(f"Backup: {backup}")
    common = [
        str(PIO), "run", "-d", str(FIRMWARE), "-e", "tdisplay",
        "--upload-port", board.port,
    ]
    _run(runner, [*common, "-t", "upload"])
    _run(runner, [*common, "-t", "uploadfs"])
    telemetry = telemetry_reader(board.port, READY_TIMEOUT_SECONDS)
    _fail_on_diagnostics(report, telemetry)
    print(
        "Deploy OK: "
        f"heap_free={telemetry.heap_free} heap_min={telemetry.heap_min} "
        f"fs={telemetry.fs_used}/{telemetry.fs_total} manifest={telemetry.manifest}"
    )
    return telemetry


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port")
    parser.add_argument("--upload-speed", type=int, default=115200)
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    board = detect_board(args.port)
    report = inspect_build()
    _fail_on_diagnostics(report)
    print(f"Board: {board.chip} id={board.chip_id} flash={board.flash_size} port={board.port}")
    print(
        f"Budgets: app={report.app_used}/{report.app_capacity} "
        f"littlefs={report.fs_used}/{report.fs_capacity} "
        f"static_ram={report.static_ram_used}/{report.static_ram_capacity}"
    )
    if not args.preflight:
        deploy(args.port, args.upload_speed, board=board, build_report=report)


if __name__ == "__main__":
    main()
