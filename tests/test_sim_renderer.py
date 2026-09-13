"""Pixel-level checks for the shared desktop/device composition."""
from pathlib import Path

from PIL import Image

from core.options import OPTION_BLUETOOTH, OPTION_DATE, OPTION_LANGUAGE, OptionsSession
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


def test_tdisplay_inventory_keeps_back_on_screen(tmp_path):
    from core.inventory import INVENTORY_BACK_INDEX
    from core.status_card import STATUS_SPLIT_X

    build_dir = tmp_path / "build-tdisplay"
    profile = get_display_profile("tdisplay")
    build_script.main(profile_name="tdisplay", output_dir=build_dir)
    frame = render_frame(
        build_dir,
        _rookie(),
        menu_index=5,
        panel_mode="inventory",
        panel_index=INVENTORY_BACK_INDEX,
        profile=profile,
    )
    yellow = (255, 210, 74)
    yellow_rows = [
        y
        for y in range(48, 135)
        if any(frame.getpixel((x, y)) == yellow for x in range(STATUS_SPLIT_X, 232))
    ]
    assert yellow_rows
    assert min(yellow_rows) >= 48
    assert max(yellow_rows) <= 133
    assert max(yellow_rows) - min(yellow_rows) >= 18
    assert frame.getpixel((20, 80)) != yellow


def test_tdisplay_inventory_splits_preview_and_list(tmp_path):
    from core.status_card import STATUS_CARD_Y, STATUS_SPLIT_X

    build_dir = tmp_path / "build-tdisplay"
    profile = get_display_profile("tdisplay")
    build_script.main(profile_name="tdisplay", output_dir=build_dir)
    meat = render_frame(
        build_dir,
        _rookie(),
        menu_index=5,
        panel_mode="inventory",
        panel_index=0,
        profile=profile,
    )
    energy = render_frame(
        build_dir,
        _rookie(),
        menu_index=5,
        panel_mode="inventory",
        panel_index=1,
        profile=profile,
    )
    parchment = (214, 180, 112)
    left = (0, 48, STATUS_SPLIT_X, 135)
    right = (STATUS_SPLIT_X, 48, 240, 135)
    assert meat.crop(left).tobytes() != energy.crop(left).tobytes()
    assert meat.getpixel((STATUS_SPLIT_X + 10, STATUS_CARD_Y + 4)) != parchment
    assert meat.getpixel((8, STATUS_CARD_Y + 4)) == parchment


def test_tdisplay_evolution_tree_branches_after_spark(tmp_path):
    from core.evolution import EVO_CHIP, EVO_COLOR_Y, EVO_DARK_Y, EVO_GAP, EVO_X0

    build_dir = tmp_path / "build-tdisplay"
    profile = get_display_profile("tdisplay")
    build_script.main(profile_name="tdisplay", output_dir=build_dir)
    frame = render_frame(
        build_dir,
        _rookie(),
        menu_index=6,
        panel_mode="evolution",
        panel_index=0,
        profile=profile,
    )
    parchment = (214, 180, 112)
    stride = EVO_CHIP + EVO_GAP
    trunk = frame.getpixel((EVO_X0 + 8, EVO_COLOR_Y + 8))
    leftover_egg = frame.getpixel((EVO_X0 + 8, EVO_DARK_Y + 8))
    dark_fork = frame.getpixel((EVO_X0 + 2 * stride + 8, EVO_DARK_Y + 8))
    assert trunk != parchment
    assert leftover_egg == parchment
    assert dark_fork != parchment


def test_tdisplay_evolution_detail_splits_card_and_list(tmp_path):
    from core.status_card import STATUS_CARD_Y, STATUS_SPLIT_X

    build_dir = tmp_path / "build-tdisplay"
    profile = get_display_profile("tdisplay")
    build_script.main(profile_name="tdisplay", output_dir=build_dir)
    egg = render_frame(
        build_dir,
        _rookie(),
        menu_index=6,
        panel_mode="evolution_detail",
        panel_index=0,
        profile=profile,
    )
    spark = render_frame(
        build_dir,
        _rookie(),
        menu_index=6,
        panel_mode="evolution_detail",
        panel_index=1,
        profile=profile,
    )
    parchment = (214, 180, 112)
    left = (0, 48, STATUS_SPLIT_X, 135)
    assert egg.crop(left).tobytes() != spark.crop(left).tobytes()
    assert egg.getpixel((STATUS_SPLIT_X + 10, STATUS_CARD_Y + 4)) != parchment
    assert egg.getpixel((8, STATUS_CARD_Y + 4)) == parchment


