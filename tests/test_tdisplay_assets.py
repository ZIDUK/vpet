"""Checks for deterministic assets consumed by the native ESP32 firmware."""
import json
from pathlib import Path

from PIL import Image, ImageDraw

from scripts import build as build_script
from scripts import build_tdisplay
from scripts.tdisplay_assets import decode_vpa, encode_vpa


ROOT = Path(__file__).parent.parent


def _rgba_test_frames():
    frames = []
    for offset in (4, 10):
        frame = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
        ImageDraw.Draw(frame).rectangle((offset, 5, offset + 7, 14), fill=(255, 80, 0, 255))
        frames.append(frame)
    return frames


def test_vpa_round_trip_preserves_transparency_and_dimensions():
    source = _rgba_test_frames()

    payload = encode_vpa(source, width=24, height=24)
    decoded = decode_vpa(payload)

    assert decoded.size == (24, 24)
    assert decoded.frame_count == len(source)
    assert decoded.transparent_index == 0
    assert decoded.frames[0].getpixel((0, 0))[3] == 0
    assert decoded.frames[1].getpixel((10, 5))[:3] == (255, 80, 0)
    assert decoded.frames[0].getbbox() == source[0].getbbox()
    assert decoded.frames[1].getbbox() == source[1].getbbox()


def test_native_manifest_covers_every_registered_animation(tmp_path):
    sim_build = tmp_path / "sim"
    data_dir = tmp_path / "data"
    include_dir = tmp_path / "include"
    build_script.main(profile_name="tdisplay", output_dir=sim_build)

    manifest = build_tdisplay.build(
        ROOT,
        sim_build=sim_build,
        data_dir=data_dir,
        include_dir=include_dir,
    )

    assert manifest["display"] == {"width": 240, "height": 135, "menu_height": 24}
    assert set(manifest["species"]) == {"rookie", "champion", "ultimate"}
    assert all(item["sha256"] and item["bytes"] > 0 for item in manifest["assets"])
    assert len(manifest["animations"]) == 20
    assert (data_dir / "manifest.json").is_file()
    catalog = (include_dir / "catalog.h").read_text()
    assert "rookie" in catalog
    assert "dragfiremon_fly.vpa" in catalog


def test_native_asset_build_is_deterministic(tmp_path):
    sim_build = tmp_path / "sim"
    data_dir = tmp_path / "data"
    include_dir = tmp_path / "include"
    build_script.main(profile_name="tdisplay", output_dir=sim_build)

    build_tdisplay.build(ROOT, sim_build, data_dir, include_dir)
    first = {
        path.relative_to(data_dir): path.read_bytes()
        for path in data_dir.rglob("*")
        if path.is_file()
    }
    build_tdisplay.build(ROOT, sim_build, data_dir, include_dir)
    second = {
        path.relative_to(data_dir): path.read_bytes()
        for path in data_dir.rglob("*")
        if path.is_file()
    }

    assert first == second
