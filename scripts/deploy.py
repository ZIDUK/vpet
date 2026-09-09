#!/usr/bin/env python3
"""Synchronize the generated build artifact to a CircuitPython device."""
import json
import glob
import hashlib
import errno
import os
import shutil
import subprocess
import sys
import time
import urllib.request
import zipfile
from pathlib import Path


CIRCUITPY = Path("/Volumes/CIRCUITPY")
BUNDLE_VERSION = "20251008"
BUNDLE_URL = (
    "https://github.com/adafruit/Adafruit_CircuitPython_Bundle/releases/download/"
    f"{BUNDLE_VERSION}/adafruit-circuitpython-bundle-10.x-mpy-{BUNDLE_VERSION}.zip"
)
BUNDLE_CACHE = Path.home() / ".cache" / "vpet" / "cp10_bundle.zip"

ROOT = Path(__file__).parent.parent
BUILD = ROOT / "build"
MANIFEST = ".vpet-manifest.json"
LEGACY_RUNTIME_FILES = {
    "app.py",
    "hal.py",
    "config.py",
    "boot.py",
    "code.py",
    "settings.toml",
}
LEGACY_ASSET_FILES = {
    "Background/jungle.bmp",
    "UI/buttons/feed.bmp",
    "UI/buttons/heal.bmp",
    "UI/buttons/play.bmp",
    "UI/buttons/rest.bmp",
    "digimon1/Baby/idle_atlas.bmp",
    "digimon1/Champion/idle_atlas.bmp",
    "digimon1/Mega/idle_atlas.bmp",
    "digimon1/Rookie/idle_atlas.bmp",
    "digimon1/Rookie/rookie_screenshot.bmp",
    "digimon1/Ultimate/idle_atlas.bmp",
}
LEGACY_EMPTY_DIRECTORIES = (
    "lib/adafruit_imageload/pnm/pgm",
    "lib/adafruit_imageload/pnm",
    "lib/adafruit_imageload/bmp",
    "lib/adafruit_imageload",
    "data/digimon",
    "data/npcs",
    "data",
    "UI/buttons",
    "UI",
    "UIAssets/buttons",
    "UIAssets",
    "digimon1/Baby",
    "digimon1/Champion",
    "digimon1/Egg",
    "digimon1/Mega",
    "digimon1/Ultimate",
)


class DeploymentSpaceError(RuntimeError):
    pass


class DeploymentVerificationError(RuntimeError):
    pass


class DeploymentRuntimeError(RuntimeError):
    pass


def verify_mounted(target=CIRCUITPY):
    if not target.is_dir():
        sys.exit(f"ERR: {target} not mounted. Plug in Pico.")


def _load_manifest(path):
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError):
        return set()
    return set(data.get("files", []))


