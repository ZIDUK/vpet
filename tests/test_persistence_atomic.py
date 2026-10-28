import subprocess
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "firmware/t-display/lib/vpet_core/src"


@pytest.fixture(scope="module")
def persistence_binary(tmp_path_factory):
    binary = tmp_path_factory.mktemp("persistence") / "atomic"
    subprocess.run(["c++", "-std=c++11", "-I" + str(CORE),
                    str(ROOT / "tests/persistence_atomic.cpp"),
                    *[str(CORE / "vpet" / name) for name in
                      ("PetState.cpp", "Nutrition.cpp", "SettingsStore.cpp", "PracticeBattle.cpp")],
                    "-o", str(binary)], check=True)
    return binary


@pytest.mark.parametrize("case", ["save", "swap", "injury", "survival", "invalid", "recovery"])
def test_durable_operations(persistence_binary, case):
    result = subprocess.run([str(persistence_binary), case], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
