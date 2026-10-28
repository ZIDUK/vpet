"""Portable collection persistence, isolated from board and personal saves."""
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "firmware/t-display/lib/vpet_core/src"


@pytest.fixture(scope="module")
def collection_binary(tmp_path_factory):
    binary = tmp_path_factory.mktemp("collection-host") / "collection"
    sources = ("CollectionStore.cpp", "SettingsStore.cpp", "PetState.cpp", "Nutrition.cpp")
    result = subprocess.run(
        ["c++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-I", str(CORE),
         "-I", str(ROOT / "firmware/t-display/include"),
         str(ROOT / "tests/collection_store.cpp"),
         str(ROOT / "firmware/t-display/src/LittleFsCollectionRepository.cpp"),
         *[str(CORE / "vpet" / name) for name in sources], "-o", str(binary)],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return binary


@pytest.mark.parametrize("case", ["roundtrip", "migration", "switch", "eggs", "failures", "corruption", "filesystem", "compact", "compact_faults", "compact_timers", "egg_transfer"])
def test_collection_repository(collection_binary, case):
    result = subprocess.run([str(collection_binary), case], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr


def test_arduino_space_api_compiles_on_host(tmp_path):
    # Exercise the Arduino-specific branch without building/flashing the board.
    (tmp_path / "LittleFS.h").write_text(
        "#pragma once\n#include <stddef.h>\n"
        "struct CollectionSpaceStub { size_t totalBytes(); size_t usedBytes(); };\n"
        "extern CollectionSpaceStub LittleFS;\n", encoding="ascii",
    )
    result = subprocess.run(
        ["c++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-DARDUINO=10819",
         "-I", str(tmp_path), "-I", str(CORE),
         "-I", str(ROOT / "firmware/t-display/include"), "-c",
         str(ROOT / "firmware/t-display/src/LittleFsCollectionRepository.cpp"),
         "-o", str(tmp_path / "adapter.o")],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_collection_host_stack_frames_are_bounded(tmp_path):
    result = subprocess.run(
        ["c++", "-std=c++17", "-O2", "-fstack-usage", "-I", str(CORE), "-c",
         str(CORE / "vpet/CollectionStore.cpp"), "-o", str(tmp_path / "stack.o")],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    rows = (tmp_path / "stack.su").read_text().splitlines()
    frames = [(line.split("\t")[0], int(line.split("\t")[1])) for line in rows]
    # These frames nest under App, the panel, snapshot decoders and libc on an
    # 8 KiB ESP32 loop stack. A 3 KiB per-function allowance was not sufficient.
    assert frames and max(size for _, size in frames) <= 1024, frames


def test_collection_save_io_is_bounded(tmp_path):
    binary = tmp_path / "collection-io"
    result = subprocess.run(
        ["c++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-I", str(CORE),
         "-I", str(ROOT / "firmware/t-display/include"),
         str(ROOT / "tests/collection_repository_io.cpp"),
         *[str(CORE / "vpet" / (name + ".cpp")) for name in
           ("CollectionStore", "SettingsStore", "PetState", "Nutrition")],
         "-o", str(binary)], capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    result = subprocess.run([str(binary)], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
