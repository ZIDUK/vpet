from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "firmware/t-display/lib/vpet_core/src"


def test_nine_menu_entries_and_exploration_navigation(tmp_path):
    binary = tmp_path / "navigation"
    subprocess.run(["c++", "-std=c++17", "-I" + str(CORE),
                    str(ROOT / "tests/exploration_navigation.cpp"),
                    str(CORE / "vpet/Navigation.cpp"), "-o", str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
