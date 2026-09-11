"""Pixel-level checks for the shared desktop/device composition."""
from pathlib import Path

from PIL import Image

from core.options import OPTION_BLUETOOTH, OPTION_DATE, OptionsSession
from core.pet import Pet, STATE_LIVE
from display_profiles import get_display_profile
from scripts import build as build_script
from scripts.sim_renderer import render_frame


ROOT = Path(__file__).parent.parent


def _rookie():
    return Pet(species="rookie", state=STATE_LIVE)


class FakeOptionsServices:
    def get_datetime(self):
        return 2026, 9, 5, 10, 15


def test_renderer_outputs_device_sized_frame_with_shared_background():
    frame = render_frame(ROOT / "build", _rookie())
    background = Image.open(ROOT / "build" / "Background" / "background.bmp").convert("RGB")

    assert frame.size == (128, 128)
    assert frame.mode == "RGB"
    assert frame.getpixel((0, 127)) == background.getpixel((0, 127))


def test_renderer_outputs_tdisplay_frame_with_30_pixel_menu_cells(tmp_path):
    build_dir = tmp_path / "build-tdisplay"
    profile = get_display_profile("tdisplay")
    build_script.main(profile_name="tdisplay", output_dir=build_dir)

    frame = render_frame(
        build_dir,
        _rookie(),
        menu_index=7,
        profile=profile,
    )

    assert frame.size == (240, 135)
    assert frame.getpixel((210, 0)) == (255, 215, 0)
    assert frame.getpixel((239, 23)) == (255, 215, 0)
    assert frame.getpixel((209, 0)) == (0, 0, 0)


def test_tdisplay_panels_stay_inside_content_area(tmp_path):
    build_dir = tmp_path / "build-tdisplay"
    profile = get_display_profile("tdisplay")
    build_script.main(profile_name="tdisplay", output_dir=build_dir)
    session = OptionsSession()

    for menu_index, panel_mode in ((0, "status"), (5, "inventory"), (6, "evolution"), (7, "options")):
        frame = render_frame(
            build_dir,
            _rookie(),
            menu_index=menu_index,
            panel_mode=panel_mode,
            options_session=session,
            profile=profile,
        )
        assert frame.size == (240, 135)
        assert frame.getpixel((239, 134)) == (214, 180, 112)


def test_renderer_draws_eight_icon_menu_across_top_row():
    frame = render_frame(ROOT / "build", _rookie())
    background = Image.open(ROOT / "build" / "Background" / "background.bmp").convert("RGB")

    for cell in range(8):
        x = cell * 16 + 8
        assert frame.getpixel((x, 8)) != background.getpixel((x, 8))
    assert frame.getpixel((0, 16)) == background.getpixel((0, 16))


def test_renderer_draws_selector_around_requested_menu_item():
    first = render_frame(ROOT / "build", _rookie(), menu_index=0)
    sixth = render_frame(ROOT / "build", _rookie(), menu_index=5)

    assert first.getpixel((0, 0)) == (255, 215, 0)
    assert first.getpixel((80, 0)) == (0, 0, 0)
    assert sixth.getpixel((0, 0)) == (0, 0, 0)
    assert sixth.getpixel((80, 0)) == (255, 215, 0)


def test_renderer_animates_transparent_firemon_idle_over_background():
    background = Image.open(ROOT / "build" / "Background" / "background.bmp").convert("RGB")
    open_eyes = render_frame(ROOT / "build", _rookie(), sprite_frame=0)
    closed_eyes = render_frame(ROOT / "build", _rookie(), sprite_frame=12)

    assert open_eyes.getpixel((32, 46)) == background.getpixel((32, 46))
    assert open_eyes.crop((32, 46, 96, 110)).tobytes() != closed_eyes.crop(
        (32, 46, 96, 110)
    ).tobytes()


