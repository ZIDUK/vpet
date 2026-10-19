from pathlib import Path
from PIL import Image
from scripts.mood_assets import build_mood_assets

ROOT=Path(__file__).resolve().parents[1]


def test_mood_assets_are_small_transparent_and_deterministic(tmp_path):
    files=build_mood_assets(ROOT,tmp_path)
    assert len(files)==11
    before={p.name:p.read_bytes() for p in files}
    for path in files:
        with Image.open(path) as image:
            assert image.mode=='P' and image.getpixel((0,0))==0
            assert image.size==((20,20) if path.stem.startswith('face_') else (32,28))
            assert len(set(image.getdata()))>3
    assert before=={p.name:p.read_bytes() for p in build_mood_assets(ROOT,tmp_path)}
