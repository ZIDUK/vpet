"""Deterministic renderer shared by simulator tests and pygame."""
from pathlib import Path
from core.sleep import is_night
from core.menu import tdisplay_menu_available
from core.cues import pet_cue, bubble_name, bubble_position, rest_detail
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
    TDISPLAY_MENU_ICON_PATHS,
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
    EVO_COLOR_Y,
    EVO_GAP,
    EVO_X0,
    evolution_card,
    evolution_hidden,
    evolution_current_stage,
    evolution_tree_node,
    evolution_tree_xy,
    evolution_window,
    split_requirement_lines,
)
from core.options import OPTION_COUNT, OPTION_ICONS, OPTION_ORDER, OPTION_WINDOW, option_window_start
from core.inventory import (
    INVENTORY_ITEMS,
    clamp_visible_inventory_index,
    inventory_blurb,
    inventory_icon,
    inventory_name,
    inventory_window,
    visible_inventory_indexes,
)
from core.item_catalog import ITEM_BY_ID, effect_amount
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


def render_boot_intro(progress, assets_ok=True):
    """Render the small 240x135 startup animation used by the T-Display."""
    frame = Image.new("RGB", (240, 135), (4, 8, 18))
    draw = ImageDraw.Draw(frame)
    draw.rectangle((3, 3, 236, 131), outline=(90, 90, 100), width=1)
    draw.text((120, 18 if progress >= 0.55 else 54), "vPET",
              fill=(255, 174, 35), anchor="mm", font=_status_font(22))
    flame_x = int(82 + min(1.0, progress * 1.35) * 76)
    flame_y = 43 if progress < 0.55 else 25
    draw.polygon(((flame_x, flame_y + 13), (flame_x + 7, flame_y - 2),
                  (flame_x + 14, flame_y + 13)), fill=(255, 112, 18))
    draw.polygon(((flame_x + 4, flame_y + 12), (flame_x + 7, flame_y + 3),
                  (flame_x + 11, flame_y + 12)), fill=(255, 224, 55))
    if progress >= 0.72 and assets_ok:
        draw.text((120, 84), "FIREMON", fill=(255, 150, 30),
                  anchor="mm", font=_status_font(12))
        draw.text((120, 119), "READY", fill=(90, 230, 80),
                  anchor="mm", font=_status_font(16))
    elif progress >= 0.72:
        draw.text((120, 76), "ASSETS MISSING", fill=(235, 60, 60),
                  anchor="mm", font=_status_font(12))
    return frame


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


def _paste_mood(frame, build_dir, name, x, y, size=None, flip=False):
    icon = _load_image(build_dir / "UIMood" / (name + ".bmp"))
    if size is not None:
        icon = icon.resize(size, Image.Resampling.NEAREST)
    if flip:
        icon = icon.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    mask = icon.point([0] + [255] * 255, mode="L")
    frame.paste(icon.convert("RGB"), (x, y), mask)


def _draw_pet_cue(frame, build_dir, pet, x, y, facing, motion_state, tired, minute=None):
    if motion_state not in ("idle", "walk"):
        return
    need, _, angry = pet_cue(pet, tired)
    name = bubble_name(need, angry)
    detail=rest_detail(pet,tired,minute)
    if detail['kind']=='energy':
        name='energy_angry' if angry else 'energy'
    if name is not None:
        bx, by, flip = bubble_position(x, y, facing)
        _paste_mood(frame, build_dir, name, bx, by, flip=flip)


def _paste_ui_icon(frame, build_dir, name, x, y, size=20):
    if name.startswith('Adopted:'):
        icon = _load_image(build_dir / 'UIItems' / (name.split(':', 1)[1] + '.png')).convert('RGBA')
        icon = icon.resize((size, size), Image.Resampling.NEAREST)
        frame.paste(icon, (x, y), icon)
        return
    icon = _load_image(device_path(build_dir, f"/UIIcons/{name}.bmp")).convert("RGB")
    if icon.size != (size, size):
        icon = icon.resize((size, size), Image.Resampling.NEAREST)
    frame.paste(icon, (x, y), _icon_glyph_mask(icon))


def _mix(color, other, amount):
    return tuple(int(color[index] * (1 - amount) + other[index] * amount) for index in range(3))