def test_tdisplay_options_uses_dedicated_setting_icons(tmp_path):
    from core.options import OPTION_ICONS

    build_dir = tmp_path / "build-tdisplay"
    profile = get_display_profile("tdisplay")
    build_script.main(profile_name="tdisplay", output_dir=build_dir)
    session = OptionsSession()
    frame = render_frame(
        build_dir,
        _rookie(),
        menu_index=7,
        panel_mode="options",
        options_session=session,
        profile=profile,
    )
    bluetooth = Image.open(build_dir / "UIIcons" / "Bluetooth.bmp").resize((20, 20), Image.Resampling.NEAREST).convert("RGB")
    energy = Image.open(build_dir / "UIIcons" / "Energy.bmp").resize((20, 20), Image.Resampling.NEAREST).convert("RGB")
    chip = frame.crop((10, 56, 30, 76)).convert("RGB")
    assert chip.tobytes() != energy.tobytes()
    lit = [
        (pixel, blue)
        for pixel, blue in zip(chip.getdata(), bluetooth.getdata())
        if sum(blue) > 80
    ]
    assert lit
    assert sum(1 for pixel, blue in lit if pixel == blue) > len(lit) // 2
    assert OPTION_ICONS[0] == "Bluetooth"


def test_tdisplay_options_chips_include_icons(tmp_path):
    build_dir = tmp_path / "build-tdisplay"
    profile = get_display_profile("tdisplay")
    build_script.main(profile_name="tdisplay", output_dir=build_dir)
    session = OptionsSession()
    frame = render_frame(
        build_dir,
        _rookie(),
        menu_index=7,
        panel_mode="options",
        options_session=session,
        profile=profile,
    )
    colors = {
        frame.getpixel((x, y))
        for y in range(84, 100)
        for x in range(10, 26)
    }
    assert len(colors) >= 6


def test_tdisplay_status_keeps_pet_left_and_pages_the_card(tmp_path):
    from core.dna import helix_color565, rgb565_to_rgb
    from core.status_card import STATUS_CARD_H, STATUS_CARD_Y, STATUS_SPLIT_X

    build_dir = tmp_path / "build-tdisplay"
    profile = get_display_profile("tdisplay")
    build_script.main(profile_name="tdisplay", output_dir=build_dir)
    pet = _rookie()
    pet.restore_dna((0x12, 0x34, 0x56, 0x78))
    pet.restore_ev({"hp": 12})
    page0 = render_frame(
        build_dir,
        pet,
        menu_index=0,
        panel_mode="status",
        panel_index=0,
        profile=profile,
        pet_x=140,
    )
    page1 = render_frame(
        build_dir,
        pet,
        menu_index=0,
        panel_mode="status",
        panel_index=1,
        current_datetime=(2026, 9, 5, 10, 15),
        profile=profile,
        pet_x=140,
    )
    page3 = render_frame(
        build_dir,
        pet,
        menu_index=0,
        panel_mode="status",
        panel_index=3,
        profile=profile,
        pet_x=140,
    )
    left = (0, 48, STATUS_SPLIT_X, 135)
    right = (STATUS_SPLIT_X, 24, 240, 135)
    parchment = (214, 180, 112)
    ink = (48, 42, 55)
    assert page0.getpixel((10, 35)) == ink
    assert page0.getpixel((2, 50)) == parchment
    page2 = render_frame(
        build_dir,
        pet,
        menu_index=0,
        panel_mode="status",
        panel_index=2,
        profile=profile,
        pet_x=140,
    )
    for page, icon_x, icon_y in (
        (page0, STATUS_SPLIT_X + 6, 57),
        (page0, STATUS_SPLIT_X + 6, 84),
        (page0, STATUS_SPLIT_X + 6, 111),
        (page2, STATUS_SPLIT_X + 74, 56),
    ):
        pixel = page.getpixel((icon_x, icon_y))
        assert pixel != ink
        assert sum(pixel) > 220
    assert page0.getpixel((STATUS_SPLIT_X + 20, 48)) == parchment
    assert page2.getpixel((STATUS_SPLIT_X + 20, 48)) == parchment
    gap_y = STATUS_CARD_Y + STATUS_CARD_H + 1
    assert page0.getpixel((STATUS_SPLIT_X + 20, gap_y)) == parchment
    assert page0.crop(left).tobytes() == page1.crop(left).tobytes()
    assert page0.crop(right).tobytes() != page1.crop(right).tobytes()
    assert any(pixel != parchment and pixel != ink for pixel in page0.crop((8, 50, 90, 130)).getdata())
    well = set(page3.crop((STATUS_SPLIT_X + 6, 56, STATUS_SPLIT_X + 44, 132)).getdata())
    assert rgb565_to_rgb(helix_color565(pet.dna, 0)) in well
    assert rgb565_to_rgb(helix_color565(pet.dna, 1)) in well
    later = render_frame(
        build_dir,
        pet,
        menu_index=0,
        panel_mode="status",
        panel_index=3,
        profile=profile,
        pet_x=140,
        now_ms=800,
    )
    assert page3.crop((STATUS_SPLIT_X + 6, 56, STATUS_SPLIT_X + 44, 132)).tobytes() != later.crop(
        (STATUS_SPLIT_X + 6, 56, STATUS_SPLIT_X + 44, 132)
    ).tobytes()
    later_well = set(later.crop((STATUS_SPLIT_X + 6, 56, STATUS_SPLIT_X + 44, 132)).getdata())
    assert rgb565_to_rgb(helix_color565(pet.dna, 0)) in later_well
    assert rgb565_to_rgb(helix_color565(pet.dna, 1)) in later_well
    assert page3.getpixel((STATUS_SPLIT_X + 20, 48)) == parchment
    assert page3.getpixel((STATUS_SPLIT_X + 20, 50)) == parchment
    assert page3.getpixel((STATUS_SPLIT_X + 56, 80)) == parchment
    assert page3.getpixel((STATUS_SPLIT_X + 20, 133)) == parchment


