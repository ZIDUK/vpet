import io
import subprocess
from pathlib import Path

import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "firmware/t-display/lib/vpet_core/src/vpet"


@pytest.fixture(scope="module")
def visual_board(tmp_path_factory):
    binary = tmp_path_factory.mktemp("collection-pixels") / "render"
    subprocess.run(["c++", "-std=c++17", "-O2", "-I" + str(ROOT / "tests/asset_stubs"),
                    "-I" + str(ROOT / "firmware/t-display/include"), "-I" + str(CORE.parent),
                    str(ROOT / "tests/collection_visual.cpp"),
                    *[str(ROOT / "firmware/t-display/src" / (name + ".cpp")) for name in
                      ("CollectionPanel", "CollectionView", "AssetStore", "LearningRuntime")],
                    *[str(CORE / (name + ".cpp")) for name in
                      ("CollectionStore", "PetState", "Nutrition", "SettingsStore", "PracticeBattle")],
                    "-o", str(binary)], check=True)
    return binary


@pytest.mark.parametrize("language", ["ES", "EN"])
@pytest.mark.parametrize("page", ["welcome", "enable", "list", "detail", "preferences", "activate", "founder", "first", "second", "breed"])
def test_board_collection_uses_real_sprites_with_bounded_read_only_labels(visual_board, language, page):
    raw = subprocess.check_output([str(visual_board), str(ROOT / "firmware/t-display/data"), page, language])
    image = Image.open(io.BytesIO(raw)).convert("RGB")
    assert image.size == (240, 135)
    boxes = ((8, 25, 92, 100), (150, 25, 234, 100)) if page in ("second", "breed") else ((4, 22, 236, 106),)
    for box in boxes:
        warm = sum(r > 120 and r > g * 1.15 and r > b * 1.4 for r, g, b in image.crop(box).getdata())
        assert warm > (100 if page != "first" else 30)