def test_renderer_places_and_flips_walking_firemon():
    right = render_frame(
        ROOT / "build",
        _rookie(),
        sprite_frame=3,
        motion_state="walk",
        pet_x=4,
        facing=1,
    )
    left = render_frame(
        ROOT / "build",
        _rookie(),
        sprite_frame=3,
        motion_state="walk",
        pet_x=4,
        facing=-1,
    )

    assert right.crop((4, 46, 68, 110)).tobytes() != left.crop((4, 46, 68, 110)).tobytes()


def test_renderer_uses_eat_animation_with_transparent_background():
    background = Image.open(ROOT / "build" / "Background" / "background.bmp").convert("RGB")
    eating = render_frame(ROOT / "build", _rookie(), sprite_frame=8, motion_state="eat")

    assert eating.getpixel((32, 46)) == background.getpixel((32, 46))
    assert eating.crop((32, 46, 96, 110)).tobytes() != render_frame(
        ROOT / "build", _rookie(), sprite_frame=8, motion_state="idle"
    ).crop((32, 46, 96, 110)).tobytes()


def test_renderer_uses_punch_animation_for_training():
    background = Image.open(ROOT / "build" / "Background" / "background.bmp").convert("RGB")
    punching = render_frame(ROOT / "build", _rookie(), sprite_frame=12, motion_state="punch")

    assert punching.getpixel((32, 46)) == background.getpixel((32, 46))
    assert punching.crop((32, 46, 96, 110)).tobytes() != render_frame(
        ROOT / "build", _rookie(), sprite_frame=12, motion_state="idle"
    ).crop((32, 46, 96, 110)).tobytes()


def test_renderer_uses_sleep_animation_for_rest():
    background = Image.open(
        ROOT / "build" / "Background" / "background_night.bmp"
    ).convert("RGB")
    sleeping = render_frame(ROOT / "build", _rookie(), sprite_frame=14, motion_state="sleep")

    assert sleeping.getpixel((32, 46)) == background.getpixel((32, 46))
    assert sleeping.crop((32, 46, 96, 110)).tobytes() != render_frame(
        ROOT / "build", _rookie(), sprite_frame=14, motion_state="idle"
    ).crop((32, 46, 96, 110)).tobytes()


def test_sleep_state_switches_to_darker_night_background():
    day = render_frame(ROOT / "build", _rookie(), sprite_frame=14, motion_state="idle")
    night = render_frame(ROOT / "build", _rookie(), sprite_frame=14, motion_state="sleep")

    day_pixel = day.getpixel((10, 25))
    night_pixel = night.getpixel((10, 25))
    assert sum(night_pixel) < sum(day_pixel)


def test_renderer_uses_cast_animation_for_battle():
    background = Image.open(ROOT / "build" / "Background" / "background.bmp").convert("RGB")
    casting = render_frame(ROOT / "build", _rookie(), sprite_frame=8, motion_state="cast")

    assert casting.getpixel((32, 46)) == background.getpixel((32, 46))
    assert casting.crop((32, 46, 96, 110)).tobytes() != render_frame(
        ROOT / "build", _rookie(), sprite_frame=8, motion_state="idle"
    ).crop((32, 46, 96, 110)).tobytes()


def test_renderer_uses_full_scene_evolution_animation():
    background = Image.open(ROOT / "build" / "Background" / "background.bmp").convert("RGB")
    evolving = render_frame(ROOT / "build", _rookie(), sprite_frame=7, motion_state="evolution")

    assert evolving.getpixel((0, 0)) == (255, 215, 0)
    assert evolving.crop((8, 16, 120, 128)).tobytes() != background.crop(
        (8, 16, 120, 128)
    ).tobytes()


def test_renderer_switches_to_flamemon_idle_and_walk_after_evolution():
    rookie = _rookie()
    flamemon = Pet(species="champion", state=STATE_LIVE)

    rookie_idle = render_frame(ROOT / "build", rookie, sprite_frame=4, motion_state="idle")
    flamemon_idle = render_frame(ROOT / "build", flamemon, sprite_frame=4, motion_state="idle")
    flamemon_walk = render_frame(ROOT / "build", flamemon, sprite_frame=4, motion_state="walk")

    area = (32, 46, 96, 110)
    assert flamemon_idle.crop(area).tobytes() != rookie_idle.crop(area).tobytes()
    assert flamemon_walk.crop(area).tobytes() != flamemon_idle.crop(area).tobytes()


