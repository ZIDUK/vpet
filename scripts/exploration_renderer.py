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


def duration_label(seconds):
    hours, remainder = divmod(max(0, int(seconds)), 3600)
    minutes, seconds = divmod(remainder, 60)
    return "%02d:%02d:%02d" % (hours, minutes, seconds)


def draw_exploration(frame, build_dir, pet, session, now, animation_ms=0):
    from scripts.sim_renderer import _status_font, _paste_ui_icon
    from scripts.practice_renderer import pet_sprite

    draw = ImageDraw.Draw(frame)
    font, small = _status_font(12), _status_font(10)
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
        text((8, 27), label(key), YELLOW)

    def buttons():
        choices = session.choices() if session else (("claim",) if not remaining else ())
        for i, choice in enumerate(choices):
            width = 232 // len(choices)
            x = 4 + i * width
            selected = session is not None and i == session.index
            draw.rectangle((x, 116, x + width - 4, 133),
                           fill=YELLOW if selected else PANEL)
            text((x + 5, 118), label(choice), INK if selected else WHITE, tiny=True)

    def reward_lines(reward):
        lines = []
        if reward["energy"]:
            lines.append(tr(pet, "explore.energy", reward["energy"]))
        if reward["ev"]:
            lines.append(tr(pet, "explore.ev", reward["ev"], tr_stat(pet, reward["stat"])))
        if reward["mastery"]:
            lines.append(tr(pet, "explore.mastery", reward["mastery"]))
        if reward["learning"]:
            lines.append(label("learned") if reward["learned"] else
                         tr(pet, "explore.learning", min(2, pet.techniques.training + (page != "receipt"))))
        if reward["guide"]:
            lines.append(label("guide"))
        return lines or [label("none")]

    if page in ("routes", "stats"):
        heading("stats" if page == "stats" else "title")
        choices = session.choices()
        start = min(max(0, session.index - 1), max(0, len(choices) - 3))
        for slot, choice in enumerate(choices[start:start + 3]):
            y = 48 + slot * 27
            selected = start + slot == session.index
            draw.rectangle((5, y, 234, y + 24), fill=PANEL)
            if selected:
                draw.rectangle((5, y, 7, y + 24), fill=YELLOW)
            if choice in DURATIONS:
                _paste_ui_icon(frame, build_dir, {"patio": "Energy", "jornada": "ItemGuide", "noche": "Pedia"}[choice], 13, y + 2, 20)
                text((40, y + 1), label(choice), YELLOW if selected else WHITE)
                text((194, y + 1), "30m" if choice == "patio" else "8h", CYAN, True)
                text((40, y + 12), label(choice + "_reward"), MUTED, True)
            else:
                text((14, y + 5), label("back") if choice == "back" else tr_stat(pet, choice),
                     YELLOW if selected else WHITE)
        if len(choices) == 1:
            text((14, 84), label("home_only"), MUTED, True)
    elif page == "confirm":
        heading("confirm")
        # Use the currently evolved pet, matching the other simulator panels.
        pet_sprite(frame, build_dir, 5, 51, 52, None, animation_ms, species=pet.species)
        text((66, 48), label(session.route), YELLOW)
        text((163, 48), "30m" if session.route == "patio" else "8h", CYAN)
        predicted = departure_reward(pet, session.route, session.stat, now)
        text((66, 64), reward_lines(predicted)[0] if predicted else label("blocked"), WHITE, True)
        good = not pet.injured and all(pet.get(s) >= GOOD_CARE_MINIMUM for s in ("h", "e", "p"))
        text((66, 80), label("good" if good else "poor"), GREEN if good else YELLOW, True)
        text((66, 96), label("free"), MUTED, True)
        if predicted and predicted["guide"]:
            _paste_ui_icon(frame, build_dir, "ItemGuide", 211, 91, 20)
        buttons()
    elif page in ("trip", "recall"):
        heading("recall_title" if page == "recall" else "away" if remaining else "ready")
        route = e.trip["route"]
        text((8, 48), label(route), WHITE)
        text((142, 48), duration_label(remaining), CYAN)
        if page == "recall":
            for i, line in enumerate(reward_lines(e.preview(pet, now))[:3]):
                text((8, 67 + i * 14), line, GREEN, True)
        elif not remaining:
            for i, line in enumerate(reward_lines(e.preview(pet, now))[:3]):
                text((8, 67 + i * 14), line, GREEN, True)
            pet_sprite(frame, build_dir, 205, 67, 28, None, animation_ms, species=pet.species)
        else:
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
            text((8, 48), label(receipt["route"]), YELLOW)
            text((142, 48), duration_label(receipt["elapsed"]), MUTED, True)
            for i, line in enumerate(reward_lines(receipt)[:3]):
                text((8, 67 + i * 14), line, GREEN, True)
            pet_sprite(frame, build_dir, 185, 62, 48, None, animation_ms, species=pet.species)
        buttons()
    if session and session.message:
        draw.rectangle((0, 90, 239, 114), fill=INK)
        text((5, 101), label(session.message), YELLOW, True)
