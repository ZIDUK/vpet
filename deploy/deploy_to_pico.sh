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
echo "    wrote code.py"

# 3) Deploy lib/ from the official CircuitPython 10.x bundle
# We do NOT commit .mpy files to the repo (build artifacts, version-specific).
# Instead we download the right version on every deploy.
# See docs/hardware-notes.md for why this matters.
BUNDLE_URL="https://github.com/adafruit/Adafruit_CircuitPython_Bundle/releases/download/20250912/adafruit-circuitpython-bundle-10.x-mpy-20250912.zip"
BUNDLE_ZIP="/tmp/cp10_bundle.zip"
if [ ! -f "$BUNDLE_ZIP" ]; then
  echo "    downloading CP 10.x bundle (one-time)..."
  curl -sL -o "$BUNDLE_ZIP" "$BUNDLE_URL" || { echo "    bundle download failed"; exit 1; }
fi

mkdir -p "$DEVICE/lib"
for f in adafruit_st7735r.mpy adafruit_debouncer.mpy adafruit_ticks.mpy; do
  unzip -p "$BUNDLE_ZIP" "adafruit-circuitpython-bundle-10.x-mpy-20250912/lib/$f" \
    > "$DEVICE/lib/$f" 2>/dev/null && echo "    wrote lib/$f"
done

# 3b) Deploy adafruit_imageload (BMP only — skip PNG/GIF/PNM to save space)
if [ ! -d "$DEVICE/lib/adafruit_imageload/bmp" ] || [ ! -f "$DEVICE/lib/adafruit_imageload/__init__.mpy" ]; then
  mkdir -p "$DEVICE/lib/adafruit_imageload/bmp"
  for f in __init__.mpy displayio_types.mpy; do
    unzip -p "$BUNDLE_ZIP" "adafruit-circuitpython-bundle-10.x-mpy-20250912/lib/adafruit_imageload/$f" \
      > "$DEVICE/lib/adafruit_imageload/$f" 2>/dev/null && echo "    wrote lib/adafruit_imageload/$f"
  done
  for f in __init__.mpy indexed.mpy negative_height_check.mpy truecolor.mpy; do
    unzip -p "$BUNDLE_ZIP" "adafruit-circuitpython-bundle-10.x-mpy-20250912/lib/adafruit_imageload/bmp/$f" \
      > "$DEVICE/lib/adafruit_imageload/bmp/$f" 2>/dev/null && echo "    wrote lib/adafruit_imageload/bmp/$f"
  done
else
  echo "    lib/adafruit_imageload/ already present (skipped)"
fi

# (legacy adafruit_imageload section removed — handled by 3b above)

# 5) Deploy asset directories
# We scan code.py for all "/path/to/file.bmp" references and only copy those.
# This keeps the device lean: no unused sprites eating flash.
ASSETS_NEEDED=$(grep -oE '/[A-Za-z_][A-Za-z0-9_/]*\.bmp' "$REPO_ROOT/code.py" | sort -u)
for asset in $ASSETS_NEEDED; do
  src="$REPO_ROOT$asset"
  dest="$DEVICE$asset"
  mkdir -p "$(dirname "$dest")"
  if [ -f "$src" ]; then
    cp "$src" "$dest" 2>/dev/null && echo "    wrote $asset" || echo "    SKIP $asset (no space)"
  else
    echo "    MISSING $asset (not in repo)"
  fi
done

# 5b) Optional: also wipe any asset files on the device that are no longer referenced.
# We ask the user interactively to avoid surprise deletions. Skip for now.

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
