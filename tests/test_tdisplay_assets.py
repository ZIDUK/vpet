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


def test_trim_tired_padding_preserves_every_pixel_and_frame():
    frames = _rgba_test_frames()
    source = [frames[0], frames[1], frames[0], frames[1], frames[0]]
    ordinary = encode_vpa(source,24,24)
    compact = encode_vpa(source,24,24,trim_transparent=True)
    assert len(ordinary)>len(compact)
    decoded = decode_vpa(compact)
    assert decoded.frame_count == 5
    original = decode_vpa(ordinary)
    for frame, expected in zip(decoded.frames,original.frames):
        anchored = Image.new('RGBA',(24,24))
        anchored.paste(frame,((24-frame.width)//2,24-frame.height))
        assert anchored.tobytes() == expected.tobytes()


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
    assert set(manifest["species"]) == {"egg", "baby", "rookie", "champion", "ultimate"}
    assert all(item["sha256"] and item["bytes"] > 0 for item in manifest["assets"])
    assert len(manifest["animations"]) == 51
    for stage, name in (("baby", "sparkmon"), ("rookie", "firemon"),
                        ("champion", "flamemon"), ("ultimate", "dragfiremon")):
        tired = decode_vpa((data_dir / "animations" / stage / (name + "_tired.vpa")).read_bytes())
        assert tired.width <= 88 and tired.height <= 88 and tired.frame_count == 25
        assert all(frame.getbbox() for frame in tired.frames)
        angry = decode_vpa((data_dir / "animations" / stage / (name + "_angry.vpa")).read_bytes())
        assert angry.width <= 88 and angry.height <= 88 and angry.frame_count == 25
        assert all(frame.getbbox() for frame in angry.frames)
    for item in manifest['animations']:
        if item['action'] not in ('angry','tired','eat','walk','fly','sleep',
                                  'punch','cast','hurt','block','dodge','hit','hit_react'):
            continue
        source = sim_build/'digimon1'/item['species'].title()/(Path(item['path']).stem+'_atlas.bmp')
        frames = build_tdisplay._atlas_frames(source)
        original = decode_vpa(encode_vpa(frames, *frames[0].size))
        compact = decode_vpa((data_dir/item['path']).read_bytes())
        for expected, frame in zip(original.frames, compact.frames):
            anchored = Image.new('RGBA', expected.size)
            anchored.paste(frame, ((expected.width-frame.width)//2, expected.height-frame.height))
            assert anchored.tobytes() == expected.tobytes()
    assert {item["action"] for item in manifest["animations"] if item["species"] == "ultimate"} >= {
        "block", "hurt", "happy", "sad",
    }
    assert {item["action"] for item in manifest["animations"] if item["species"] == "champion"} >= {
        "block", "hurt", "hit_react", "dodge", "happy", "sad",
    }
    assert {item["action"] for item in manifest["animations"] if item["species"] == "rookie"} >= {
        "hit",
        "hurt",
        "dodge",
        "block",
        "happy",
        "sad",
    }
    bag = decode_vpa((data_dir / "ui" / "fx" / "bag.vpa").read_bytes())
    grave = decode_vpa((data_dir / "ui" / "fx" / "grave.vpa").read_bytes())
    assert bag.frame_count == 16
    assert grave.frame_count == 1
    assert (data_dir / "manifest.json").is_file()
    catalog = (include_dir / "catalog.h").read_text()
    assert "rookie" in catalog
    assert "sparkmon_idle.vpa" in catalog
    assert "sparkmon_evolution.vpa" in catalog
    assert "firemon_hit.vpa" in catalog
    assert "firemon_happy.vpa" in catalog
    assert "firemon_sad.vpa" in catalog
    assert "egg_hatch.vpa" in catalog
    assert '{"egg", "baby", false, false, 8, -1, 0, 0, 0, 0, 0}' in catalog
    assert "43800" in catalog
    assert "129600" in catalog
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
