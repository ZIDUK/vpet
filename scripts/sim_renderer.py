"""Deterministic renderer shared by simulator tests and pygame."""
from pathlib import Path
from functools import lru_cache

from PIL import Image, ImageDraw

from display_profiles import get_display_profile

from config import (
    BABY_SPECIES,
    BACKGROUND_PATH,
    BACKGROUND_NIGHT_PATH,
    DISPLAY_HEIGHT,
    DISPLAY_WIDTH,
    EGG_EVOLUTION_THUMB_PATH,
    EGG_IDLE_FRAME_COUNT,
    EGG_IDLE_IMAGE_PATH,
    EGG_SPECIES,
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
    ROOKIE_SPECIES,
    SPARKMON_EAT_IMAGE_PATH,
    SPARKMON_EVOLUTION_FRAME_COUNT,
    SPARKMON_EVOLUTION_IMAGE_PATH,
    SPARKMON_EVOLUTION_THUMB_PATH,
    SPARKMON_FRAME_COUNT,
    SPARKMON_IDLE_IMAGE_PATH,
    SPARKMON_SLEEP_IMAGE_PATH,
    SPARKMON_WALK_IMAGE_PATH,
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
    draw_status,
)


def device_path(build_dir, absolute_path):
    return Path(build_dir) / absolute_path.lstrip("/")


@lru_cache(maxsize=64)
def _load_image(path):
    with Image.open(path) as opened:
        return opened.copy()


