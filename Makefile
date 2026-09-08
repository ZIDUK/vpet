# vPet dev workflow
# make help to see all targets

PY ?= python3
PORT ?=
UPLOAD_SPEED ?= 115200
SIM_PY := $(shell for p in "$(PY)" /usr/local/bin/python3 /Library/Frameworks/Python.framework/Versions/3.13/bin/python3 /usr/bin/python3; do \
	if [ -x "$$p" ] || command -v "$$p" >/dev/null 2>&1; then \
		"$$p" -c 'import pygame, PIL' >/dev/null 2>&1 && echo "$$p" && break; \
	fi; \
done)

.PHONY: help build build-pico build-tdisplay bootstrap-pio firmware native-test preflight deploy deploy-pico sim sim-pico sim-record test clean all

help:
	@echo "vPet dev workflow"
	@echo ""
	@echo "  make build        Build both T-Display and Pico artifacts"
	@echo "  make build-pico   Build the preserved 128x128 CircuitPython artifact"
	@echo "  make build-tdisplay Build the 240x135 T-Display simulator artifact"
	@echo "  make firmware     Compile the native ESP32 firmware"
	@echo "  make native-test  Test portable firmware logic on this Mac"
	@echo "  make preflight    Detect board and check memory without writing"
	@echo "  make deploy       Build + test + verified deploy + serial startup check"
	@echo "  make deploy-pico  Deploy the preserved CircuitPython build"
	@echo "  make sim          Run the vPet in a pygame window on Mac (no Pico needed)"
	@echo "  make sim-pico     Run the 128x128 Pico-compatible simulator"
	@echo "  make sim-record   Same as sim, but saves every frame as PNG to out/sim_frames/"
	@echo "  make test         Run pytest in tests/"
	@echo "  make all          Same verified pipeline as make deploy"
	@echo "  make clean        Remove the generated build/ directory"

build: build-pico build-tdisplay

build-pico:
	$(PY) scripts/build.py --profile pico --output build

build-tdisplay:
	$(PY) scripts/build.py --profile tdisplay --output build-tdisplay
	$(PY) scripts/build_tdisplay.py --sim-build build-tdisplay

bootstrap-pio:
	@bash scripts/bootstrap_platformio.sh

native-test: bootstrap-pio
	.venv-platformio/bin/pio test -d firmware/t-display -e native

firmware: build-tdisplay bootstrap-pio
	.venv-platformio/bin/pio run -d firmware/t-display -e tdisplay

deploy: test native-test firmware
	.venv-platformio/bin/python scripts/deploy_tdisplay.py --port "$(PORT)" --upload-speed "$(UPLOAD_SPEED)"

preflight: firmware
	.venv-platformio/bin/python scripts/deploy_tdisplay.py --preflight --port "$(PORT)"

deploy-pico: build-pico test
	$(PY) scripts/deploy.py

sim: build-tdisplay
	@if [ -z "$(SIM_PY)" ]; then echo "ERR: pygame and Pillow are required (python3 -m pip install pygame pillow)"; exit 1; fi
	$(SIM_PY) scripts/sim.py --profile tdisplay --build-dir build-tdisplay

sim-pico: build-pico
	@if [ -z "$(SIM_PY)" ]; then echo "ERR: pygame and Pillow are required (python3 -m pip install pygame pillow)"; exit 1; fi
	$(SIM_PY) scripts/sim.py --profile pico --build-dir build

sim-record: build-tdisplay
	@if [ -z "$(SIM_PY)" ]; then echo "ERR: pygame and Pillow are required (python3 -m pip install pygame pillow)"; exit 1; fi
	$(SIM_PY) scripts/sim.py --profile tdisplay --build-dir build-tdisplay --record out/sim_frames

test:
	$(PY) -m pytest tests/ -v

all: deploy

clean:
	@echo "  removing generated build directories"
	@rm -rf build build-tdisplay