def _draw_wide_row(frame, draw, build_dir, icon, label, value, x, y, ink, muted, font, width=128, height=14, extra=""):
    """Full-width single-column row for the care (2/4) and battle (3/4)
    pages. The approved mockup stacks five rows vertically across the
    full 128 px of the right side. Each row is 14 px tall with a 12 px
    icon on the left, the label in the middle, and the value right-
    aligned. The 14 px height lets five rows fit in the 78 px content
    area (y=54..132) without clipping the bottom of the frame."""
    draw.rounded_rectangle(
        (x, y, x + width, y + height),
        radius=3,
        fill=_mix(ink, (214, 180, 112), 0.88),
        outline=ink,
    )
    icon_size = min(13, height - 2)
    _paste_ui_icon(frame, build_dir, icon, x + 1, y + 1, icon_size)
    text_y = y + (height - 10) // 2
    draw.text((x + icon_size + 4, text_y), label, fill=muted,
              font=_status_font(10))
    if extra:
        draw.text((x + icon_size + 4, text_y + 9), extra, fill=muted,
                  font=_status_font(7))
    draw.text((x + width - 3, text_y), str(value), fill=ink,
              font=_status_font(10), anchor="ra")


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


def _vital_raw(pet, kind):
    """Map a vital row kind back to the raw 0..100 value used by the
    meter. The formatted string (``85/100``) is shown to the player;
    the raw value drives the bar fill. Both are derived from the same
    pet field so the two never disagree."""
    if kind == "hp_care":
        return int(pet.stats.get("hp", 0))
    if kind == "feed":
        return int(pet.stats.get("h", 0))
    if kind == "energy":
        return int(pet.stats.get("e", 0))
    if kind == "mood":
        return int(pet.stats.get("p", 0))
    return 0


def _clock_extra(current_datetime):
    clock = format_clock(current_datetime)
    if clock == "--":
        return ""
    return clock[5:]