def _draw_wide_panel(frame, build_dir, pet, panel_mode, panel_index, options_session):
    draw = ImageDraw.Draw(frame)
    panel = (214, 180, 112)
    ink = (48, 42, 55)
    yellow = (255, 210, 74)
    draw.rectangle((0, 24, 239, 134), fill=panel)
    draw.rectangle((3, 27, 236, 47), fill=ink)
    title = {
        "status": "STATUS",
        "inventory": "INVENTORY",
        "evolution": "EVOLUTION",
        "options": "OPTIONS",
    }.get(panel_mode, "VPET")
    draw.text((120, 37), title, fill=(255, 255, 255), anchor="mm")

    if panel_mode == "status":
        rows = (
            ("HP", pet.stats["hp"]), ("HUN", pet.stats["h"]),
            ("ENE", pet.stats["e"]), ("MOOD", pet.stats["p"]),
        )
        for index, (label, value) in enumerate(rows):
            x = 8 + (index % 2) * 116
            y = 55 + (index // 2) * 34
            draw.text((x, y), f"{label} {value}/100", fill=ink)
            draw.rectangle((x, y + 12, x + 104, y + 20), outline=ink)
            draw.rectangle((x + 2, y + 14, x + 2 + value, y + 18), fill=(196, 70, 56))
        draw.text((8, 122), f"AGE {int(pet.age_seconds)}s   WINS {pet.battles_won}", fill=ink)
    elif panel_mode == "inventory":
        items = ("MEAT x3", "TONIC x2", "MEDKIT x1", "BACK")
        for index, label in enumerate(items):
            x = 8 + (index % 2) * 116
            y = 55 + (index // 2) * 34
            draw.rectangle((x, y, x + 106, y + 27), outline=yellow if index == panel_index else ink, width=2)
            draw.text((x + 8, y + 9), label, fill=ink)
    elif panel_mode == "evolution":
        species = (
            ("Egg", "Egg.bmp"),
            ("Sparkmon", "Sparkmon.bmp"),
            ("Firemon", "Firemon.bmp"),
            ("Flamemon", "Flamemon.bmp"),
            ("Dragfiremon", "Dragfiremon.bmp"),
        )
        current_stage = {"egg": 0, "baby": 1, "rookie": 2, "champion": 3, "ultimate": 4}.get(pet.species, 0)
        window_start = max(0, min(panel_index - 1, len(species) - 3))
        for slot, index in enumerate(range(window_start, window_start + 3)):
            label, filename = species[index]
            x = 4 + slot * 79
            draw.rectangle((x, 52, x + 72, 124), outline=yellow if index == panel_index else ink, width=2)
            portrait = _load_image(Path(build_dir) / "UIEvolution" / filename)
            mask = portrait.point([0] + [255] * 255, mode="L")
            hidden = index > current_stage
            art = Image.new("RGB", portrait.size, (20, 20, 24)) if hidden else portrait.convert("RGB")
            frame.paste(art, (x + 18, 57), mask)
            draw.text((x + 36, 101), "???" if hidden else label.upper()[:10], fill=ink, anchor="mm")
            if index < len(species) - 1 and slot < 2:
                draw.text((x + 76, 76), ">", fill=ink, anchor="mm")
        draw.text((120, 130), "NEXT: MOVE   ACTION: DETAIL", fill=ink, anchor="mm")
    elif panel_mode == "options" and options_session is not None:
        if options_session.mode in ("date", "time"):
            draw.text((120, 67), options_session.mode.upper(), fill=ink, anchor="mm")
            value = " / ".join(str(item) for item in options_session.values)
            draw.rectangle((25, 79, 214, 111), outline=yellow, width=2)
            draw.text((120, 95), value, fill=ink, anchor="mm")
        else:
            labels = (
                f"BLUETOOTH: {options_session.bluetooth_status}",
                "LANGUAGE: ES", "SOUND: ON", "SAVE", "LOAD", "DATE", "TIME",
                "EVOLVE", "BACK",
            )
            current = options_session.index % 9
            window_start = 0 if current < 4 else (4 if current < 8 else 5)
            for slot in range(4):
                index = window_start + slot
                y = 52 + slot * 20
                if index == current:
                    draw.rectangle((5, y - 2, 234, y + 16), fill=yellow)
                draw.text((10, y), labels[index], fill=ink)


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
    frame = _load_image(device_path(build_dir, background_path)).convert("RGB")
    if frame.size != (profile.width, profile.height):
        raise ValueError(f"Background must be {profile.width}x{profile.height}")

    ImageDraw.Draw(frame).rectangle(
        (0, 0, profile.width - 1, profile.menu_height - 1),
        fill=(0, 0, 0),
    )
    for index, path in enumerate(MENU_ICON_PATHS):
        icon = _load_image(device_path(build_dir, path)).convert("RGB")
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
    if pet.species == EGG_SPECIES:
        image_path = EGG_IDLE_IMAGE_PATH
        frame_count = EGG_IDLE_FRAME_COUNT
        sprite_x = (profile.width - sprite_size) // 2
    elif pet.species == BABY_SPECIES:
        image_path = {
            "walk": SPARKMON_WALK_IMAGE_PATH,
            "eat": SPARKMON_EAT_IMAGE_PATH,
            "sleep": SPARKMON_SLEEP_IMAGE_PATH,
        }.get(motion_state, SPARKMON_IDLE_IMAGE_PATH)
        frame_count = SPARKMON_FRAME_COUNT
    elif motion_state == "evolution":
        if pet.species == ROOKIE_SPECIES:
            image_path = SPARKMON_EVOLUTION_IMAGE_PATH
            frame_count = SPARKMON_EVOLUTION_FRAME_COUNT
        elif pet.species == ULTIMATE_SPECIES:
            image_path = FLAMEMON_EVOLUTION_IMAGE_PATH
            frame_count = PET_EVOLUTION_FRAME_COUNT
        else:
            image_path = PET_EVOLUTION_IMAGE_PATH
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
    atlas = _load_image(device_path(build_dir, image_path))
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
        if profile.name == "tdisplay":
            _draw_wide_panel(
                frame, build_dir, pet, panel_mode, panel_index, options_session
            )
            return frame
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
            if options_session.mode in ("date", "time"):
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
                portrait = _load_image(device_path(build_dir, path))
                mask = portrait.point([0] + [255] * 255, mode="L")
                frame.paste(portrait.convert("RGB"), (x, EVOLUTION_THUMB_Y), mask)
    return frame
