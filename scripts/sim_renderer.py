"""Deterministic renderer shared by simulator tests and pygame."""
from pathlib import Path

from PIL import Image, ImageDraw

from display_profiles import get_display_profile

from config import (
    BACKGROUND_PATH,
    BACKGROUND_NIGHT_PATH,
    DISPLAY_HEIGHT,
    DISPLAY_WIDTH,
    DRAGFIREMON_CAST_IMAGE_PATH,
    DRAGFIREMON_EAT_IMAGE_PATH,
    DRAGFIREMON_EVOLUTION_THUMB_PATH,
    DRAGFIREMON_FLY_FRAME_COUNT,
    DRAGFIREMON_FLY_IMAGE_PATH,
    DRAGFIREMON_IDLE_FRAME_COUNT,
    DRAGFIREMON_IDLE_IMAGE_PATH,
    DRAGFIREMON_PUNCH_IMAGE_PATH,
    DRAGFIREMON_SLEEP_IMAGE_PATH,
    EVOLUTION_DRAGFIREMON_THUMB_X,
    EVOLUTION_FIREMON_THUMB_X,
    EVOLUTION_FLAMEMON_THUMB_X,
    EVOLUTION_THUMB_Y,
    EVOLVED_SPECIES,
    FLAMEMON_CAST_IMAGE_PATH,
    FLAMEMON_EAT_IMAGE_PATH,
    FLAMEMON_EVOLUTION_IMAGE_PATH,
    FLAMEMON_EVOLUTION_THUMB_PATH,
    FLAMEMON_IDLE_FRAME_COUNT,
    FLAMEMON_IDLE_IMAGE_PATH,
    FLAMEMON_PUNCH_IMAGE_PATH,
    FLAMEMON_SLEEP_IMAGE_PATH,
    FLAMEMON_WALK_FRAME_COUNT,
    FLAMEMON_WALK_IMAGE_PATH,
    MENU_BAR_HEIGHT,
    MENU_ICON_PATHS,
    MENU_ICON_X,
    MENU_ICON_Y,
    MENU_SELECTOR_COLOR,
    PET_CAST_FRAME_COUNT,
    PET_CAST_IMAGE_PATH,
    PET_EAT_FRAME_COUNT,
    PET_EAT_IMAGE_PATH,
    PET_EVOLUTION_FRAME_COUNT,
    PET_EVOLUTION_IMAGE_PATH,
    PET_EVOLUTION_SIZE,
    PET_EVOLUTION_X,
    PET_EVOLUTION_Y,
    PET_IDLE_FRAME_COUNT,
    PET_IDLE_IMAGE_PATH,
    PET_PUNCH_FRAME_COUNT,
    PET_PUNCH_IMAGE_PATH,
    PET_SLEEP_FRAME_COUNT,
    PET_SLEEP_IMAGE_PATH,
    PET_SIZE,
    PET_WALK_FRAME_COUNT,
    PET_WALK_IMAGE_PATH,
    PET_X,
    PET_Y,
    FIREMON_EVOLUTION_THUMB_PATH,
    ULTIMATE_SPECIES,
)
from ui.status import (
    STATUS_COLORS,
    STATUS_HEIGHT,
    STATUS_WIDTH,
    draw_evolution_guide,
    draw_datetime_editor,
    draw_inventory,
    draw_options,
    draw_password_editor,
    draw_status,
    draw_wifi,
)


def device_path(build_dir, absolute_path):
    return Path(build_dir) / absolute_path.lstrip("/")


