#!/bin/bash
# deploy/deploy_to_pico.sh
# Deploys runtime files (code.py, lib, assets) to a Pico W running CircuitPython
# mounted at /Volumes/CIRCUITPY (default) or a path passed as $1.
#
# Usage:
#   ./deploy/deploy_to_pico.sh                  # uses /Volumes/CIRCUITPY
#   ./deploy/deploy_to_pico.sh /Volumes/CIRCUITPY_WIFI

set -e

DEVICE="${1:-/Volumes/CIRCUITPY}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

echo "==> Deploying vPet to $DEVICE"
echo "    from $REPO_ROOT"

# Sanity check
if [ ! -d "$DEVICE" ]; then
  echo "ERROR: $DEVICE not mounted. Plug in your Pico and wait for CIRCUITPY to appear."
  exit 1
fi

# 0) Clean up macOS metadata junk (AppleDouble, .Trashes, .fseventsd)
# This stuff is created by macOS when files are written to FAT32 and wastes 4KB+ per file.
# We delete any matching files/dirs at the top level of the device.
for junk in "._*" ".Trashes" ".fseventsd" ".metadata_never_index" ".Spotlight-V100" ".DS_Store" ".TemporaryItems"; do
  find "$DEVICE" -maxdepth 1 -name "$junk" -exec rm -rf {} + 2>/dev/null || true
done
echo "    cleaned up macOS metadata"

# 1) Backup current code.py (so we can roll back)
if [ -f "$DEVICE/code.py" ]; then
  cp "$DEVICE/code.py" "$DEVICE/code.py.bak"
  echo "    backed up current code.py -> code.py.bak"
fi

# 2) Deploy code.py
cp "$REPO_ROOT/code.py" "$DEVICE/code.py"
echo "    wrote code.py (vPet v13.0)"

# 3) Deploy lib/ (only files we actually need)
mkdir -p "$DEVICE/lib"
for f in adafruit_st7735r.mpy adafruit_debouncer.mpy adafruit_ticks.mpy; do
  if [ -f "$REPO_ROOT/lib/$f" ]; then
    cp "$REPO_ROOT/lib/$f" "$DEVICE/lib/$f"
    echo "    wrote lib/$f"
  fi
done

# 4) Deploy adafruit_imageload (BMP only - no PNG/GIF/PNM to save space)
# Just make sure the BMP submodule is present, don't re-copy the whole tree
if [ ! -d "$DEVICE/lib/adafruit_imageload/bmp" ]; then
  mkdir -p "$DEVICE/lib/adafruit_imageload"
  if [ -f "$REPO_ROOT/lib/adafruit_imageload/__init__.mpy" ]; then
    cp "$REPO_ROOT/lib/adafruit_imageload/__init__.mpy" "$DEVICE/lib/adafruit_imageload/"
  fi
  if [ -f "$REPO_ROOT/lib/adafruit_imageload/displayio_types.mpy" ]; then
    cp "$REPO_ROOT/lib/adafruit_imageload/displayio_types.mpy" "$DEVICE/lib/adafruit_imageload/"
  fi
  if [ -d "$REPO_ROOT/lib/adafruit_imageload/bmp" ]; then
    cp -r "$REPO_ROOT/lib/adafruit_imageload/bmp" "$DEVICE/lib/adafruit_imageload/"
  fi
  echo "    wrote lib/adafruit_imageload/ (BMP only)"
else
  echo "    lib/adafruit_imageload/ already present (skipped)"
fi

# 5) Deploy asset directories
# Only deploy what the current code.py uses (BMPs from Agumon/, registerjungle.bmp).
# Avoid `rm -rf` on Agumon/ because deleting/recreating the directory on a full FAT
# filesystem is unreliable; we just copy the BMPs the code needs and let macOS metadata
# (`._*`) be cleaned by step 0 above.
for bmp in "$REPO_ROOT"/Agumon/*.bmp; do
  if [ -f "$bmp" ]; then
    cp "$bmp" "$DEVICE/Agumon/" 2>/dev/null && echo "    wrote Agumon/$(basename "$bmp")" || echo "    SKIP Agumon/$(basename "$bmp") (no space or other error)"
  fi
done
if [ -d "$REPO_ROOT/Background" ]; then
  mkdir -p "$DEVICE/Background"
  for bmp in "$REPO_ROOT"/Background/*.bmp; do
    if [ -f "$bmp" ]; then
      cp "$bmp" "$DEVICE/Background/" 2>/dev/null && echo "    wrote Background/$(basename "$bmp")"
    fi
  done
fi
# Icons: only deploy if code.py uses them (v14 doesn't). Skip for now.

# 6) Deploy settings.toml (wifi config, etc)
if [ -f "$REPO_ROOT/settings.toml" ]; then
  cp "$REPO_ROOT/settings.toml" "$DEVICE/settings.toml"
  echo "    wrote settings.toml"
fi

echo ""
echo "==> Deploy complete. The Pico will auto-reload in ~2 seconds."
echo "    If you see garbage on the screen, hard-reset by unplugging+replugging the USB."
echo ""
echo "    To roll back: mv $DEVICE/code.py.bak $DEVICE/code.py"
