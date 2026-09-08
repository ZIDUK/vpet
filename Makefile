# vPet dev workflow
# make help to see all targets

PY ?= python3
SIM_PY := $(shell for p in "$(PY)" /usr/local/bin/python3 /Library/Frameworks/Python.framework/Versions/3.13/bin/python3 /usr/bin/python3; do \
	if [ -x "$$p" ] || command -v "$$p" >/dev/null 2>&1; then \
		"$$p" -c 'import pygame, PIL' >/dev/null 2>&1 && echo "$$p" && break; \
	fi; \
done)

.PHONY: help build deploy deploy-pico sim sim-pico sim-record test clean all

help:
	@echo "vPet dev workflow"
	@echo ""
	@echo "  make build        src/ + assets/ → build/  (clean rebuild)"
	@echo "  make deploy       Build + test + verified deploy + serial startup check"
	@echo "  make deploy-pico  Deploy the preserved CircuitPython build"
	@echo "  make sim          Run the vPet in a pygame window on Mac (no Pico needed)"
	@echo "  make sim-pico     Run the 128x128 Pico-compatible simulator"
	@echo "  make sim-record   Same as sim, but saves every frame as PNG to out/sim_frames/"
	@echo "  make test         Run pytest in tests/"
	@echo "  make all          Same verified pipeline as make deploy"
	@echo "  make clean        Remove the generated build/ directory"

build:
	$(PY) scripts/build.py

deploy: build test
	$(PY) scripts/deploy.py

deploy-pico: build test
	$(PY) scripts/deploy.py

sim: build
	@if [ -z "$(SIM_PY)" ]; then echo "ERR: pygame and Pillow are required (python3 -m pip install pygame pillow)"; exit 1; fi
	$(SIM_PY) scripts/sim.py --profile pico --build-dir build

sim-pico: build
	@if [ -z "$(SIM_PY)" ]; then echo "ERR: pygame and Pillow are required (python3 -m pip install pygame pillow)"; exit 1; fi
	$(SIM_PY) scripts/sim.py --profile pico --build-dir build

sim-record: build
	@if [ -z "$(SIM_PY)" ]; then echo "ERR: pygame and Pillow are required (python3 -m pip install pygame pillow)"; exit 1; fi
	$(SIM_PY) scripts/sim.py --record out/sim_frames

test:
	$(PY) -m pytest tests/ -v

all: deploy

clean:
	@echo "  removing generated build/"
	@rm -rf build