def _draw_tdisplay_status(frame, draw, build_dir, pet, panel_index, current_datetime, ink, yellow, now_ms=0):
    """Paint the four Status pages (1/4 vital, 2/4 care, 3/4 battle,
    4/4 DNA). The pet sprite stays on the left half; the fiche on the
    right half shows icon + label + value chips. NEXT cycles the page
    number in the header. The renderer never mutates the pet: the
    helix rotation is derived from ``now_ms`` and the stat values are
    read from the pet without writing back."""
    spanish = getattr(pet, "language", "EN") == "ES"
    page = panel_index % STATUS_PAGE_COUNT
    muted = _mix(ink, (214, 180, 112), 0.28)
    font = _status_font(12)
    x = STATUS_SPLIT_X + 4
    width = 232 - STATUS_SPLIT_X

    if page == 0:
        # Four care meters; combat HP remains on the DNA page.
        bar_colors = {
            "hp_care": (241, 93, 112),    # red
            "feed":    (255, 174, 35),    # orange
            "energy":  (71, 191, 230),    # cyan
            "mood":    (82, 218, 140),    # green
        }
        for index, (icon, label, value_str, kind) in enumerate(vital_rows(pet, spanish)):
            x = STATUS_SPLIT_X + 1
            width = 131
            y = 49 + index * 21
            card_h = 19
            draw.rounded_rectangle(
                (x, y, x + width, y + card_h),
                radius=5,
                fill=_mix(ink, (214, 180, 112), 0.88),
                outline=ink,
            )
            if kind == "mood":
                _paste_mood(frame, build_dir, "face_" + pet_cue(pet)[1], x + 2, y + 2, (16, 16))
            else:
                _paste_ui_icon(frame, build_dir, icon, x + 2, y + 2, 16)
            draw.text((x + 22, y + 2), label, fill=muted,
                      font=_status_font(8))
            draw.text((x + width - 4, y + 2), value_str, fill=ink,
                      font=_status_font(8), anchor="ra")
            raw = _vital_raw(pet, kind)
            _draw_meter(draw, x + 22, y + 12, width - 29, raw, 100,
                          bar_colors.get(kind, (49, 28, 39)), ink)
        return

    if page == 3:
        # 4/4 DNA: full code on the right of the helix, six combat
        # stats with bars on a 0..99 scale. The code is rendered with
        # the medium font so the full "DNA: XX-XX-XX-XX" stays
        # readable; the stats use 3-char labels to leave room for the
        # bar. The helix rotation is derived from ``now_ms``; the
        # stat values are read from the pet and never written back.
        from core.i18n import tr_status_dna_label
        dna = getattr(pet, "dna", [0, 0, 0, 0])
        _draw_helix(
            draw,
            STATUS_SPLIT_X + 2,
            58,
            dna,
            width=40,
            height=68,
            spin=helix_spin(now_ms),
        )
        rows = dna_stat_rows(pet)
        if not rows:
            # Honest placeholder when the pet has no DNA yet (egg).
            from core.i18n import tr
            draw.text((STATUS_SPLIT_X + 43, 61), tr(pet, "status.dna.empty"),
                      fill=muted, font=_status_font(8), anchor="lm")
            return
        stat_icons = {
            "hp": "Heart", "mp": "Energy", "off": "Training",
            "def": "Battle", "spd": "Back", "brn": "Brain",
        }
        bar_color = (144, 91, 220)
        draw.text((215, 47), "EV", fill=muted, font=_status_font(8))
        for index, (key, value, ev) in enumerate(rows):
            y = 55 + index * 13
            label = tr_status_dna_label(pet, key)[:3]
            card_x = 145
            card_right = 237
            draw.rounded_rectangle((card_x, y, card_right, y + 12), radius=2,
                                   fill=_mix(ink, (214, 180, 112), 0.88),
                                   outline=ink)
            _paste_ui_icon(frame, build_dir, stat_icons[key], card_x + 2,
                           y + 1, 10)
            label_font = _status_font(8)
            if label_font.getlength(label) > 18:
                label_font = _status_font(7)
            draw.text((card_x + 14, y + 1), label, fill=muted,
                      font=label_font)
            draw.text((card_x + 34, y + 1), "%02d" % value, fill=ink,
                      font=_status_font(8))
            _draw_meter(draw, card_x + 48, y + 2, 18, value, 99,
                        bar_color, ink)
            draw.text((card_x + 88, y + 1), str(ev), fill=ink,
                      font=_status_font(8), anchor="ra")
        return

    # Battle retains five rows; care uses six shorter rows.
    if page == 2:
        rows = battle_rows(pet, spanish)
        # Five rows fill the content column while preserving a small
        # bottom margin at the 240x135 target resolution.
        wide_x = STATUS_SPLIT_X + 1
        wide_w = 131
        wide_h = 16
        wide_gap = 1
        for index, row_data in enumerate(rows):
            wide_y = 48 + index * (wide_h + wide_gap)
            _draw_wide_row(frame, draw, build_dir, row_data[0],
                            row_data[1], row_data[2],
                            wide_x, wide_y, ink, muted, font,
                            width=wide_w, height=wide_h)
        return
    # page == 1: care
    rows = care_rows(pet, spanish, _clock_extra(current_datetime),
                      _call_label(pet, spanish))
    # Keep the age value concise; care-call details remain available
    # through the pet state elsewhere in the interface.
    wide_x = STATUS_SPLIT_X + 1
    wide_w = 131
    wide_h = 13
    wide_gap = 1
    for index, row_data in enumerate(rows):
        wide_y = 48 + index * (wide_h + wide_gap)
        _draw_wide_row(frame, draw, build_dir, row_data[0],
                        row_data[1], row_data[2],
                        wide_x, wide_y, ink, muted, font,
                        width=wide_w, height=wide_h)


