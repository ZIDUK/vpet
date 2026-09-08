"""Board discovery, backup and memory diagnostics for the T-Display."""
from dataclasses import dataclass
from datetime import datetime
import glob
import hashlib
from pathlib import Path
import re
import subprocess


APP_FREE_RATIO_MIN = 0.10
FS_FREE_RATIO_MIN = 0.10
STARTUP_HEAP_MIN = 64 * 1024
MIN_HEAP_MIN = 48 * 1024
READY_TIMEOUT_SECONDS = 15
BACKUP_BAUD = 115200
CRITICAL_BACKUP_OFFSET = 0x8000
CRITICAL_BACKUP_SIZE = 0x6000
ROOT = Path(__file__).parent.parent
PIO_PYTHON = ROOT / ".venv-platformio" / "bin" / "python"
ESPTOOL = Path.home() / ".platformio" / "packages" / "tool-esptoolpy" / "esptool.py"


@dataclass(frozen=True)
class BoardInfo:
    port: str
    chip: str
    chip_id: str
    flash_size: int


@dataclass(frozen=True)
class BuildReport:
    app_used: int
    app_capacity: int
    fs_used: int
    fs_capacity: int
    static_ram_used: int
    static_ram_capacity: int


@dataclass(frozen=True)
class ReadyTelemetry:
    heap_free: int
    heap_min: int
    flash_size: int
    fs_used: int
    fs_total: int
    manifest: str


@dataclass(frozen=True)
class Diagnostic:
    code: str
    message: str


def _run(runner, command):
    result = runner(command, capture_output=True, text=True, check=False)
    if result.returncode:
        detail = (result.stderr or result.stdout or "command failed").strip()
        raise RuntimeError(f"{detail}\nCommand: {' '.join(map(str, command))}")
    return (result.stdout or "") + (result.stderr or "")


def _esptool_command(port, action):
    if not PIO_PYTHON.is_file() or not ESPTOOL.is_file():
        raise RuntimeError("PlatformIO/esptool missing; run make bootstrap-pio")
    return [str(PIO_PYTHON), str(ESPTOOL), "--chip", "esp32", "--port", port, *action]


def detect_board(port=None, runner=subprocess.run):
    if not port:
        ports = sorted(
            set(glob.glob("/dev/cu.usbserial-*") + glob.glob("/dev/cu.SLAB_USBtoUART*"))
        )
        if len(ports) != 1:
            raise RuntimeError(
                f"Expected exactly one T-Display serial port, found {len(ports)}: {ports}. "
                "Set PORT=/dev/cu... explicitly."
            )
        port = ports[0]
    chip_output = _run(runner, _esptool_command(port, ["chip_id"]))
    flash_output = _run(runner, _esptool_command(port, ["flash_id"]))
    chip_match = re.search(r"Chip is ([^\r\n]+)", chip_output)
    id_match = re.search(r"(?:MAC|Chip ID):\s*([0-9a-fA-F:]+)", chip_output)
    flash_match = re.search(r"Detected flash size:\s*(\d+)MB", flash_output, re.I)
    if not id_match or not flash_match:
        raise RuntimeError("Could not verify ESP32 chip ID and flash size with esptool")
    return BoardInfo(
        port=port,
        chip=chip_match.group(1).strip() if chip_match else "ESP32",
        chip_id=id_match.group(1).replace(":", "").lower(),
        flash_size=int(flash_match.group(1)) * 1024 * 1024,
    )


