"""Compact 240x135 expedition screens using the shared pixel assets and catalog."""
from PIL import ImageDraw
from core.exploration import DURATIONS, GOOD_CARE_MINIMUM, departure_reward, week_id
from core.i18n import tr, tr_stat

INK = (16, 22, 26)
PANEL = (32, 47, 51)
WHITE = (234, 238, 219)
MUTED = (156, 178, 179)
GREEN = (102, 204, 160)
YELLOW = (255, 217, 61)
CYAN = (77, 190, 217)
PINK = (241, 93, 112)
SELECTED = (40, 74, 75)
STAT_ICONS = {'hp': 'hp', 'mp': 'mp', 'off': 'attack', 'def': 'defense',
              'spd': 'speed', 'brn': 'mind'}


def fitted_text(draw, box, value, font, color, right=False):
    """Place visible glyph bounds inside an exclusive rectangle, not the baseline."""
    value = str(value)
    x0, y0, x1, y1 = box
    bounds = font.getbbox(value)
    if bounds[3] - bounds[1] > y1 - y0:
        raise ValueError('Text row is shorter than its font')
    if bounds[2] - bounds[0] > x1 - x0:
        while value and font.getlength(value + '...') > x1 - x0:
            value = value[:-1]
        value += '...'
        bounds = font.getbbox(value)
    width, height = bounds[2] - bounds[0], bounds[3] - bounds[1]
    x = x1 - width if right else x0
    y = y0 + (y1 - y0 - height) // 2
    draw.text((x - bounds[0], y - bounds[1]), value, fill=color, font=font)
    return x, y, x + width, y + height


def duration_label(seconds):
    hours, remainder = divmod(max(0, int(seconds)), 3600)
    minutes, seconds = divmod(remainder, 60)
    return "%02d:%02d:%02d" % (hours, minutes, seconds)


