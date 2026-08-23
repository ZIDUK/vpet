# vPet dev workflow
# make help to see all targets

PY := python3

.PHONY: help build deploy sim test clean all

help:
	@echo "vPet dev workflow"
	@echo ""
	@echo "  make build    Flatten src/ → build/code.py"
	@echo "  make deploy   Copy build/ → /Volumes/CIRCUITPY/  (the Pico)"
	@echo "  make sim      Run the vPet in a pygame window on Mac"
	@echo "  make test     Run pytest in tests/"
	@echo "  make all      build + test + deploy"
	@echo "  make clean    Remove build/code.py"

build:
	$(PY) scripts/build.py

deploy: build
	$(PY) scripts/deploy.py

sim:
	$(PY) scripts/simulator.py

test:
	$(PY) -m pytest tests/ -v

all: build test deploy

clean:
	rm -f build/code.py