def _sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_backup(board, output, runner=subprocess.run):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    pattern = f"{board.chip_id}-*-{board.flash_size // (1024 * 1024)}mb.bin"
    for candidate in sorted(output.glob(pattern)):
        checksum = candidate.with_suffix(candidate.suffix + ".sha256")
        if candidate.stat().st_size == board.flash_size and checksum.is_file():
            expected = checksum.read_text().split()[0]
            if expected == _sha256(candidate):
                return candidate
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = output / f"{board.chip_id}-{stamp}-{board.flash_size // (1024 * 1024)}mb.bin"
    _run(
        runner,
        _esptool_command(
            board.port,
            ["--baud", str(BACKUP_BAUD), "read_flash", "0x0", hex(board.flash_size), str(target)],
        ),
    )
    if target.stat().st_size != board.flash_size:
        raise RuntimeError(
            f"Backup size mismatch: expected {board.flash_size}, got {target.stat().st_size}"
        )
    digest = _sha256(target)
    target.with_suffix(target.suffix + ".sha256").write_text(f"{digest}  {target.name}\n")
    return target


def ensure_critical_backup(board, output, runner=subprocess.run):
    """Preserve the partition table and NVS without a slow full-flash read."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    pattern = f"{board.chip_id}-*-critical.bin"
    for candidate in sorted(output.glob(pattern)):
        checksum = candidate.with_suffix(candidate.suffix + ".sha256")
        if candidate.stat().st_size == CRITICAL_BACKUP_SIZE and checksum.is_file():
            if checksum.read_text().split()[0] == _sha256(candidate):
                return candidate
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = output / f"{board.chip_id}-{stamp}-critical.bin"
    _run(
        runner,
        _esptool_command(
            board.port,
            [
                "--baud", str(BACKUP_BAUD), "read_flash",
                hex(CRITICAL_BACKUP_OFFSET), hex(CRITICAL_BACKUP_SIZE), str(target),
            ],
        ),
    )
    if target.stat().st_size != CRITICAL_BACKUP_SIZE:
        raise RuntimeError("Critical board-state backup is incomplete")
    digest = _sha256(target)
    target.with_suffix(target.suffix + ".sha256").write_text(f"{digest}  {target.name}\n")
    return target


def parse_ready_line(line):
    fields = dict(re.findall(r"(\w+)=([^\s]+)", line))
    required = ("heap_free", "heap_min", "flash", "fs_used", "fs_total", "manifest")
    if not line.startswith("VPET_READY ") or any(key not in fields for key in required):
        raise ValueError("Invalid VPET_READY telemetry")
    return ReadyTelemetry(
        int(fields["heap_free"]),
        int(fields["heap_min"]),
        int(fields["flash"]),
        int(fields["fs_used"]),
        int(fields["fs_total"]),
        fields["manifest"],
    )


def classify_memory(report, telemetry=None):
    diagnostics = []
    if report.app_capacity <= 0 or (report.app_capacity - report.app_used) / report.app_capacity < APP_FREE_RATIO_MIN:
        diagnostics.append(Diagnostic("FLASH_OVERFLOW", "Firmware leaves less than 10% of the app partition free."))
    if report.fs_capacity <= 0 or (report.fs_capacity - report.fs_used) / report.fs_capacity < FS_FREE_RATIO_MIN:
        diagnostics.append(Diagnostic("ASSET_STORAGE_OVERFLOW", "Assets leave less than 10% of LittleFS free."))
    if report.static_ram_used > report.static_ram_capacity:
        diagnostics.append(Diagnostic("STATIC_RAM_OVERFLOW", "Static RAM exceeds ESP32 capacity."))
    if telemetry is not None:
        if telemetry.heap_free < STARTUP_HEAP_MIN:
            diagnostics.append(Diagnostic("HEAP_STARTUP_LOW", "Free heap at startup is below 64 KiB."))
        if telemetry.heap_min < MIN_HEAP_MIN:
            diagnostics.append(Diagnostic("HEAP_MIN_LOW", "Minimum observed heap is below 48 KiB."))
        if telemetry.flash_size != 16 * 1024 * 1024:
            diagnostics.append(Diagnostic("FLASH_SIZE_MISMATCH", "Runtime did not report the expected 16 MB flash."))
        if telemetry.manifest != "1":
            diagnostics.append(Diagnostic("ASSET_MANIFEST_INVALID", "Runtime did not validate asset manifest version 1."))
    return diagnostics