def _draw_wide_panel(frame, build_dir, pet, panel_mode, panel_index, options_session, current_datetime=None, now_ms=0, exploration_menu=None):
    from core.i18n import tr
    if panel_mode == "explore" and hasattr(exploration_menu, "choices"):
        from scripts.exploration_renderer import draw_exploration
        draw_exploration(frame, build_dir, pet, exploration_menu, exploration_menu.now(), now_ms)
        return
    draw = ImageDraw.Draw(frame)
    panel = (214, 180, 112)
    ink = (48, 42, 55)
    yellow = (255, 210, 74)
    green = (66, 190, 140)
    if panel_mode == "status":
        draw.rectangle((0, 24, 239, 134), fill=panel)
        draw.rectangle((3, 27, 236, 47), fill=ink)
        # Left-aligned header text inside the dark band. The approved
        # mockup anchors the label to the left edge. The text starts
        # at x=14 so the band background at (10, 35) remains clean
        # ink for the existing layout test.
        draw.text(
            (14, 37),
            tr(pet, "status.header",
               (panel_index % STATUS_PAGE_COUNT) + 1, STATUS_PAGE_COUNT),
            fill=(255, 255, 255),
            font=_status_font(12),
            anchor="lm",
        )
        if panel_index % STATUS_PAGE_COUNT == 3:
            dna_id = format_dna_id(getattr(pet, "dna", [0, 0, 0, 0]))
            draw.text((233, 37), dna_id,
                      fill=(214, 180, 112), font=_status_font(8),
                      anchor="rm")
        _draw_tdisplay_status(frame, draw, build_dir, pet, panel_index, current_datetime, ink, yellow, now_ms)
        return
    draw.rectangle((0, 24, 239, 134), fill=panel)
    draw.rectangle((3, 27, 236, 47), fill=ink)
    spanish = getattr(pet, "language", "EN") == "ES"
    title = {
        "feeding": "ALIMENTAR" if spanish else "FEED",
        "inventory": "MOCHILA" if spanish else "INVENTORY",
        "evolution": "EVOLUTION",
        "evolution_detail": "EVOLUTION",
        "options": "OPTIONS",
        "explore": "EXPLORE",
        "rest": tr(pet, "rest.title"),
    }.get(panel_mode, "VPET")
    draw.text((120, 37), title, fill=(255, 255, 255), anchor="mm")

    if panel_mode == "rest":
        labels=(tr(pet,"rest.on" if pet.sleep.asleep else "rest.off"),tr(pet,"rest.back"))
        for index,label in enumerate(labels):
            y=52+index*20
            if panel_index%2==index:
                draw.rectangle((5,y-2,234,y+16),fill=yellow)
            draw.text((10,y),label,fill=ink,font=_status_font(12))
    elif panel_mode == "inventory":
        visible = visible_inventory_indexes(pet)
        current = clamp_visible_inventory_index(pet, panel_index)
        chip = _mix(ink, panel, 0.88)
        outline = _mix(ink, panel, 0.45)
        from scripts.exploration_renderer import fitted_text
        if current >= 8:
            _paste_ui_icon(frame, build_dir, inventory_icon(current), 30, 55, 40)
            name = inventory_name(current, spanish)
            words, lines, line = name.split(), [], ''
            for word in words:
                candidate = (line + ' ' + word).strip()
                if _status_font(10).getlength(candidate) > 88 and line:
                    lines.append(line)
                    line = word
                else:
                    line = candidate
            lines.append(line)
            for i, line in enumerate(lines[:2]):
                fitted_text(draw, (6, 99 + i * 11, 94, 110 + i * 11), line, _status_font(10), ink)
            fitted_text(draw, (6, 123, 94, 134), inventory_blurb(current, spanish), _status_font(10), ink)
        else:
            _paste_ui_icon(frame, build_dir, inventory_icon(current), 30, 62, 40)
            draw.text((50, 108), inventory_name(current, spanish), fill=ink, font=_status_font(12), anchor="mm")
            draw.text((50, 122), inventory_blurb(current, spanish), fill=_mix(ink, panel, 0.28), font=_status_font(10), anchor="mm")
        x = STATUS_SPLIT_X + 4
        width = 232 - STATUS_SPLIT_X
        for slot, index in enumerate(inventory_window(visible, current)):
            y = STATUS_CARD_Y + slot * STATUS_CARD_ROW
            selector = (255, 215, 0)
            border = selector if index == current else outline
            draw.rounded_rectangle(
                (x, y, x + width, y + STATUS_CARD_H),
                radius=5,
                fill=selector if index == current else chip,
                outline=border,
            )
            _paste_ui_icon(frame, build_dir, inventory_icon(index), x + 2, y + 2, 20)
            if inventory_icon(index) == "ItemGuide":
                label = inventory_name(index, spanish) + " x1"
            elif index < len(INVENTORY_ITEMS):
                _, key, _, _ = INVENTORY_ITEMS[index]
                label = "%s x%d" % (inventory_name(index, spanish), pet.inventory.get(key, 0))
            elif index >= 8:
                from core.adopted_items import menu_item, short_name
                adopted = menu_item(index)
                count = 'x%d' % pet.adopted_inventory.get(adopted['id'], 0)
                fitted_text(draw, (x + 24, y + 3, x + width - 26, y + 20),
                            short_name(adopted, spanish), _status_font(10), ink)
                fitted_text(draw, (x + width - 25, y + 3, x + width - 3, y + 20),
                            count, _status_font(10), ink, right=True)
                continue
            else:
                label = inventory_name(index, spanish)
            draw.text((x + 24, y + 6), label, fill=ink, font=_status_font(12))
    elif panel_mode == "feeding":
        selected = int(panel_index or 0) % 3
        language = "ES" if spanish else "EN"
        for index, item_id in enumerate(("meat", "protein")):
            item = ITEM_BY_ID[item_id]
            icon = item["icon"]
            name, effect = item["names"][language], item["blurbs"][language]
            x = 7 + index * 115
            active = selected == index
            fill = yellow if active else _mix(ink, panel, 0.88)
            outline = yellow if active else _mix(ink, panel, 0.45)
            draw.rounded_rectangle((x, 56, x + 108, 109), radius=4,
                                   fill=fill, outline=outline)
            _paste_ui_icon(frame, build_dir, icon, x + 5, 66, 26)
            draw.text((x + 34, 64), name, fill=ink, font=_status_font(10))
            draw.text((x + 34, 82), effect, fill=ink, font=_status_font(8))
            note = "EN DESCANSO" if spanish else "RESTING"
            unlimited = "ILIMITADO" if spanish else "UNLIMITED"
            if index == 1 and (getattr(pet, "protein_fed_this_cycle", False)
                               or pet.get("e") > 100 - effect_amount("protein", "restore", "e")):
                draw.text((x + 34, 96), note, fill=(113, 122, 126), font=_status_font(7))
            else:
                draw.text((x + 34, 96), unlimited, fill=green, font=_status_font(7))
        back_fill = yellow if selected == 2 else _mix(ink, panel, 0.88)
        back_edge = yellow if selected == 2 else _mix(ink, panel, 0.45)
        draw.rounded_rectangle((7, 116, 231, 131), radius=3,
                               fill=back_fill, outline=back_edge)
        draw.text((119, 123), "VOLVER" if spanish else "BACK",
                  fill=ink, font=_status_font(8), anchor="mm")
    elif panel_mode == "evolution":
        species = ("Egg.bmp", "Sparkmon.bmp", "Firemon.bmp", "Flamemon.bmp", "Dragfiremon.bmp")
        current_stage = evolution_current_stage(pet)
        selected = current_stage if panel_index is None else panel_index % EVOLUTION_NODE_COUNT
        chip = _mix(ink, panel, 0.88)
        outline = _mix(ink, panel, 0.45)
        stride = EVO_CHIP + EVO_GAP
        center_y = EVO_COLOR_Y + EVO_CHIP // 2
        reached = (255, 220, 70)
        window = evolution_window(selected)
        for slot in range(len(window) - 1):
            stage = window[slot]
            x1 = EVO_X0 + slot * stride + EVO_CHIP
            x2 = x1 + EVO_GAP
            color = reached if stage < current_stage else outline
            draw.line((x1, center_y, x2 - 4, center_y), fill=color, width=2)
            draw.polygon(((x2 - 7, center_y - 3), (x2 - 4, center_y),
                          (x2 - 7, center_y + 3)), fill=color)
        for slot, index in enumerate(window):
            stage, _ = evolution_tree_node(index)
            x, y = evolution_tree_xy(index, window[0])
            hidden = evolution_hidden(stage, False, current_stage)
            active = index == selected
            selector = (255, 215, 0)
            draw.rounded_rectangle(
                (x, y, x + EVO_CHIP, y + EVO_CHIP),
                radius=4,
                fill=selector if active else chip,
                outline=selector if active else outline,
            )
            portrait = _load_image(Path(build_dir) / "UIEvolution" / species[stage])
            thumb = portrait.resize((32, 32), Image.Resampling.NEAREST)
            mask = thumb.point([0] + [255] * 255, mode="L")
            art = Image.new("RGB", thumb.size, (20, 20, 24)) if hidden else thumb.convert("RGB")
            frame.paste(art, (x, y), mask)
            card = evolution_card(index, pet, EVOLUTION_REGISTRY, spanish)
            name_color = (145, 165, 165) if hidden else ink
            draw.text((x + EVO_CHIP // 2, 98), card["label"],
                      fill=name_color, font=_status_font(8), anchor="mm")
        selected_card = evolution_card(selected, pet, EVOLUTION_REGISTRY, spanish)
        stage_status = selected_card["status"]
        progress_label = "%s  %d/5" % (stage_status, selected + 1)
        draw.text((120, 111), progress_label,
                  fill=ink, font=_status_font(9), anchor="mm")
        draw.rounded_rectangle((10, 122, 230, 129), radius=3, outline=outline)
        filled = 218 * (current_stage + 1) // EVOLUTION_NODE_COUNT
        draw.rounded_rectangle((11, 123, 11 + filled, 128), radius=2, fill=green)
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
            selector = (255, 215, 0)
            border = selector if index == selected else outline
            draw.rounded_rectangle(
                (x, y, x + width, y + STATUS_CARD_H),
                radius=5,
                fill=selector if index == selected else chip,
                outline=border,
            )
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
                ("SOUND", "ON"),
                ("SAVE", ""),
                ("LOAD", ""),
                ("DATE", ""),
                ("TIME", ""),
                ("EVO", ""),
                ("BACK", ""),
                (tr(pet,"options.pause"), tr(pet,"options.on" if getattr(pet,"cold",False) else "options.off")),
            )
            current = options_session.index % OPTION_COUNT
            start = option_window_start(OPTION_ORDER.index(current))
            chip = _mix(ink, panel, 0.88)
            outline = _mix(ink, panel, 0.45)
            selector = (255, 215, 0)
            x = 8
            width = 224
            for slot in range(OPTION_WINDOW):
                position = start + slot
                if position >= OPTION_COUNT:
                    break
                index = OPTION_ORDER[position]
                label, extra = labels[index]
                y = STATUS_CARD_Y + slot * STATUS_CARD_ROW
                border = selector if index == current else outline
                draw.rounded_rectangle(
                    (x, y, x + width, y + STATUS_CARD_H),
                    radius=5,
                    fill=selector if index == current else chip,
                    outline=border,
                )
                _paste_ui_icon(frame, build_dir, OPTION_ICONS[index], x + 2, y + 2, 20)
                text = label if not extra else "%s  %s" % (label, extra)
                draw.text((x + 28, y + 6), text, fill=ink, font=_status_font(12))


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
    panel_index=None,
    options_session=None,
    current_datetime=None,
    profile=None,
    now_ms=0,
    exploration_menu=None,
    exploration_now=None,
):
    """Render the composition shared with the CircuitPython display group."""
    profile = profile or get_display_profile("pico")
    build_dir = Path(build_dir)
    if panel_index is None and panel_mode != "evolution":
        panel_index = 0
    minute = (current_datetime[3]*60+current_datetime[4]
              if current_datetime and current_datetime[0]>=2024 else None)
    night = (minute is not None and is_night(minute)) if profile.name == "tdisplay" else motion_state == "sleep"
    background_path = BACKGROUND_NIGHT_PATH if night else BACKGROUND_PATH
    frame = _load_image(device_path(build_dir, background_path)).convert("RGB")
    if frame.size != (profile.width, profile.height):
        raise ValueError(f"Background must be {profile.width}x{profile.height}")

    ImageDraw.Draw(frame).rectangle(
        (0, 0, profile.width - 1, profile.menu_height - 1),
        fill=(0, 0, 0),
    )
    icons = TDISPLAY_MENU_ICON_PATHS if profile.name == "tdisplay" else MENU_ICON_PATHS
    stride = profile.width // len(icons)
    for index, path in enumerate(icons):
        icon = _load_image(device_path(build_dir, path)).convert("RGB")
        if profile.name == "tdisplay" and not tdisplay_menu_available(pet.species, index):
            icon = icon.point(lambda channel: channel >> 1)
        icon_x = index * stride + (stride - profile.icon_size) // 2
        icon_y = (profile.menu_height - profile.icon_size) // 2
        frame.paste(icon, (icon_x, icon_y))

    selector_x = (menu_index % len(icons)) * stride
    selector_color = (
        (MENU_SELECTOR_COLOR >> 16) & 0xFF,
        (MENU_SELECTOR_COLOR >> 8) & 0xFF,
        MENU_SELECTOR_COLOR & 0xFF,
    )
    ImageDraw.Draw(frame).rectangle(
        (selector_x, 0, selector_x + stride - 1, profile.menu_height - 1),
        outline=selector_color,
        width=1,
    )

    sprite_size = profile.pet_size
    sprite_x = int(pet_x)
    sprite_y = PET_Y if profile.name == "pico" else profile.height - sprite_size - 4
    tired = (profile.name == "tdisplay" and pet.species != EGG_SPECIES and
             motion_state in ("idle", "walk") and not pet.dead and not pet.injured and
             not getattr(pet, "cold", False) and
             pet.sleep.tired(pet.stats["e"], pet.dna[3], minute))
    angry = (profile.name == "tdisplay" and panel_mode is None and not status_visible and
             motion_state in ("idle", "walk") and not tired and
             pet_cue(pet)[0] is not None and pet_cue(pet)[1] == "angry")
    if pet.species == EGG_SPECIES:
        if motion_state == "hatch":
            image_path = EGG_HATCH_IMAGE_PATH
            frame_count = EGG_HATCH_FRAME_COUNT
        else:
            image_path = EGG_IDLE_IMAGE_PATH
            frame_count = EGG_IDLE_FRAME_COUNT
        sprite_x = (profile.width - sprite_size) // 2
    elif tired or angry:
        stage, name = {"baby": ("Baby", "sparkmon"), "rookie": ("Rookie", "firemon"),
                       "champion": ("Champion", "flamemon"), "ultimate": ("Ultimate", "dragfiremon")}[pet.species]
        image_path = "/digimon1/%s/%s_%s_atlas.bmp" % (stage,name,"tired" if tired else "angry")
        frame_count = 25
        sprite_frame = now_ms // 90
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
    elif pet.species == EVOLVED_SPECIES and motion_state in (
        "block", "hurt", "hit_react", "dodge", "happy", "sad", "hit",
    ):
        action = "punch" if motion_state == "hit" else motion_state
        image_path = f"/digimon1/Champion/flamemon_{action}_atlas.bmp"
        frame_count = 15
    elif pet.species == ULTIMATE_SPECIES and motion_state in ("block", "hurt", "happy", "sad", "hit"):
        action = "punch" if motion_state == "hit" else motion_state
        image_path = f"/digimon1/Ultimate/dragfiremon_{action}_atlas.bmp"
        frame_count = 15
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
    if profile.name == "tdisplay" and pet.exploration.away and panel_mode is None:
        from scripts.exploration_renderer import draw_exploration
        draw_exploration(frame, build_dir, pet, None, exploration_now, now_ms)
        return frame
    if status_visible and panel_mode is None:
        panel_mode = "status"
    if panel_mode is not None:
        if profile.name == "tdisplay":
            _draw_wide_panel(
                frame, build_dir, pet, panel_mode, panel_index, options_session,
                current_datetime, now_ms, exploration_menu,
            )
            if status_split:
                if pet.dead or pet.injured:
                    if pet.dead:
                        rookie = _load_image(build_dir / "UIFx" / "grave.bmp")
                    rookie = rookie.resize((76, 76), Image.Resampling.NEAREST)
                    transparency_mask = rookie.point([0] + [255] * 255, mode="L")
                    frame.paste(rookie.convert("RGB"), (12, 59), transparency_mask)
                    draw = ImageDraw.Draw(frame)
                    draw.text((50, 49), _call_label(pet, pet.language == "ES"),
                              font=_status_font(8), anchor="ma",
                              fill=(48, 42, 55) if pet.dead else (184, 0, 0))
                else:
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
    if profile.name == "tdisplay" and panel_mode is None and not status_visible:
        _draw_pet_cue(frame, build_dir, pet, sprite_x, sprite_y, facing, motion_state, tired, minute)
        if pet.sleep.asleep or motion_state == "sleep":
            world = frame.crop((0, profile.menu_height, profile.width, profile.height))
            channels = world.split()
            dimmed = Image.merge("RGB", tuple(channel.point([
                ((value >> shift) >> 2) * 255 // maximum for value in range(256)
            ]) for channel, shift, maximum in zip(channels, (3, 2, 3), (31, 63, 31))))
            frame.paste(dimmed, (0, profile.menu_height))
    return frame