def test_renderer_uses_flamemon_action_sprites_after_evolution():
    rookie = _rookie()
    flamemon = Pet(species="champion", state=STATE_LIVE)

    for state, frame_index in (
        ("eat", 10),
        ("punch", 10),
        ("sleep", 10),
        ("cast", 8),
    ):
        rookie_action = render_frame(
            ROOT / "build", rookie, sprite_frame=frame_index, motion_state=state
        )
        flamemon_action = render_frame(
            ROOT / "build", flamemon, sprite_frame=frame_index, motion_state=state
        )
        assert flamemon_action.crop((32, 46, 96, 110)).tobytes() != rookie_action.crop(
            (32, 46, 96, 110)
        ).tobytes()


def test_renderer_uses_dragfiremon_fly_for_movement_and_action_sprites():
    dragfiremon = Pet(species="ultimate", state=STATE_LIVE)
    idle = render_frame(ROOT / "build", dragfiremon, sprite_frame=8, motion_state="idle")
    flying = render_frame(ROOT / "build", dragfiremon, sprite_frame=8, motion_state="walk")

    area = (32, 46, 96, 110)
    assert flying.crop(area).tobytes() != idle.crop(area).tobytes()
    for state in ("eat", "punch", "sleep", "cast"):
        action = render_frame(
            ROOT / "build", dragfiremon, sprite_frame=8, motion_state=state
        )
        assert action.crop(area).tobytes() != idle.crop(area).tobytes()


def test_flamemon_to_dragfiremon_uses_flamemon_evolution_sprite():
    flamemon = Pet(species="champion", state=STATE_LIVE)
    dragfiremon = Pet(species="ultimate", state=STATE_LIVE)

    first_evolution = render_frame(
        ROOT / "build", flamemon, sprite_frame=8, motion_state="evolution"
    )
    second_evolution = render_frame(
        ROOT / "build", dragfiremon, sprite_frame=8, motion_state="evolution"
    )

    assert first_evolution.crop((8, 16, 120, 128)).tobytes() != second_evolution.crop(
        (8, 16, 120, 128)
    ).tobytes()


def test_sparkmon_to_firemon_uses_sparkmon_evolution_sprite():
    firemon = Pet(species="rookie", state=STATE_LIVE)
    flamemon = Pet(species="champion", state=STATE_LIVE)

    sparkmon_evolution = render_frame(
        ROOT / "build", firemon, sprite_frame=10, motion_state="evolution"
    )
    firemon_evolution = render_frame(
        ROOT / "build", flamemon, sprite_frame=10, motion_state="evolution"
    )

    area = (8, 16, 120, 128)
    assert sparkmon_evolution.crop(area).tobytes() != firemon_evolution.crop(area).tobytes()


def test_renderer_uses_egg_and_sparkmon_assets():
    from core.pet import STATE_EGG

    egg = render_frame(ROOT / "build", Pet(species="egg", state=STATE_EGG), sprite_frame=8)
    sparkmon = render_frame(
        ROOT / "build", Pet(species="baby", state=STATE_LIVE), sprite_frame=8, motion_state="walk"
    )

    assert egg.crop((32, 46, 96, 110)).getbbox() is not None
    assert sparkmon.crop((32, 46, 96, 110)).getbbox() is not None
    assert egg.tobytes() != sparkmon.tobytes()


