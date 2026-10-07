"""240x135 practice UI prototype; combat rules remain in core.practice."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from config import (BACKGROUND_PATH, PET_IDLE_IMAGE_PATH, PET_PUNCH_IMAGE_PATH,
                    PET_CAST_IMAGE_PATH, PET_BLOCK_IMAGE_PATH, PET_WALK_IMAGE_PATH)
from core.techniques import TECHNIQUES
from scripts.practice_icons import technique_icon, muted_icon, info_icon
from scripts.sim_renderer import _load_image, device_path

INK = (19, 23, 27)
WHITE = (242, 244, 238)
YELLOW = (255, 220, 70)
MUTED = (162, 181, 182)
PANEL = (36, 48, 52)
TEAL = (40, 74, 75)
HP = (241, 93, 112)
MP = (71, 191, 230)
GREEN = (111, 208, 164)
FONT = ImageFont.load_default(size=10)
SMALL = ImageFont.load_default(size=9)


def text(draw, xy, value, color=WHITE, small=False):
    draw.fontmode = "1"
    draw.text(xy, str(value), font=SMALL if small else FONT, fill=color)


def bar(draw, x, y, width, value, maximum, color, height=4):
    draw.rectangle((x, y, x + width - 1, y + height - 1), fill=PANEL)
    filled = min(width, max(0, width * value // max(1, maximum)))
    if filled:
        draw.rectangle((x, y, x + filled - 1, y + height - 1), fill=color)


def header(draw, title, context):
    draw.rectangle((0, 0, 239, 17), fill=TEAL)
    text(draw, (6, 3), title)
    text(draw, (238 - draw.textlength(context, font=SMALL), 4), context, MUTED, small=True)


def asset_icon(build_dir, name):
    return _load_image(build_dir / "UIIcons" / (name + ".bmp")).convert("RGBA").resize(
        (16, 16), Image.Resampling.NEAREST)


def paste_icon(frame, icon, x, y):
    frame.paste(icon, (x, y), icon)


def info_label(frame, draw, name, x, y, value, color=WHITE, small=True):
    paste_icon(frame, info_icon(name, 10), x, y + 1)
    text(draw, (x + 14, y), value, color, small=small)


def icon_button(frame, draw, icon, x, y, selected, size=24, unavailable=False):
    draw.rectangle((x, y, x + size - 1, y + size - 1), fill=TEAL if selected else PANEL,
                   outline=YELLOW if selected else PANEL, width=2)
    paste_icon(frame, muted_icon(icon) if unavailable else icon, x + (size - 16) // 2, y + (size - 16) // 2)


def pet_sprite(frame, build_dir, x, y, size, action, now_ms, flip=False):
    path = {0: PET_PUNCH_IMAGE_PATH, 1: PET_CAST_IMAGE_PATH, 2: PET_BLOCK_IMAGE_PATH,
            "walk": PET_WALK_IMAGE_PATH}.get(action, PET_IDLE_IMAGE_PATH)
    atlas = _load_image(device_path(build_dir, path))
    cell = atlas.height
    index = (now_ms // 100) % (atlas.width // cell)
    sprite = atlas.crop((index * cell, 0, (index + 1) * cell, cell))
    mask = sprite.point([0] + [255] * 255, mode="L")
    sprite = sprite.convert("RGBA")
    sprite.putalpha(mask)
    sprite = sprite.resize((size, size), Image.Resampling.NEAREST)
    if flip:
        sprite = sprite.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    frame.paste(sprite, (x, y), sprite)


def render_tech(frame, draw, build_dir, session, now_ms):
    header(draw, "TECNICAS", "ENTRENAMIENTO" if session.training else "FIREMON")
    progress = session.pet.techniques
    text(draw, (6, 26), "EQUIPADAS", MUTED, small=True)
    for slot in range(2):
        x = 83 + slot * 77
        draw.rectangle((x, 21, x + 73, 40), fill=PANEL)
        if slot < len(progress.equipped):
            tech = TECHNIQUES[progress.equipped[slot]]
            paste_icon(frame, technique_icon(tech["id"]), x + 2, 23)
            text(draw, (x + 22, 26), tech["name"], small=True)
        else:
            text(draw, (x + 14, 26), "VACIO", MUTED, small=True)
    draw.line((5, 45, 234, 45), fill=TEAL)
    selected = session.index
    learned = selected < 3 and progress.learned(selected)
    pet_sprite(frame, build_dir, 18, 47, 60, selected if learned else None, now_ms)
    for i in range(4):
        icon = (technique_icon(TECHNIQUES[i]["id"], not progress.learned(i)) if i < 3
                else asset_icon(build_dir, "Back"))
        icon_button(frame, draw, icon, 4 + i * 28, 107, i == selected)
    if selected == 3:
        text(draw, (126, 52), "VOLVER", YELLOW)
        return
    tech = TECHNIQUES[selected]
    text(draw, (126, 52), tech["name"] if learned else "???", YELLOW)
    if not learned:
        info_label(frame, draw, "lock", 126, 67, "BLOQUEADA", MUTED)
        info_label(frame, draw, "training", 126, 86, "ENTRENAMIENTOS")
        text(draw, (126, 101), "%d / 2" % progress.training, YELLOW)
        bar(draw, 126, 120, 107, progress.training, 2, YELLOW)
    else:
        text(draw, (126, 67), "EQUIPADA" if selected in progress.equipped else "EN RESERVA", GREEN, small=True)
        info_label(frame, draw, "defense" if selected == 2 else "power", 126, 81,
                   "DANO / 2" if selected == 2 else "POTENCIA %d" % tech["power"])
        info_label(frame, draw, "cost", 126, 94, "RECUPERA 4 MP" if selected == 2 else "COSTE %d MP" % tech["mp"], MP)
        info_label(frame, draw, "mastery", 126, 109, "DOMINIO %d/100" % progress.mastery[selected], MUTED)
        bar(draw, 126, 125, 107, progress.mastery[selected], 100, GREEN)


def render_detail(frame, draw, build_dir, session, now_ms):
    progress = session.pet.techniques
    learned = progress.learned(session.tech)
    tech = TECHNIQUES[session.tech]
    header(draw, "TECNICAS", tech["name"] if learned else "POR DESCUBRIR")
    pet_sprite(frame, build_dir, 2, 20, 64, session.tech if learned else None, now_ms)
    paste_icon(frame, technique_icon(tech["id"], not learned), 59, 23)
    if learned:
        text(draw, (86, 23), "EQUIPADA" if session.tech in progress.equipped else "EN RESERVA", GREEN)
        info_label(frame, draw, "defense" if session.tech == 2 else "power", 86, 39,
                   "DANO / 2" if session.tech == 2 else "POTENCIA %d" % tech["power"])
        info_label(frame, draw, "cost", 182, 39, "+4 MP" if session.tech == 2 else "%d MP" % tech["mp"], MP)
        info_label(frame, draw, "range", 86, 53, "ALCANCE " + ("CORTO" if tech["range"] == 1 else "AMPLIO"), MUTED)
        info_label(frame, draw, "mastery", 86, 66, "DOMINIO %d/100" % progress.mastery[session.tech])
        bar(draw, 86, 80, 146, progress.mastery[session.tech], 100, GREEN)
    else:
        info_label(frame, draw, "lock", 86, 24, "BLOQUEADA", YELLOW)
        info_label(frame, draw, "training", 86, 44, "ENTRENAMIENTOS %d/2" % progress.training)
        bar(draw, 86, 65, 146, progress.training, 2, YELLOW)
    if session.training:
        info_label(frame, draw, "energy", 6, 89, "ENERGIA %d / COSTE 4" % session.pet.get("e"), MUTED)
    else:
        info_label(frame, draw, "training", 6, 89, "ENTRENAMIENTO: PESA", MUTED)
    if session.message:
        text(draw, (6, 101), session.message, YELLOW, small=True)
    icons = ("Training", "Pedia", "Back") if session.training else ("Pedia", "Back")
    for i, name in enumerate(icons):
        icon_button(frame, draw, asset_icon(build_dir, name), 4 + i * 28, 114, i == session.index, size=20,
                    unavailable=name == "Pedia" and not learned)
    text(draw, (94, 118), session.choices()[session.index], YELLOW)


def battle_feedback(session):
    battle = session.battle
    if battle.round == 0:
        return "ESPERANDO ORDEN", "PRACTICA / RONDA 1"
    order = "AUTO" if session.last_order == -1 else TECHNIQUES[session.last_order]["name"]
    action = battle.actions[0]
    used = TECHNIQUES[action]["name"] if action is not None else "NO ACTUO"
    reasons = {"SIGUE ORDEN": "SIGUIO TU ORDEN", "A SU CRITERIO": "DECISION DEL PET",
               "PREFIERE DEFENDER": "PREFIRIO DEFENDER", "PREFIERE ATACAR": "PREFIRIO ATACAR",
               "RECUPERA": "RECUPERA MP"}
    return "PEDIDO %s / USO %s" % (order, used), battle.result or reasons.get(battle.reason, battle.reason)


def render_battle(frame, draw, build_dir, session, now_ms):
    battle = session.battle
    bg = _load_image(device_path(build_dir, BACKGROUND_PATH)).convert("RGB")
    frame.paste(bg.resize((240, 135), Image.Resampling.NEAREST))
    active = 0 <= now_ms - session.updated_at < 1500 and battle.round > 0
    animation_ms = now_ms - session.updated_at if active else now_ms
    pet_sprite(frame, build_dir, 24, 33, 60, battle.actions[0] if active else None, animation_ms)
    pet_sprite(frame, build_dir, 154, 33, 60, battle.actions[1] if active else None, animation_ms, True)
    draw.rectangle((0, 0, 239, 33), fill=INK)
    draw.line((119, 3, 119, 30), fill=TEAL)
    for x, name, fighter in ((4, "FIREMON", battle.player), (125, "RIVAL", battle.rival)):
        text(draw, (x, 0), name)
        for y, label, value, maximum, color in ((16, "HP", fighter.hp, fighter.max_hp, HP),
                                               (28, "MP", fighter.mp, fighter.max_mp, MP)):
            paste_icon(frame, info_icon(label.lower(), 10), x, y - 5)
            text(draw, (x + 12, y - 5), label, color, small=True)
            bar(draw, x + 29, y, 32, value, maximum, color)
            text(draw, (x + 65, y - 5), "%d/%d" % (value, maximum), small=True)
    draw.rectangle((0, 92, 239, 134), fill=INK)
    requested, reason = battle_feedback(session)
    text(draw, (4, 92), requested, small=True)
    text(draw, (4, 103), session.message or reason, YELLOW, small=True)
    if battle.round:
        text(draw, (212, 103), "R%d" % battle.round, MUTED, small=True)
    if battle.result:
        icon_button(frame, draw, asset_icon(build_dir, "Back"), 4, 115, True, size=20)
        text(draw, (34, 119), "VOLVER", YELLOW)
        return
    commands = [-1] + session.pet.techniques.equipped + [None]
    for i, command in enumerate(commands):
        icon = (asset_icon(build_dir, "Back") if command is None else
                technique_icon("auto" if command == -1 else TECHNIQUES[command]["id"]))
        unavailable = command not in (None, -1) and not battle.player.valid(command)
        x = 4 + i * 26
        icon_button(frame, draw, icon, x, 115, i == session.index, size=20, unavailable=unavailable)
        if unavailable:
            draw.rectangle((x + 14, 115, x + 19, 120), fill=HP)
    command = commands[session.index]
    label = "RETIRARSE" if command is None else "AUTO" if command == -1 else TECHNIQUES[command]["name"]
    text(draw, (112, 114), label, YELLOW)
    if command not in (None, -1):
        tech = TECHNIQUES[command]
        status = "RECARGA %d" % battle.player.cooldowns[command] if battle.player.cooldowns[command] else (
            "SIN MP" if battle.player.mp < tech["mp"] else "+4 MP" if command == 2 else "%d MP" % tech["mp"])
        text(draw, (112, 125), status, MUTED, small=True)
    elif command == -1:
        text(draw, (112, 125), "A SU CRITERIO", MUTED, small=True)


def render_practice(build_dir, session, now_ms=0):
    frame = Image.new("RGB", (240, 135), INK)
    draw = ImageDraw.Draw(frame)
    renderers = {"tech": render_tech, "detail": render_detail, "battle": render_battle}
    renderers[session.page](frame, draw, Path(build_dir), session, now_ms)
    return frame
