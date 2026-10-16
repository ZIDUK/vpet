import pytest
from scripts.explore_icon import render_explore_icon
from scripts.menu_icons import render_menu_icon


@pytest.mark.parametrize("size", [16, 20, 32])
def test_navigation_icons_share_neutral_frame_without_selection(size):
    explore = render_explore_icon(size)
    back = render_menu_icon("Back", size)
    assert explore.size == back.size == (size, size)
    assert explore.mode == back.mode == "RGBA"
    for x in range(size):
        for y in (0, size - 1):
            assert max(abs(a - b) for a, b in zip(explore.getpixel((x, y)),
                                                back.getpixel((x, y)))) <= 3
    assert max(explore.getpixel((0, 0))[:3]) < 50
    assert explore.tobytes() != back.tobytes()
    assert len(explore.getcolors()) > 10 and len(back.getcolors()) > 10
