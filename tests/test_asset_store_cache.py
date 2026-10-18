import subprocess
from pathlib import Path

from PIL import Image
from scripts.tdisplay_assets import encode_vpa

ROOT = Path(__file__).resolve().parents[1]


def test_real_asset_store_reuses_static_training_icons_without_io(tmp_path):
    data = tmp_path / "training"
    data.mkdir()
    for index in range(11):
        image = Image.new("RGBA", (16, 16))
        for y in range(2, 14):
            for x in range(1, 13):
                image.putpixel((x, y), (index * 20, x * 19, y * 17, 255))
        (data / f"icon{index}.vpa").write_bytes(encode_vpa([image], 16, 16))
    frames = [Image.new("RGBA", (68, 68), color) for color in ("red", "blue")]
    (data / "pet.vpa").write_bytes(encode_vpa(frames, 68, 68))
    portrait = Image.new("RGBA", (88, 88))
    for x, y, color in ((0, 0, "red"), (70, 70, "blue"), (0, 80, "green"), (80, 0, "yellow")):
        portrait.paste(color, (x, y, min(x + 8, 88), min(y + 8, 88)))
    (data / "portrait.vpa").write_bytes(encode_vpa([portrait], 88, 88))
    binary = tmp_path / "asset-cache"
    subprocess.run([
        "c++", "-std=c++17", "-I" + str(ROOT / "tests/asset_stubs"),
        "-I" + str(ROOT / "firmware/t-display/include"),
        str(ROOT / "tests/asset_store_cache.cpp"),
        str(ROOT / "firmware/t-display/src/AssetStore.cpp"), "-o", str(binary),
    ], check=True)
    subprocess.run([str(binary), str(tmp_path)], check=True)
