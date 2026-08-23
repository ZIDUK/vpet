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

# 4) Deploy adafruit_imageload (used for sprite loading)
if [ -d "$REPO_ROOT/lib/adafruit_imageload" ]; then
  rm -rf "$DEVICE/lib/adafruit_imageload"
  cp -r "$REPO_ROOT/lib/adafruit_imageload" "$DEVICE/lib/"
  echo "    wrote lib/adafruit_imageload/"
fi

# 5) Deploy asset directories
for dir in Agumon Background icons; do
  if [ -d "$REPO_ROOT/$dir" ]; then
    rm -rf "$DEVICE/$dir"
    cp -r "$REPO_ROOT/$dir" "$DEVICE/"
    echo "    wrote $dir/"
  fi
done

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
