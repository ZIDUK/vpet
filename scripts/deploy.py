#!/usr/bin/env python3
"""Deploy build/ to /Volumes/CIRCUITPY/ (the Pico's flash).

Steps:
  1. Verify CIRCUITPY is mounted.
  2. Copy code.py, settings.toml from build/ to /Volumes/CIRCUITPY/.
  3. Copy subdirs (Agumon/, Background/) only with files actually referenced in code.py.
  4. Sync CircuitPython libs to /Volumes/CIRCUITPY/lib/ from the cached bundle.
  5. Clean macOS AppleDouble noise (._*).

Does NOT delete files on the device that aren't in build/ — that's by design
to avoid wiping data the user might have added (e.g. /pet_save.json).
"""
import os
import re
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

CIRCUITPY = Path("/Volumes/CIRCUITPY")
BUNDLE_URL = "https://github.com/adafruit/Adafruit_CircuitPython_Bundle/releases/download/20251008/adafruit-circuitpython-bundle-10.x-mpy-20251008.zip"
BUNDLE_CACHE = Path.home() / ".cache" / "vpet" / "cp10_bundle.zip"
BUNDLE_VERSION = "20251008"

ROOT = Path(__file__).parent.parent
BUILD = ROOT / "build"


def verify_mounted():
    if not CIRCUITPY.exists():
        sys.exit(f"ERR: {CIRCUITPY} not mounted. Plug in Pico.")


def clean_apple_double():
    """Remove macOS ._* metadata files that leak onto FAT filesystems."""
    count = 0
    for p in CIRCUITPY.rglob("._*"):
        if p.is_file():
            p.unlink()
            count += 1
    # .Trashes and .fseventsd always come back, ignore them
    return count


def download_bundle():
    """Download CircuitPython lib bundle if not cached."""
    BUNDLE_CACHE.parent.mkdir(parents=True, exist_ok=True)
    if BUNDLE_CACHE.exists():
        return BUNDLE_CACHE
    print(f"  downloading {BUNDLE_URL}...")
    urllib.request.urlretrieve(BUNDLE_URL, BUNDLE_CACHE)
    return BUNDLE_CACHE


def scan_code_for_bmps():
    """Find BMP paths referenced in build/code.py."""
    code = (BUILD / "code.py").read_text()
    return set(re.findall(r'"(/[A-Za-z0-9_/]+\.bmp)"', code))


def deploy_runtime_files():
    """Copy code.py, settings.toml, and referenced BMPs to device."""
    referenced = scan_code_for_bmps()
    print(f"  referenced BMPs: {referenced}")

    # code.py
    shutil.copy2(BUILD / "code.py", CIRCUITPY / "code.py")
    print(f"  copied code.py")

    # settings.toml
    if (BUILD / "settings.toml").exists():
        shutil.copy2(BUILD / "settings.toml", CIRCUITPY / "settings.toml")
        print(f"  copied settings.toml")

    # Sprite + background dirs (only referenced files)
    for ref in referenced:
        rel = ref.lstrip("/")  # /Agumon/idle.bmp → Agumon/idle.bmp
        src = BUILD / rel
        dst = CIRCUITPY / rel
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            print(f"  copied {ref}")


def sync_libs():
    """Ensure CP 10 .mpy libs are on the device."""
    bundle = download_bundle()
    needed = ["adafruit_st7735r.mpy", "adafruit_debouncer.mpy", "adafruit_ticks.mpy"]
    needed_pkg = ["adafruit_imageload"]
    with zipfile.ZipFile(bundle) as zf:
        for name in needed:
            target = f"adafruit-circuitpython-bundle-10.x-mpy-{BUNDLE_VERSION}/lib/{name}"
            with zf.open(target) as src, open(CIRCUITPY / "lib" / name, "wb") as dst:
                shutil.copyfileobj(src, dst)
            print(f"  synced lib/{name}")
        for pkg in needed_pkg:
            base = f"adafruit-circuitpython-bundle-10.x-mpy-{BUNDLE_VERSION}/lib/{pkg}"
            for entry in zf.namelist():
                if entry.startswith(base + "/") and entry.endswith(".mpy"):
                    rel = entry.split("lib/")[1]
                    target = CIRCUITPY / "lib" / rel
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(entry) as src, open(target, "wb") as dst:
                        shutil.copyfileobj(src, dst)
            print(f"  synced lib/{pkg}/")


def main():
    print("=== deploy.py ===")
    verify_mounted()
    print(f"  CIRCUITPY mounted at {CIRCUITPY}")
    deploy_runtime_files()
    sync_libs()
    n = clean_apple_double()
    print(f"  cleaned {n} ._* files")
    print("OK. Reboot Pico to see changes.")


if __name__ == "__main__":
    main()