def _allocated_size(size, block_size):
    return ((size + block_size - 1) // block_size) * block_size


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def files_match(source, target):
    """Return whether two files contain exactly the same bytes."""
    try:
        return source.is_file() and target.is_file() and _sha256(source) == _sha256(target)
    except OSError:
        return False


def check_capacity(source, target, block_size=None, safety_margin=16 * 1024):
    """Fail before copying when the generated artifact cannot fit in flash."""
    files = _load_manifest(source / MANIFEST)
    if not files:
        raise ValueError(f"Missing or empty build manifest: {source / MANIFEST}")
    if block_size is None:
        # st_blksize is 1 MiB for macOS FAT mounts even when the volume's
        # allocation unit is 512 bytes. statvfs.f_frsize reflects the latter.
        block_size = max(512, os.statvfs(target).f_frsize)

    old_files = _load_manifest(target / MANIFEST)
    changed_files = {
        relative
        for relative in files
        if not files_match(source / relative, target / relative)
    }

    required = safety_margin
    for relative in changed_files:
        required += _allocated_size((source / relative).stat().st_size, block_size)
        required += block_size  # transient AppleDouble metadata on macOS

    reclaimable = 0
    replaceable_files = changed_files | (old_files - files)
    for relative in replaceable_files:
        try:
            reclaimable += _allocated_size((target / relative).stat().st_size, block_size)
        except OSError:
            pass
    free = shutil.disk_usage(target).free
    available = free + reclaimable
    if required > available:
        raise DeploymentSpaceError(
            "CIRCUITPY flash capacity check failed: "
            f"required {required} bytes, available {available} bytes "
            f"({free} free + {reclaimable} reclaimable). "
            "Reduce BMP sizes or remove unused runtime files."
        )
    return {
        "required": required,
        "free": free,
        "reclaimable": reclaimable,
        "changed": len(changed_files),
    }


def verify_deploy(source, target):
    """Verify every managed file byte-for-byte after copying."""
    mismatches = []
    for relative in sorted(_load_manifest(source / MANIFEST)):
        source_path = source / relative
        target_path = target / relative
        try:
            matches = _sha256(source_path) == _sha256(target_path)
        except OSError:
            matches = False
        if not matches:
            mismatches.append(relative)
    if mismatches:
        raise DeploymentVerificationError(
            "Post-deploy hash verification failed: " + ", ".join(mismatches)
        )
    return len(_load_manifest(source / MANIFEST))


def runtime_error(output):
    """Return a user-facing diagnosis for CircuitPython serial output."""
    if "MemoryError" in output:
        return "CircuitPython RAM error: MemoryError reported during startup."
    markers = ("Traceback", "ImportError", "SyntaxError", "NameError", "OSError:")
    if any(marker in output for marker in markers):
        return "CircuitPython runtime error reported during startup."
    return None


def open_serial_monitor():
    ports = sorted(glob.glob("/dev/cu.usbmodem*"))
    if not ports:
        raise DeploymentRuntimeError("No CircuitPython serial port found for runtime verification.")
    try:
        import serial
    except ImportError as error:
        raise DeploymentRuntimeError(
            "pyserial is required for runtime verification: python3 -m pip install pyserial"
        ) from error
    try:
        connection = serial.Serial(ports[0], 115200, timeout=0.1)
        connection.reset_input_buffer()
        return connection, ports[0]
    except OSError as error:
        raise DeploymentRuntimeError(f"Cannot open CircuitPython serial port {ports[0]}: {error}") from error


def restart_and_monitor(connection, seconds=6):
    """Soft-reboot CircuitPython and capture startup output."""
    connection.write(b"\x03")
    connection.flush()
    time.sleep(0.3)
    connection.reset_input_buffer()
    connection.write(b"\x04")
    connection.flush()

    deadline = time.monotonic() + seconds
    chunks = []
    while time.monotonic() < deadline:
        waiting = connection.in_waiting
        data = connection.read(waiting or 1)
        if data:
            chunks.append(data)
        time.sleep(0.05)
    output = b"".join(chunks).decode("utf-8", errors="replace")
    diagnosis = runtime_error(output)
    if diagnosis:
        raise DeploymentRuntimeError(f"{diagnosis}\n--- serial output ---\n{output.strip()}")
    return output


def clear_extended_attributes(path):
    """Remove macOS metadata before it accumulates as 4 KB FAT sidecars."""
    try:
        subprocess.run(
            ["/usr/bin/xattr", "-c", str(path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except FileNotFoundError:
        pass
    safe_unlink(path.parent / ("._" + path.name))


def safe_copy2(source, target, max_retries=3, delay=0.5):
    """Copy bytes without extended metadata, with retries for the Pico race."""
    last_error = None
    for attempt in range(max_retries):
        try:
            safe_unlink(target.parent / ("._" + target.name))
            safe_unlink(target)
            with open(source, "rb") as source_handle, open(target, "wb") as target_handle:
                shutil.copyfileobj(source_handle, target_handle, length=8192)
                target_handle.flush()
                os.fsync(target_handle.fileno())
            clear_extended_attributes(target)
            return
        except OSError as error:
            last_error = error
            if error.errno != 22:
                raise
            time.sleep(delay * (attempt + 1))
    raise last_error


def safe_unlink(path, max_retries=3, delay=0.2):
    for attempt in range(max_retries):
        try:
            path.unlink()
            return
        except FileNotFoundError:
            return
        except OSError as error:
            if error.errno != 22 or attempt == max_retries - 1:
                raise
            time.sleep(delay * (attempt + 1))


def safe_rmdir(path, max_retries=3, delay=0.2):
    """Remove a known legacy directory only when it is empty."""
    for attempt in range(max_retries):
        try:
            path.rmdir()
            return True
        except FileNotFoundError:
            return False
        except OSError as error:
            if error.errno in (errno.ENOTEMPTY, errno.EEXIST):
                return False
            if error.errno != errno.EINVAL or attempt == max_retries - 1:
                raise
            time.sleep(delay * (attempt + 1))


def sync_build(source, target):
    """Make all vPet-managed files on target match a build manifest."""
    manifest_path = source / MANIFEST
    new_files = _load_manifest(manifest_path)
    if not new_files:
        raise ValueError(f"Missing or empty build manifest: {manifest_path}")

    target.mkdir(parents=True, exist_ok=True)
    old_files = _load_manifest(target / MANIFEST)

    # Remove root-level files that belonged to an older manifest.
    for relative in sorted(old_files - new_files):
        safe_unlink(target / relative)

    for filename in LEGACY_RUNTIME_FILES - new_files:
        safe_unlink(target / filename)
    for relative in LEGACY_ASSET_FILES - new_files:
        safe_unlink(target / relative)
    for relative in LEGACY_EMPTY_DIRECTORIES:
        safe_rmdir(target / relative)

    changed_files = {
        relative
        for relative in new_files
        if not files_match(source / relative, target / relative)
    }

    copied = 0
    for relative in sorted(new_files - {"code.py"}):
        source_path = source / relative
        if not source_path.is_file():
            raise FileNotFoundError(f"Manifest entry does not exist: {source_path}")
        if relative not in changed_files:
            continue
        target_path = target / relative
        target_path.parent.mkdir(parents=True, exist_ok=True)
        safe_copy2(source_path, target_path)
        copied += 1

    if not files_match(manifest_path, target / MANIFEST):
        safe_copy2(manifest_path, target / MANIFEST)

    # code.py is copied last so CircuitPython reloads only after every module
    # and asset needed by the new application is already present.
    code_source = source / "code.py"
    if "code.py" not in new_files or not code_source.is_file():
        raise FileNotFoundError("build/code.py is missing from the manifest")
    if changed_files:
        safe_copy2(code_source, target / "code.py")
        copied += 1
    return copied


def clean_apple_double(target=CIRCUITPY):
    count = 0
    for path in target.rglob("._*"):
        if path.is_file():
            path.unlink()
            count += 1
    return count


def download_bundle():
    BUNDLE_CACHE.parent.mkdir(parents=True, exist_ok=True)
    if not BUNDLE_CACHE.exists():
        print(f"  downloading {BUNDLE_URL}...")
        urllib.request.urlretrieve(BUNDLE_URL, BUNDLE_CACHE)
    return BUNDLE_CACHE


def sync_libs(target=CIRCUITPY):
    """Install the CircuitPython 10 libraries required by the runtime."""
    bundle = download_bundle()
    library_dir = target / "lib"
    library_dir.mkdir(parents=True, exist_ok=True)
    prefix = f"adafruit-circuitpython-bundle-10.x-mpy-{BUNDLE_VERSION}/lib/"
    standalone = ("adafruit_st7735r.mpy", "adafruit_debouncer.mpy", "adafruit_ticks.mpy")

    unused_package = library_dir / "adafruit_imageload"
    if unused_package.exists():
        for path in unused_package.rglob("*"):
            if path.is_file():
                safe_unlink(path)

    with zipfile.ZipFile(bundle) as archive:
        for filename in standalone:
            target_path = library_dir / filename
            payload = archive.read(prefix + filename)
            try:
                unchanged = target_path.read_bytes() == payload
            except OSError:
                unchanged = False
            if unchanged:
                continue
            safe_unlink(target_path.parent / ("._" + target_path.name))
            safe_unlink(target_path)
            with open(target_path, "wb") as output:
                output.write(payload)
                output.flush()
                os.fsync(output.fileno())
            clear_extended_attributes(target_path)


def main():
    print("=== deploy.py ===")
    verify_mounted()
    try:
        clean_apple_double()
        sync_libs()
        capacity = check_capacity(BUILD, CIRCUITPY)
        print(
            f"  flash preflight: {capacity['required']} required, "
            f"{capacity['free']} free, {capacity['reclaimable']} reclaimable, "
            f"{capacity['changed']} changed"
        )
        serial_connection, serial_port = open_serial_monitor()
        try:
            copied = sync_build(BUILD, CIRCUITPY)
            cleaned = clean_apple_double()
            verified = verify_deploy(BUILD, CIRCUITPY)
            print(f"  synced {copied} build files")
            print(f"  verified {verified} file hashes")
            print(f"  cleaned {cleaned} AppleDouble files")
            print(f"  runtime check: soft reboot via {serial_port}")
            restart_and_monitor(serial_connection)
        finally:
            serial_connection.close()
    except DeploymentSpaceError as error:
        sys.exit(f"ERR: {error}")
    except DeploymentVerificationError as error:
        sys.exit(f"ERR: {error}")
    except DeploymentRuntimeError as error:
        sys.exit(f"ERR: {error}")
    except OSError as error:
        if error.errno == 28:
            sys.exit("ERR: CIRCUITPY flash is full (ENOSPC). Build was not activated.")
        raise
    print("OK. Build verified and CircuitPython started without reported errors.")


if __name__ == "__main__":
    main()