def test_tdisplay_dna_id_stays_inside_the_screen(tmp_path):
    from core.status_card import STATUS_CARD_Y, STATUS_SPLIT_X

    build_dir = tmp_path / "build-tdisplay"
    profile = get_display_profile("tdisplay")
    build_script.main(profile_name="tdisplay", output_dir=build_dir)
    pet = _rookie()
    pet.restore_dna((0xBF, 0x1E, 0x1B, 0x93))
    page = render_frame(
        build_dir,
        pet,
        menu_index=0,
        panel_mode="status",
        panel_index=3,
        profile=profile,
        pet_x=140,
    )
    parchment = (214, 180, 112)
    row = STATUS_CARD_Y + 4
    assert page.getpixel((238, row)) == parchment
    tail = [page.getpixel((x, row)) for x in range(200, 228)]
    head = [page.getpixel((x, row)) for x in range(STATUS_SPLIT_X + 44, 180)]
    assert any(sum(pixel) < sum(parchment) - 30 for pixel in tail)
    assert any(sum(pixel) < sum(parchment) - 30 for pixel in head)


def test_status_page_three_differs_from_bars_on_pico():
    pet = _rookie()
    pet.restore_dna((0x12, 0x34, 0x56, 0x78))
    page0 = render_frame(ROOT / "build", pet, menu_index=0, status_visible=True, panel_index=0)
    page3 = render_frame(ROOT / "build", pet, menu_index=0, status_visible=True, panel_index=3)
    assert page0.crop((0, 16, 128, 128)).tobytes() != page3.crop((0, 16, 128, 128)).tobytes()


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


def test_tdisplay_options_next_moves_yellow_chip(tmp_path):
    build_dir = tmp_path / "build-tdisplay"
    profile = get_display_profile("tdisplay")
    build_script.main(profile_name="tdisplay", output_dir=build_dir)
    session = OptionsSession()
    session.index = OPTION_BLUETOOTH
    bluetooth = render_frame(
        build_dir,
        _rookie(),
        menu_index=7,
        panel_mode="options",
        options_session=session,
        profile=profile,
    )
    session.index = OPTION_LANGUAGE
    language = render_frame(
        build_dir,
        _rookie(),
        menu_index=7,
        panel_mode="options",
        options_session=session,
        profile=profile,
    )

    selector = (255, 215, 0)
    assert bluetooth.getpixel((40, 58)) == selector
    assert language.getpixel((40, 58)) != selector
    assert language.getpixel((116, 58)) == selector


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
