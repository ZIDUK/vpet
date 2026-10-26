from types import SimpleNamespace

import pytest

from scripts.deploy_tdisplay import deploy
from scripts.tdisplay_device import BoardInfo, BuildReport, ReadyTelemetry


def test_full_filesystem_deploy_is_blocked_before_any_device_access():
    calls = []
    with pytest.raises(RuntimeError, match="COLLECTION_FILESYSTEM_PROTECTED"):
        deploy(runner=lambda *args, **kwargs: calls.append(args))
    assert not calls


def test_explicit_firmware_only_upload_never_replaces_user_collection(tmp_path):
    calls = []
    def runner(command, **kwargs):
        calls.append(command)
        if "read_flash" in command:
            from pathlib import Path
            with Path(command[-1]).open("wb") as stream:
                stream.truncate(int(str(command[-2]), 16))
        return SimpleNamespace(returncode=0, stdout="", stderr="")
    deploy(board=BoardInfo("test", "ESP32", "aabbcc", 16 << 20), output=tmp_path,
           runner=runner, firmware_only=True,
           build_report=BuildReport(100, 1000, 100, 1000, 100, 1000),
           telemetry_reader=lambda *_: ReadyTelemetry(100000, 80000, 16 << 20, 100, 1000, "1"))
    assert any("upload" in command for command in calls)
    assert not any("uploadfs" in command for command in calls)