def render_frame(
    build_dir,
    pet,
    menu_index=0,
    sprite_frame=0,
    motion_state="idle",
    pet_x=PET_X,
    facing=1,
    status_visible=False,
    panel_mode=None,
    panel_index=0,
    options_session=None,
    current_datetime=None,
    profile=None,
):
    """Render the composition shared with the CircuitPython display group."""
    profile = profile or get_display_profile("pico")
    build_dir = Path(build_dir)
    background_path = BACKGROUND_NIGHT_PATH if motion_state == "sleep" else BACKGROUND_PATH
    with Image.open(device_path(build_dir, background_path)) as opened:
        frame = opened.convert("RGB")
    if frame.size != (profile.width, profile.height):
        raise ValueError(f"Background must be {profile.width}x{profile.height}")

    ImageDraw.Draw(frame).rectangle(
        (0, 0, profile.width - 1, profile.menu_height - 1),
        fill=(0, 0, 0),
    )
    for index, path in enumerate(MENU_ICON_PATHS):
        with Image.open(device_path(build_dir, path)) as opened:
            icon = opened.convert("RGB")
        icon_x = index * profile.cell_width + (profile.cell_width - profile.icon_size) // 2
        icon_y = (profile.menu_height - profile.icon_size) // 2
        frame.paste(icon, (icon_x, icon_y))

    selector_x = (menu_index % len(MENU_ICON_PATHS)) * profile.cell_width
    selector_color = (
        (MENU_SELECTOR_COLOR >> 16) & 0xFF,
        (MENU_SELECTOR_COLOR >> 8) & 0xFF,
        MENU_SELECTOR_COLOR & 0xFF,
    )
    ImageDraw.Draw(frame).rectangle(
        (selector_x, 0, selector_x + profile.cell_width - 1, profile.menu_height - 1),
        outline=selector_color,
        width=1,
    )

    sprite_size = profile.pet_size
    sprite_x = int(pet_x)
    sprite_y = PET_Y if profile.name == "pico" else profile.height - sprite_size - 4
    if motion_state == "evolution":
        image_path = (
            FLAMEMON_EVOLUTION_IMAGE_PATH
            if pet.species == ULTIMATE_SPECIES
            else PET_EVOLUTION_IMAGE_PATH
        )
        frame_count = PET_EVOLUTION_FRAME_COUNT
        sprite_size = (
            PET_EVOLUTION_SIZE
            if profile.name == "pico"
            else profile.height - profile.menu_height
        )
        sprite_x = (profile.width - sprite_size) // 2
        sprite_y = profile.menu_height
    elif motion_state == "walk":
        if pet.species == ULTIMATE_SPECIES:
            image_path = DRAGFIREMON_FLY_IMAGE_PATH
            frame_count = DRAGFIREMON_FLY_FRAME_COUNT
        elif pet.species == EVOLVED_SPECIES:
            image_path = FLAMEMON_WALK_IMAGE_PATH
            frame_count = FLAMEMON_WALK_FRAME_COUNT
        else:
            image_path = PET_WALK_IMAGE_PATH
            frame_count = PET_WALK_FRAME_COUNT
    elif motion_state == "eat":
        if pet.species == ULTIMATE_SPECIES:
            image_path = DRAGFIREMON_EAT_IMAGE_PATH
        elif pet.species == EVOLVED_SPECIES:
            image_path = FLAMEMON_EAT_IMAGE_PATH
        else:
            image_path = PET_EAT_IMAGE_PATH
        frame_count = PET_EAT_FRAME_COUNT
    elif motion_state == "punch":
        if pet.species == ULTIMATE_SPECIES:
            image_path = DRAGFIREMON_PUNCH_IMAGE_PATH
        elif pet.species == EVOLVED_SPECIES:
            image_path = FLAMEMON_PUNCH_IMAGE_PATH
        else:
            image_path = PET_PUNCH_IMAGE_PATH
        frame_count = PET_PUNCH_FRAME_COUNT
    elif motion_state == "sleep":
        if pet.species == ULTIMATE_SPECIES:
            image_path = DRAGFIREMON_SLEEP_IMAGE_PATH
        elif pet.species == EVOLVED_SPECIES:
            image_path = FLAMEMON_SLEEP_IMAGE_PATH
        else:
            image_path = PET_SLEEP_IMAGE_PATH
        frame_count = PET_SLEEP_FRAME_COUNT
    elif motion_state == "cast":
        if pet.species == ULTIMATE_SPECIES:
            image_path = DRAGFIREMON_CAST_IMAGE_PATH
        elif pet.species == EVOLVED_SPECIES:
            image_path = FLAMEMON_CAST_IMAGE_PATH
        else:
            image_path = PET_CAST_IMAGE_PATH
        frame_count = PET_CAST_FRAME_COUNT
    else:
        if pet.species == ULTIMATE_SPECIES:
            image_path = DRAGFIREMON_IDLE_IMAGE_PATH
            frame_count = DRAGFIREMON_IDLE_FRAME_COUNT
        elif pet.species == EVOLVED_SPECIES:
            image_path = FLAMEMON_IDLE_IMAGE_PATH
            frame_count = FLAMEMON_IDLE_FRAME_COUNT
        else:
            image_path = PET_IDLE_IMAGE_PATH
            frame_count = PET_IDLE_FRAME_COUNT
    with Image.open(device_path(build_dir, image_path)) as opened:
        atlas = opened.copy()
    frame_index = sprite_frame % frame_count
    rookie = atlas.crop(
        (frame_index * sprite_size, 0, (frame_index + 1) * sprite_size, sprite_size)
    )
    if facing < 0 and motion_state != "evolution":
        rookie = rookie.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    transparency_mask = rookie.point([0] + [255] * 255, mode="L")
    frame.paste(rookie.convert("RGB"), (sprite_x, sprite_y), transparency_mask)
    if status_visible and panel_mode is None:
        panel_mode = "status"
    if panel_mode is not None:
        status = Image.new("P", (STATUS_WIDTH, STATUS_HEIGHT))
        palette = []
        for color in STATUS_COLORS:
            palette.extend(((color >> 16) & 0xFF, (color >> 8) & 0xFF, color & 0xFF))
        status.putpalette(palette + [0] * (768 - len(palette)))
        if panel_mode == "inventory":
            draw_inventory(status.load(), pet, panel_index)
        elif panel_mode == "evolution":
            draw_evolution_guide(status.load(), pet)
        elif panel_mode == "options" and options_session is not None:
            if options_session.mode == "wifi":
                draw_wifi(status.load(), pet, options_session)
            elif options_session.mode == "password":
                draw_password_editor(status.load(), pet, options_session)
            elif options_session.mode in ("date", "time"):
                draw_datetime_editor(status.load(), pet, options_session)
            else:
                draw_options(status.load(), pet, options_session, current_datetime)
        else:
            draw_status(status.load(), pet)
        panel = status.convert("RGB")
        if profile.name != "pico":
            panel = panel.resize(
                (profile.width, profile.height - profile.menu_height),
                Image.Resampling.NEAREST,
            )
        frame.paste(panel, (0, profile.menu_height))
        if panel_mode == "evolution":
            for path, x in (
                (FIREMON_EVOLUTION_THUMB_PATH, EVOLUTION_FIREMON_THUMB_X),
                (FLAMEMON_EVOLUTION_THUMB_PATH, EVOLUTION_FLAMEMON_THUMB_X),
                (DRAGFIREMON_EVOLUTION_THUMB_PATH, EVOLUTION_DRAGFIREMON_THUMB_X),
            ):
                with Image.open(device_path(build_dir, path)) as opened:
                    portrait = opened.copy()
                mask = portrait.point([0] + [255] * 255, mode="L")
                frame.paste(portrait.convert("RGB"), (x, EVOLUTION_THUMB_Y), mask)
    return frame
