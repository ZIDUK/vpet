import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_actual_app_retries_failed_saves_without_accepting_input(tmp_path):
    core = ROOT / "firmware/t-display/lib/vpet_core/src"
    firmware = ROOT / "firmware/t-display"
    binary = tmp_path / "app"
    subprocess.run(["c++", "-std=c++17", "-I" + str(ROOT / "tests/app_stubs"),
                    "-I" + str(firmware / "include"), "-I" + str(core),
                    str(ROOT / "tests/app_persistence.cpp"), str(firmware / "src/App.cpp"),
                    *[str(core / "vpet" / (name + ".cpp")) for name in
                      ("PetState", "Nutrition", "SettingsStore", "PracticeBattle", "Motion", "Navigation", "Evolution", "DateTimeMenu")],
                    "-o", str(binary)], check=True)
    subprocess.run([str(binary)], check=True)


def test_ready_telemetry_is_guarded_and_only_after_initialization():
    source = (ROOT / "firmware/t-display/src/main.cpp").read_text()
    report = source.split("void reportReady()", 1)[1].split("void drawBoot", 1)[0]
    assert "!app.ready()" in report and "readyReported" in report
    setup = source.split("void setup()", 1)[1].split("void loop()", 1)[0]
    assert setup.index("app.begin(") < setup.index("reportReady();")
    loop = source.split("void loop()", 1)[1]
    assert loop.index("app.tick(") < loop.index("reportReady();")
