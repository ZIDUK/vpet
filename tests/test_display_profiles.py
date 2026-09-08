import pytest

from display_profiles import get_display_profile


def test_tdisplay_profile_is_default_landscape_geometry():
    profile = get_display_profile()

    assert profile.name == "tdisplay"
    assert (profile.width, profile.height) == (240, 135)
    assert (profile.menu_height, profile.cell_width) == (24, 30)
    assert profile.content_rect == (0, 24, 240, 111)
    assert profile.pet_size == 88
    assert profile.portrait_size == 36


def test_pico_profile_remains_available():
    profile = get_display_profile("pico")

    assert (profile.width, profile.height) == (128, 128)
    assert profile.content_rect == (0, 16, 128, 112)


def test_unknown_profile_is_rejected():
    with pytest.raises(ValueError, match="Unknown display profile: missing"):
        get_display_profile("missing")

