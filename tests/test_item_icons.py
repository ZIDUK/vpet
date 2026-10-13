from PIL import Image

from display_profiles import get_display_profile
from scripts import build as build_script
from scripts.item_icons import ICON_NAMES, render_item_icon


def test_generated_inventory_icons_are_distinct_pixel_art():
    icons = [render_item_icon(name, 32) for name in ICON_NAMES]

    assert all(image.size == (32, 32) and image.mode == "RGBA" for image in icons)
    assert len({image.tobytes() for image in icons}) == len(ICON_NAMES)
    assert all(len(image.getcolors(1024)) <= 20 for image in icons)
    assert all(image.getpixel((0, 0))[:3] == (52, 82, 84) for image in icons)


def test_custom_icons_are_packaged_for_the_shared_simulator_build(tmp_path, monkeypatch):
    monkeypatch.setattr(build_script, "BUILD", tmp_path)
    monkeypatch.setattr(build_script, "ACTIVE_PROFILE", get_display_profile("tdisplay"))

    build_script.collect_ui()

    for name in ICON_NAMES:
        with Image.open(tmp_path / "UIIcons" / f"{name}.bmp") as icon:
            assert icon.size == (get_display_profile("tdisplay").icon_size,) * 2
