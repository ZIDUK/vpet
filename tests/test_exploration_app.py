from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "firmware/t-display/lib/vpet_core/src"


def test_actual_app_exploration_clock_and_transactions(tmp_path):
    binary = tmp_path / "explore-app"
    subprocess.run(["c++", "-std=c++17", "-I" + str(ROOT / "tests/app_stubs"),
                    "-I" + str(ROOT / "firmware/t-display/include"), "-I" + str(CORE),
                    str(ROOT / "tests/exploration_app.cpp"), str(ROOT / "firmware/t-display/src/App.cpp"),
                    *[str(CORE / "vpet" / (name + ".cpp")) for name in
                      ("PetState", "Nutrition", "SettingsStore", "PracticeBattle", "Motion", "Navigation", "Evolution", "DateTimeMenu")],
                    "-o", str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
