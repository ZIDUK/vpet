#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$ROOT/.venv-platformio"

test -x "$VENV/bin/python" || python3 -m venv "$VENV"
"$VENV/bin/python" -m pip install --disable-pip-version-check \
    "platformio==6.2.0" \
    "intelhex==2.3.0"
"$VENV/bin/pio" --version