def test_first_menu_item_opens_dynamic_status_panel():
    pet = _rookie()
    pet.stats.update({"hp": 83, "h": 61, "e": 74, "p": 92})
    world = render_frame(ROOT / "build", pet, menu_index=0)
    status = render_frame(ROOT / "build", pet, menu_index=0, status_visible=True)

    assert status.getpixel((0, 0)) == (255, 215, 0)
    assert status.crop((0, 16, 128, 128)).tobytes() != world.crop(
        (0, 16, 128, 128)
    ).tobytes()
    assert status.getpixel((27, 49)) == (203, 75, 67)


def test_backpack_panel_draws_items_and_selected_row():
    pet = _rookie()
    inventory = render_frame(
        ROOT / "build",
        pet,
        menu_index=5,
        panel_mode="inventory",
        panel_index=1,
    )

    assert inventory.getpixel((80, 0)) == (255, 215, 0)
    assert inventory.getpixel((8, 60)) == (255, 210, 74)
    assert inventory.getpixel((8, 40)) != (255, 210, 74)


def test_book_panel_highlights_current_evolution_form():
    firemon = render_frame(
        ROOT / "build",
        _rookie(),
        menu_index=6,
        panel_mode="evolution",
    )
    flamemon = render_frame(
        ROOT / "build",
        Pet(species="champion", state=STATE_LIVE),
        menu_index=6,
        panel_mode="evolution",
    )
    dragfiremon = render_frame(
        ROOT / "build",
        Pet(species="ultimate", state=STATE_LIVE),
        menu_index=6,
        panel_mode="evolution",
    )

    assert firemon.getpixel((96, 0)) == (255, 215, 0)
    assert firemon.getpixel((2, 47)) == (255, 210, 74)
    assert firemon.getpixel((45, 47)) != (255, 210, 74)
    assert flamemon.getpixel((2, 47)) != (255, 210, 74)
    assert flamemon.getpixel((45, 47)) == (255, 210, 74)
    assert dragfiremon.getpixel((88, 47)) == (255, 210, 74)

    firemon_card = firemon.crop((5, 49, 37, 81))
    flamemon_card = firemon.crop((48, 49, 80, 81))
    dragfiremon_card = firemon.crop((91, 49, 123, 81))
    assert any(r > 120 and g < 150 for r, g, _ in firemon_card.getdata())
    assert any(r > 120 and g < 150 for r, g, _ in flamemon_card.getdata())
    assert any(r > 120 and g < 150 for r, g, _ in dragfiremon_card.getdata())


def test_gear_panel_draws_options_and_selected_row():
    session = OptionsSession()
    session.index = OPTION_BLUETOOTH
    options = render_frame(
        ROOT / "build",
        _rookie(),
        menu_index=7,
        panel_mode="options",
        options_session=session,
        current_datetime=(2026, 9, 5, 10, 15),
    )

    assert options.getpixel((112, 0)) == (255, 215, 0)
    assert options.getpixel((6, 36)) == (255, 210, 74)


def test_options_renderer_draws_bluetooth_and_date_panels():
    pet = _rookie()
    session = OptionsSession()
    session.index = OPTION_BLUETOOTH
    session.action(pet, FakeOptionsServices())
    bluetooth = render_frame(
        ROOT / "build",
        pet,
        menu_index=7,
        panel_mode="options",
        options_session=session,
        current_datetime=(2026, 9, 5, 10, 15),
    )

    session = OptionsSession()
    session.index = OPTION_DATE
    session.action(pet, FakeOptionsServices())
    date = render_frame(
        ROOT / "build",
        pet,
        menu_index=7,
        panel_mode="options",
        options_session=session,
        current_datetime=(2026, 9, 5, 10, 15),
    )

    assert bluetooth.crop((0, 16, 128, 128)).tobytes() != date.crop((0, 16, 128, 128)).tobytes()


def test_renderer_has_no_legacy_stat_bars_or_action_buttons():
    frame = render_frame(ROOT / "build", _rookie())
    background = Image.open(ROOT / "build" / "Background" / "background.bmp").convert("RGB")

    assert frame.getpixel((10, 78)) == background.getpixel((10, 78))
    assert frame.getpixel((110, 100)) == background.getpixel((110, 100))
