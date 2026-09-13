"""Deterministic renderer shared by simulator tests and pygame."""
from pathlib import Path
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont

from display_profiles import get_display_profile

from config import (
    BABY_SPECIES,
    BACKGROUND_PATH,
    BACKGROUND_NIGHT_PATH,
    DISPLAY_HEIGHT,
    DISPLAY_WIDTH,
    EGG_EVOLUTION_THUMB_PATH,
    EGG_HATCH_FRAME_COUNT,
    EGG_HATCH_IMAGE_PATH,
    EGG_IDLE_FRAME_COUNT,
    EGG_IDLE_IMAGE_PATH,
    EGG_SPECIES,
    EVOLUTION_REGISTRY,
    DRAGFIREMON_CAST_IMAGE_PATH,
    DRAGFIREMON_EAT_IMAGE_PATH,
    DRAGFIREMON_EVOLUTION_THUMB_PATH,
    DRAGFIREMON_FLY_FRAME_COUNT,
    DRAGFIREMON_FLY_IMAGE_PATH,
    DRAGFIREMON_IDLE_FRAME_COUNT,
    DRAGFIREMON_IDLE_IMAGE_PATH,
    DRAGFIREMON_PUNCH_IMAGE_PATH,
    DRAGFIREMON_SLEEP_FRAME_COUNT,
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
from core.dna import HELIX_TURNS, format_dna_id, helix_color565, helix_depth, helix_sample, helix_spin, rgb565_to_rgb
from core.evolution import (
    EVOLUTION_NODE_COUNT,
    EVO_CHIP,
    evolution_card,
    evolution_hidden,
    evolution_current_stage,
    evolution_tree_node,
    evolution_tree_xy,
    evolution_window,
    split_requirement_lines,
)
from core.options import OPTION_ICONS
from core.inventory import (
    INVENTORY_ITEMS,
    clamp_visible_inventory_index,
    inventory_blurb,
    inventory_icon,
    inventory_name,
    inventory_window,
    visible_inventory_indexes,
)
from core.status_card import (
    HELIX_HEIGHT,
    HELIX_RUNGS,
    HELIX_WIDTH,
    HELIX_Y,
    STATUS_CARD_H,
    STATUS_CARD_ROW,
    STATUS_CARD_Y,
    STATUS_PAGE_COUNT,
    STATUS_SPLIT_X,
    battle_rows,
    care_rows,
    dna_stat_rows,
    pin_pet_x,
    vital_rows,
)
from scripts.sim_services import format_clock
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


@lru_cache(maxsize=4)
def _status_font(size):
    return ImageFont.load_default(size=size)


def _icon_glyph_mask(icon):
    gray = icon.convert("L")
    width, height = gray.size
    mask = gray.point(lambda pixel: 0 if pixel < 18 else 255)
    border = []
    for column in range(width):
        border.append(gray.getpixel((column, 0)))
        border.append(gray.getpixel((column, height - 1)))
    for row in range(1, height - 1):
        border.append(gray.getpixel((0, row)))
        border.append(gray.getpixel((width - 1, row)))
    if border and sum(1 for pixel in border if pixel < 96) < int(len(border) * 0.65):
        return mask
    inset = 2 if min(width, height) >= 16 else 1
    pixels = mask.load()
    source = gray.load()
    for row in range(height):
        for column in range(width):
            if column < inset or row < inset or column >= width - inset or row >= height - inset:
                if source[column, row] < 96:
                    pixels[column, row] = 0
    return mask


def _paste_ui_icon(frame, build_dir, name, x, y, size=20):
    icon = _load_image(device_path(build_dir, f"/UIIcons/{name}.bmp")).convert("RGB")
    if icon.size != (size, size):
        icon = icon.resize((size, size), Image.Resampling.NEAREST)
    frame.paste(icon, (x, y), _icon_glyph_mask(icon))


def _mix(color, other, amount):
    return tuple(int(color[index] * (1 - amount) + other[index] * amount) for index in range(3))


def _draw_stat_chip(frame, draw, build_dir, icon, label, value, x, y, ink, muted, font, width=64, extra=""):
    draw.rounded_rectangle(
        (x, y, x + width, y + STATUS_CARD_H),
        radius=5,
        fill=_mix(ink, (214, 180, 112), 0.88),
        outline=ink,
    )
    _paste_ui_icon(frame, build_dir, icon, x + 2, y + 2, 20)
    if extra:
        draw.text((x + 24, y + 2), label, fill=muted, font=font)
        draw.text((x + 24, y + 13), extra, fill=muted, font=_status_font(10))
        draw.text((x + width - 3, y + 2), str(value), fill=ink, font=font, anchor="ra")
        return
    draw.text((x + 24, y + 6), label, fill=muted, font=font)
    draw.text((x + width - 3, y + 6), str(value), fill=ink, font=font, anchor="ra")


def _draw_helix(draw, x, y, dna, width=HELIX_WIDTH, height=HELIX_HEIGHT, spin=None):
    color_a = rgb565_to_rgb(helix_color565(dna, 0))
    color_b = rgb565_to_rgb(helix_color565(dna, 1))
    empty = not dna or not any(dna)
    spin = helix_spin(0) if spin is None else spin
    well = (36, 28, 34)
    draw.rounded_rectangle((x - 2, y - 2, x + width + 2, y + height + 2), radius=4, fill=well)
    steps = 48
    points_a = []
    points_b = []
    for index in range(steps + 1):
        t = index / steps
        yy = y + int(round(t * height))
        points_a.append((x + helix_sample(0, t, width, turns=HELIX_TURNS, spin=spin), yy, helix_depth(0, t, turns=HELIX_TURNS, spin=spin)))
        points_b.append((x + helix_sample(1, t, width, turns=HELIX_TURNS, spin=spin), yy, helix_depth(1, t, turns=HELIX_TURNS, spin=spin)))

    def draw_strand(points, color, back):
        dim = _mix(color, well, 0.5)
        for index in range(len(points) - 1):
            depth = points[index][2]
            if back and depth >= 0:
                continue
            if not back and depth < 0:
                continue
            draw.line((points[index][:2], points[index + 1][:2]), fill=dim if back else color, width=2 if not back else 1)

    draw_strand(points_a, color_a, True)
    draw_strand(points_b, color_b, True)
    if not empty:
        for rung in range(HELIX_RUNGS):
            t = (rung + 0.5) / HELIX_RUNGS
            index = min(steps, int(round(t * steps)))
            xa, ya, _ = points_a[index]
            xb, yb, _ = points_b[index]
            rung_color = color_a if rung % 2 == 0 else color_b
            draw.line((xa, ya, xb, yb), fill=_mix(rung_color, well, 0.1), width=1)
            draw.ellipse((xa - 2, ya - 2, xa + 2, ya + 2), fill=color_a, outline=_mix(color_a, (255, 255, 255), 0.35))
            draw.ellipse((xb - 2, yb - 2, xb + 2, yb + 2), fill=color_b, outline=_mix(color_b, (255, 255, 255), 0.35))
    draw_strand(points_a, color_a, False)
    draw_strand(points_b, color_b, False)


def _draw_meter(draw, x, y, width, value, maximum, fill, ink):
    draw.rounded_rectangle((x, y, x + width, y + 7), radius=2, outline=ink)
    filled = int(max(0, min(maximum, value)) * (width - 2) / maximum) if maximum else 0
    if filled > 1:
        draw.rectangle((x + 1, y + 1, x + 1 + filled, y + 6), fill=fill)


def _call_label(pet, spanish):
    if getattr(pet, "dead", False):
        return "MUERTO" if spanish else "DEAD"
    if getattr(pet, "injured", False):
        return "HERIDO" if spanish else "HURT"
    call = getattr(pet, "call_reason", None)
    if call == "hunger":
        return "LLAM HAM" if spanish else "CALL HUN"
    if call == "strength":
        return "LLAM FUE" if spanish else "CALL STR"
    if call == "lights":
        return "LLAM LUZ" if spanish else "CALL LIT"
    return ""


def _clock_extra(current_datetime):
    clock = format_clock(current_datetime)
    if clock == "--":
        return ""
    return clock[5:]


def _draw_tdisplay_status(frame, draw, build_dir, pet, panel_index, current_datetime, ink, yellow, now_ms=0):
    spanish = getattr(pet, "language", "EN") == "ES"
    page = panel_index % STATUS_PAGE_COUNT
    muted = _mix(ink, (214, 180, 112), 0.28)
    bar = (49, 28, 39)
    font = _status_font(12)
    small = _status_font(10)
    x = STATUS_SPLIT_X + 4
    width = 232 - STATUS_SPLIT_X
    if page == 0:
        for index, (icon, label, value) in enumerate(vital_rows(pet, spanish)):
            y = STATUS_CARD_Y + index * STATUS_CARD_ROW
            draw.rounded_rectangle(
                (x, y, x + width, y + STATUS_CARD_H),
                radius=5,
                fill=_mix(ink, (214, 180, 112), 0.88),
                outline=ink,
            )
            _paste_ui_icon(frame, build_dir, icon, x + 2, y + 2, 20)
            draw.text((x + 24, y + 1), label, fill=muted, font=font)
            draw.text((x + width - 4, y + 1), str(max(0, min(100, value))), fill=ink, font=font, anchor="ra")
            _draw_meter(draw, x + 24, y + 14, width - 30, value, 100, bar, ink)
        return
    if page == 3:
        dna = getattr(pet, "dna", [0, 0, 0, 0])
        _draw_helix(
            draw,
            x + 2,
            HELIX_Y,
            dna,
            width=HELIX_WIDTH,
            height=HELIX_HEIGHT,
            spin=helix_spin(now_ms),
        )
        draw.text((x + 44, STATUS_CARD_Y + 2), format_dna_id(dna), fill=ink, font=small, anchor="lm")
        rows = dna_stat_rows(pet)
        if not rows:
            return
        for index, (label, value, _ev) in enumerate(rows):
            y = 64 + index * 11
            draw.text((x + 56, y + 5), label, fill=muted, font=small, anchor="lm")
            draw.text((x + 82, y + 5), "%02d" % value, fill=ink, font=small, anchor="lm")
            _draw_meter(draw, x + 100, y + 2, width - 102, value, 99, rgb565_to_rgb(helix_color565(dna, 0)), ink)
        return
    left = x
    right = x + 68
    row0 = STATUS_CARD_Y
    row1 = STATUS_CARD_Y + STATUS_CARD_ROW
    row2 = STATUS_CARD_Y + STATUS_CARD_ROW * 2
    if page == 2:
        rows = battle_rows(pet, spanish)
        _draw_stat_chip(frame, draw, build_dir, rows[0][0], rows[0][1], rows[0][2], left, row0, ink, muted, font)
        _draw_stat_chip(frame, draw, build_dir, rows[1][0], rows[1][1], rows[1][2], right, row0, ink, muted, font)
        _draw_stat_chip(frame, draw, build_dir, rows[2][0], rows[2][1], rows[2][2], left, row1, ink, muted, font)
        _draw_stat_chip(frame, draw, build_dir, rows[3][0], rows[3][1], rows[3][2], right, row1, ink, muted, font)
        _draw_stat_chip(frame, draw, build_dir, rows[4][0], rows[4][1], rows[4][2], left, row2, ink, muted, font, width)
        return
    rows = care_rows(pet, spanish, _clock_extra(current_datetime), _call_label(pet, spanish))
    _draw_stat_chip(frame, draw, build_dir, rows[0][0], rows[0][1], rows[0][2], left, row0, ink, muted, font, width, rows[0][3])
    _draw_stat_chip(frame, draw, build_dir, rows[1][0], rows[1][1], rows[1][2], left, row1, ink, muted, font)
    _draw_stat_chip(frame, draw, build_dir, rows[2][0], rows[2][1], rows[2][2], right, row1, ink, muted, font)
    _draw_stat_chip(frame, draw, build_dir, rows[3][0], rows[3][1], rows[3][2], left, row2, ink, muted, font)
    _draw_stat_chip(frame, draw, build_dir, rows[4][0], rows[4][1], rows[4][2], right, row2, ink, muted, font)


def _draw_wide_panel(frame, build_dir, pet, panel_mode, panel_index, options_session, current_datetime=None, now_ms=0):
    draw = ImageDraw.Draw(frame)
    panel = (214, 180, 112)
    ink = (48, 42, 55)
    yellow = (255, 210, 74)
    if panel_mode == "status":
        draw.rectangle((0, 24, 239, 134), fill=panel)
        draw.rectangle((3, 27, 236, 47), fill=ink)
        draw.text(
            (120, 37),
            "STATUS %d/%d" % ((panel_index % STATUS_PAGE_COUNT) + 1, STATUS_PAGE_COUNT),
            fill=(255, 255, 255),
            font=_status_font(12),
            anchor="mm",
        )
        _draw_tdisplay_status(frame, draw, build_dir, pet, panel_index, current_datetime, ink, yellow, now_ms)
        return
    draw.rectangle((0, 24, 239, 134), fill=panel)
    draw.rectangle((3, 27, 236, 47), fill=ink)
    title = {
        "inventory": "INVENTORY",
        "evolution": "EVOLUTION",
        "evolution_detail": "EVOLUTION",
        "options": "OPTIONS",
    }.get(panel_mode, "VPET")
    draw.text((120, 37), title, fill=(255, 255, 255), anchor="mm")

    if panel_mode == "inventory":
        spanish = getattr(pet, "language", "EN") == "ES"
        visible = visible_inventory_indexes(pet)
        current = clamp_visible_inventory_index(pet, panel_index)
        chip = _mix(ink, panel, 0.88)
        outline = _mix(ink, panel, 0.45)
        _paste_ui_icon(frame, build_dir, inventory_icon(current), 30, 62, 40)
        draw.text((50, 108), inventory_name(current, spanish), fill=ink, font=_status_font(12), anchor="mm")
        draw.text((50, 122), inventory_blurb(current, spanish), fill=_mix(ink, panel, 0.28), font=_status_font(10), anchor="mm")
        x = STATUS_SPLIT_X + 4
        width = 232 - STATUS_SPLIT_X
        for slot, index in enumerate(inventory_window(visible, current)):
            y = STATUS_CARD_Y + slot * STATUS_CARD_ROW
            border = yellow if index == current else outline
            draw.rounded_rectangle((x, y, x + width, y + STATUS_CARD_H), radius=5, fill=chip, outline=border)
            _paste_ui_icon(frame, build_dir, inventory_icon(index), x + 2, y + 2, 20)
            if index < len(INVENTORY_ITEMS):
                _, key, _, _ = INVENTORY_ITEMS[index]
                label = "%s x%d" % (inventory_name(index, spanish), pet.inventory.get(key, 0))
            else:
                label = inventory_name(index, spanish)
            draw.text((x + 24, y + 6), label, fill=ink, font=_status_font(12))
    elif panel_mode == "evolution":
        species = ("Egg.bmp", "Sparkmon.bmp", "Firemon.bmp", "Flamemon.bmp", "Dragfiremon.bmp")
        current_stage = evolution_current_stage(pet)
        selected = panel_index % EVOLUTION_NODE_COUNT
        chip = _mix(ink, panel, 0.88)
        outline = _mix(ink, panel, 0.45)
        spark_x, spark_y = evolution_tree_xy(1)
        fire_x, fire_y = evolution_tree_xy(2)
        _dark_x, dark_y = evolution_tree_xy(5)
        mid_x = spark_x + EVO_CHIP
        fork_x = fire_x
        draw.line((mid_x, spark_y + EVO_CHIP // 2, fork_x, fire_y + EVO_CHIP // 2), fill=ink, width=2)
        draw.line((fork_x, fire_y + EVO_CHIP // 2, fork_x, dark_y + EVO_CHIP // 2), fill=ink, width=2)
        for index in range(EVOLUTION_NODE_COUNT):
            stage, dark = evolution_tree_node(index)
            x, y = evolution_tree_xy(index)
            hidden = evolution_hidden(stage, dark, current_stage)
            active = index == selected
            draw.rounded_rectangle((x, y, x + EVO_CHIP, y + EVO_CHIP), radius=4, fill=chip, outline=yellow if active else outline)
            portrait = _load_image(Path(build_dir) / "UIEvolution" / species[stage])
            thumb = portrait.resize((32, 32), Image.Resampling.NEAREST)
            mask = thumb.point([0] + [255] * 255, mode="L")
            art = Image.new("RGB", thumb.size, (20, 20, 24)) if hidden else thumb.convert("RGB")
            frame.paste(art, (x + 4, y + 4), mask)
    elif panel_mode == "evolution_detail":
        spanish = getattr(pet, "language", "EN") == "ES"
        selected = panel_index % EVOLUTION_NODE_COUNT
        card = evolution_card(selected, pet, EVOLUTION_REGISTRY, spanish)
        chip = _mix(ink, panel, 0.88)
        outline = _mix(ink, panel, 0.45)
        muted = _mix(ink, panel, 0.28)
        portrait = _load_image(Path(build_dir) / "UIEvolution" / card["portrait"])
        thumb = portrait.resize((36, 36), Image.Resampling.NEAREST)
        mask = thumb.point([0] + [255] * 255, mode="L")
        art = Image.new("RGB", thumb.size, (20, 20, 24)) if card["hidden"] else thumb.convert("RGB")
        frame.paste(art, (32, 56), mask)
        draw.text((50, 96), card["label"], fill=ink, font=_status_font(12), anchor="mm")
        status = card["status"] if not card["snapshot"] else "%s %s" % (card["status"], card["snapshot"])
        draw.text((50, 108), status, fill=muted, font=_status_font(10), anchor="mm")
        first, second = split_requirement_lines(card["requirements"])
        if first:
            draw.text((50, 118), first, fill=muted, font=_status_font(10), anchor="mm")
        if second:
            draw.text((50, 128), second, fill=muted, font=_status_font(10), anchor="mm")
        x = STATUS_SPLIT_X + 4
        width = 232 - STATUS_SPLIT_X
        for slot, index in enumerate(evolution_window(selected)):
            y = STATUS_CARD_Y + slot * STATUS_CARD_ROW
            entry = evolution_card(index, pet, EVOLUTION_REGISTRY, spanish)
            border = yellow if index == selected else outline
            draw.rounded_rectangle((x, y, x + width, y + STATUS_CARD_H), radius=5, fill=chip, outline=border)
            _paste_ui_icon(frame, build_dir, "Pedia", x + 2, y + 2, 20)
            draw.text((x + 24, y + 6), entry["label"], fill=ink, font=_status_font(12))
    elif panel_mode == "options" and options_session is not None:
        if options_session.mode in ("date", "time"):
            draw.text((120, 67), options_session.mode.upper(), fill=ink, font=_status_font(12), anchor="mm")
            value = " / ".join(str(item) for item in options_session.values)
            draw.rounded_rectangle((25, 79, 214, 111), radius=5, outline=yellow, width=2)
            draw.text((120, 95), value, fill=ink, font=_status_font(13), anchor="mm")
        else:
            labels = (
                ("BT", options_session.bluetooth_status[:3]),
                ("LANG", "ES"),
                ("SND", "ON"),
                ("SAVE", ""),
                ("LOAD", ""),
                ("DATE", ""),
                ("TIME", ""),
                ("EVO", ""),
                ("BACK", ""),
            )
            current = options_session.index % 9
            chip = _mix(ink, panel, 0.88)
            outline = _mix(ink, panel, 0.45)
            for index, (label, extra) in enumerate(labels):
                col = index % 3
                row = index // 3
                x = 8 + col * 76
                y = 54 + row * 26
                selector = (255, 215, 0)
                border = selector if index == current else outline
                draw.rounded_rectangle(
                    (x, y, x + 72, y + 24),
                    radius=5,
                    fill=selector if index == current else chip,
                    outline=border,
                )
                _paste_ui_icon(frame, build_dir, OPTION_ICONS[index], x + 2, y + 2, 20)
                text = label if not extra else "%s %s" % (label, extra)
                draw.text((x + 46, y + 12), text, fill=ink, font=_status_font(10), anchor="mm")


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
    now_ms=0,
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
        if motion_state == "hatch":
            image_path = EGG_HATCH_IMAGE_PATH
            frame_count = EGG_HATCH_FRAME_COUNT
        else:
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
        frame_count = (
            DRAGFIREMON_SLEEP_FRAME_COUNT
            if pet.species == ULTIMATE_SPECIES
            else PET_SLEEP_FRAME_COUNT
        )
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
    status_split = profile.name == "tdisplay" and (panel_mode == "status" or status_visible)
    if status_split and motion_state != "evolution":
        sprite_x = pin_pet_x(sprite_size)
        sprite_y = 47
        if pet.species == EGG_SPECIES:
            image_path = EGG_IDLE_IMAGE_PATH
            frame_count = EGG_IDLE_FRAME_COUNT
        elif pet.species == BABY_SPECIES:
            image_path = SPARKMON_IDLE_IMAGE_PATH
            frame_count = SPARKMON_FRAME_COUNT
        elif pet.species == ULTIMATE_SPECIES:
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
    if not status_split:
        frame.paste(rookie.convert("RGB"), (sprite_x, sprite_y), transparency_mask)
    if status_visible and panel_mode is None:
        panel_mode = "status"
    if panel_mode is not None:
        if profile.name == "tdisplay":
            _draw_wide_panel(
                frame, build_dir, pet, panel_mode, panel_index, options_session, current_datetime, now_ms
            )
            if status_split:
                frame.paste(rookie.convert("RGB"), (sprite_x, sprite_y), transparency_mask)
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
            draw_status(status.load(), pet, page=panel_index)
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