def draw_exploration(frame, build_dir, pet, session, now, animation_ms=0):
    from scripts.sim_renderer import _status_font, _paste_ui_icon
    from scripts.practice_renderer import pet_sprite
    from scripts.practice_icons import info_icon

    draw = ImageDraw.Draw(frame)
    font, small = _status_font(12), _status_font(10)
    spanish = pet.language == 'ES'
    draw.rectangle((0, 24, 239, 134), fill=INK)
    page = session.page if session else "trip"
    e = pet.exploration
    now = now if now is not None else (e.trip["started"] if e.trip else 0)
    remaining = e.remaining(now)

    def text(xy, value, color=WHITE, tiny=False):
        draw.text(xy, value, fill=color, font=small if tiny else font)

    def label(key):
        return tr(pet, "explore." + key)

    def heading(key):
        draw.rectangle((0, 24, 239, 43), fill=PANEL)
        fitted_text(draw, (8, 25, 232, 42), label(key), font, YELLOW)

    def icon(name, x, y, size=16):
        sprite = info_icon(name, size)
        frame.paste(sprite, (x, y), sprite)

    def buttons():
        choices = session.choices() if session else (("claim",) if not remaining else ())
        for i, choice in enumerate(choices):
            width = 232 // len(choices)
            x = 4 + i * width
            selected = session is not None and i == session.index
            outlined = page == 'confirm'
            draw.rectangle((x, 116, x + width - 4, 133),
                           fill=INK if outlined else YELLOW if selected else PANEL,
                           outline=(YELLOW if selected else MUTED) if outlined else None)
            fitted_text(draw, (x + 5, 117, x + width - 6, 133), label(choice),
                        small, (YELLOW if selected else MUTED) if outlined else INK if selected else WHITE)

    def table_row(y, name, caption, value, color=GREEN, asset=False, height=11):
        draw.rectangle((70, y, 237, y + height - 1), fill=INK, outline=PANEL)
        draw.line((160, y, 160, y + height - 1), fill=PANEL)
        icon_y = y + (height - 10) // 2
        if asset:
            _paste_ui_icon(frame, build_dir, name, 73, icon_y, 10)
        else:
            icon(name, 73, icon_y, 10)
        fitted_text(draw, (86, y + 1, 156, y + height - 1), caption, small, color)
        fitted_text(draw, (166, y + 1, 234, y + height - 1), value, small, WHITE)

    def reward_value(reward):
        if reward['route'] == 'patio':
            return '+%d ENE' % reward['energy']
        if reward['route'] == 'jornada':
            return '+%d EV' % reward['ev']
        if reward['learning']:
            return ('APRENDIDA' if spanish else 'LEARNED') if reward['learned'] else '1/2'
        return '+%d DOM' % reward['mastery']

    def attribute_row(y, route, stat, height=11):
        if route == 'jornada':
            table_row(y, STAT_ICONS.get(stat, 'training'), 'ATRIBUTO' if spanish else 'STAT',
                      tr_stat(pet, stat) if stat in STAT_ICONS else '--', height=height)
        elif route == 'patio':
            table_row(y, 'energy', 'RECURSO' if spanish else 'RESOURCE', 'ENE', CYAN, height=height)
        else:
            table_row(y, 'mastery', 'TECNICA' if spanish else 'TECHNIQUE',
                      'LLAMA' if spanish else 'FLAME', YELLOW, height=height)

    def object_row(y, reward, height=11):
        has_guide = bool(reward and reward['guide'])
        table_row(y, 'ItemGuide' if has_guide else 'training', 'OBJETO' if spanish else 'ITEM',
                  ('GUIA' if spanish else 'GUIDE') if has_guide else '--',
                  YELLOW if has_guide else MUTED, asset=has_guide, height=height)

    def return_table(reward, saved=False):
        pet_sprite(frame, build_dir, 5, 55, 56, None, animation_ms, species=pet.species)
        fitted_text(draw, (70, 46, 233, 59), label(reward['route']), font, YELLOW)
        table_row(60, 'Clock', 'TIEMPO' if spanish else 'TIME', duration_label(reward['elapsed']),
                  CYAN, asset=True)
        attribute_row(71, reward['route'], reward['stat'])
        table_row(82, 'training', 'PREMIO' if spanish else 'REWARD', reward_value(reward), GREEN)
        object_row(93, reward)
        status = ('YA GUARDADO' if spanish else 'ALREADY SAVED') if saved else (
            'POR RECLAMAR' if spanish else 'TO CLAIM')
        fitted_text(draw, (70, 104, 233, 114), status, small, GREEN if saved else YELLOW)

    if page in ("routes", "stats"):
        heading("stats" if page == "stats" else "title")
        choices = session.choices()
        start = min(max(0, session.index - 1), max(0, len(choices) - 3))
        for slot, choice in enumerate(choices[start:start + 3]):
            y = 46 + slot * 29
            selected = start + slot == session.index
            draw.rectangle((5, y, 234, y + 26), fill=SELECTED if selected else PANEL)
            if selected:
                draw.rectangle((5, y, 7, y + 26), fill=YELLOW)
            if choice in DURATIONS:
                _paste_ui_icon(frame, build_dir, {"patio": "Energy", "jornada": "ItemGuide", "noche": "Pedia"}[choice], 12, y + 4, 20)
                fitted_text(draw, (39, y + 1, 188, y + 14), label(choice), font,
                            YELLOW if selected else WHITE)
                fitted_text(draw, (194, y + 1, 229, y + 14),
                            "30m" if choice == "patio" else "8h", small, CYAN, right=True)
                fitted_text(draw, (39, y + 16, 230, y + 26),
                            label(choice + "_reward"), small, MUTED)
            else:
                if choice == 'back':
                    _paste_ui_icon(frame, build_dir, 'Back', 13, y + 5, 16)
                else:
                    icon(STAT_ICONS[choice], 13, y + 5)
                fitted_text(draw, (39, y + 4, 228, y + 23),
                            label("back") if choice == "back" else tr_stat(pet, choice),
                            font, YELLOW if selected else WHITE)
        if len(choices) == 1:
            text((14, 84), label("home_only"), MUTED, True)
    elif page == "confirm":
        heading("confirm")
        pet_sprite(frame, build_dir, 5, 55, 48, None, animation_ms, species=pet.species)
        fitted_text(draw, (70, 46, 190, 59), label(session.route), font, YELLOW)
        fitted_text(draw, (194, 46, 233, 59),
                    "30m" if session.route == "patio" else "8h", small, CYAN, right=True)
        predicted = departure_reward(pet, session.route, session.stat, now)
        attribute_row(60, session.route, session.stat, height=14)
        table_row(73, 'training', 'PREMIO' if spanish else 'REWARD',
                  reward_value(predicted) if predicted else '--', GREEN, height=14)
        object_row(86, predicted, height=14)
        table_row(99, 'energy', 'COSTE' if spanish else 'COST', '0 ENE', PINK, height=14)
        good = not pet.injured and all(pet.get(s) >= GOOD_CARE_MINIMUM for s in ("h", "e", "p"))
        care = ('BIEN' if spanish else 'GOOD') if good else ('ATENDER' if spanish else 'NEEDS CARE')
        fitted_text(draw, (4, 105, 65, 115), care,
                    small, GREEN if good else YELLOW)
        buttons()
    elif page in ("trip", "recall"):
        heading("recall_title" if page == "recall" else "away" if remaining else "ready")
        route = e.trip["route"]
        if page == "recall" or not remaining:
            return_table(e.preview(pet, now))
        else:
            text((8, 48), label(route), WHITE)
            text((142, 48), duration_label(remaining), CYAN)
            draw.line((18, 84, 220, 84), fill=MUTED, width=2)
            progress = 1 - remaining / DURATIONS[route]
            x = 18 + int(202 * progress)
            draw.line((18, 84, x, 84), fill=GREEN, width=2)
            for px in (18, 119, 220):
                draw.rectangle((px - 2, 82, px + 2, 86), fill=WHITE)
            pet_sprite(frame, build_dir, min(210, max(4, x - 14)), 56, 28,
                       "walk" if remaining else None, animation_ms, species=pet.species,
                       frame_interval_ms=70)
            week_ev = e.week_ev if week_id(now) <= e.week else 0
            week_mastery = e.week_mastery if week_id(now) <= e.week else 0
            text((8, 96), tr(pet, "explore.week", week_ev, week_mastery), MUTED, True)
        buttons()
    else:
        heading("receipt")
        receipt = e.receipt
        if receipt:
            return_table(receipt, saved=True)
        buttons()
    if session and session.message:
        draw.rectangle((0, 90, 239, 114), fill=INK)
        text((5, 101), label(session.message), YELLOW, True)
