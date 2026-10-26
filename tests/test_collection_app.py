from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "firmware/t-display/lib/vpet_core/src/vpet"


def test_collection_app_runtime_and_transactions(tmp_path):
    binary = tmp_path / "collection-app"
    subprocess.run([
        "c++", "-std=c++17", "-include", str(ROOT / "tests/asset_stubs/Arduino.h"),
        "-I" + str(ROOT / "tests/app_stubs"),
        "-I" + str(ROOT / "tests/asset_stubs"),
        "-I" + str(ROOT / "firmware/t-display/include"), "-I" + str(CORE.parent),
        str(ROOT / "tests/collection_app.cpp"),
        str(ROOT / "firmware/t-display/src/App.cpp"),
        str(ROOT / "firmware/t-display/src/CollectionPanel.cpp"),
        str(ROOT / "firmware/t-display/src/LearningRuntime.cpp"),
        *[str(CORE / (name + ".cpp")) for name in (
            "CollectionStore", "PetState", "Nutrition", "SettingsStore", "PracticeBattle",
            "Motion", "Navigation", "Evolution", "DateTimeMenu")],
        "-o", str(binary),
    ], check=True)
    subprocess.run([str(binary)], check=True)
