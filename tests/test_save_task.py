from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def test_real_task_adapter_is_bounded_and_publishes_completion(tmp_path):
    binary = tmp_path / "save-task"
    subprocess.run([
        "c++", "-std=c++17", "-pthread",
        "-I" + str(ROOT / "tests/task_stubs"),
        "-I" + str(ROOT / "firmware/t-display/include"),
        str(ROOT / "tests/save_task.cpp"), "-o", str(binary),
    ], check=True, timeout=30)
    subprocess.run([str(binary)], check=True, timeout=15)
