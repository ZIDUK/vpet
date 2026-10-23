import io
import subprocess
from pathlib import Path

from PIL import Image
import pytest

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "firmware/t-display/lib/vpet_core/src"


@pytest.fixture(scope="module")
def exploration_pixels(tmp_path_factory):
    binary = tmp_path_factory.mktemp("explore-pixels") / "render"
    subprocess.run(["c++", "-std=c++17", "-O2", "-I" + str(CORE),
                    "-I" + str(ROOT / "firmware/t-display/include"),
                    str(ROOT / "tests/exploration_pixels.cpp"),
                    str(CORE / "vpet/PetState.cpp"), str(CORE / "vpet/Nutrition.cpp"),
                    "-o", str(binary)], check=True)
    return binary


@pytest.mark.parametrize("language", ["ES", "EN"])
@pytest.mark.parametrize("species", [0, 1, 2])
@pytest.mark.parametrize("route", [0, 1, 2])
@pytest.mark.parametrize("page,count", [(0, 4), (1, 7), (2, 2), (3, 2), (4, 2), (5, 1), (6, 2)])
def test_board_exploration_render_bounds_and_assets(exploration_pixels, language, species, route, page, count):
    for cursor in range(count):
        raw = subprocess.check_output([str(exploration_pixels), str(ROOT / "firmware/t-display/data"),
                                       str(page), language, str(route), str(species), str(cursor), "14400", "2"])
        image = Image.open(io.BytesIO(raw)).convert("RGB")
        assert image.size == (240, 135)
        assert len(image.crop((0, 24, 240, 135)).getcolors(240 * 135)) > 5


def test_preparation_has_outlined_cells_and_buttons(exploration_pixels):
    raw = subprocess.check_output([str(exploration_pixels), str(ROOT / "firmware/t-display/data"),
                                   "2", "ES", "1", "0", "0", "0", "0"])
    image = Image.open(io.BytesIO(raw)).convert("RGB")
    assert image.getpixel((70, 60)) == image.getpixel((160, 60))
    assert image.getpixel((70, 60)) != image.getpixel((71, 61))
    assert image.getpixel((4, 116)) != image.getpixel((5, 117))


@pytest.mark.parametrize("species", [0, 1, 2])
@pytest.mark.parametrize("language", ["ES", "EN"])
@pytest.mark.parametrize("elapsed", [0, 14400, 28799])
@pytest.mark.parametrize("view", ["home", "panel"])
def test_travel_sprite_is_larger_and_stays_inside_its_lane(exploration_pixels, species, language, elapsed, view):
    raw = subprocess.check_output([str(exploration_pixels), str(ROOT / "firmware/t-display/data"),
                                   "3", language, "1", str(species), "0", str(elapsed), "0", view])
    image = Image.open(io.BytesIO(raw)).convert("RGB")
    lane = image.crop((0, 60, 240, 104))
    mask = Image.new("1", lane.size)
    mask.putdata([r > 100 and r > g * 1.2 and r > b * 1.5 for r, g, b in lane.getdata()])
    bounds = mask.getbbox()
    assert bounds is not None and bounds[3] - bounds[1] >= 30
    assert bounds[0] >= 4 and bounds[2] <= 236
