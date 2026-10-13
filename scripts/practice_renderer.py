"""240x135 practice UI prototype; combat rules remain in core.practice."""
from collections import namedtuple
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from config import (BACKGROUND_PATH,
                    PET_HIT_FRAME_COUNT, PET_HURT_FRAME_COUNT,
                    PET_HIT_FRAME_INTERVAL, PET_HURT_FRAME_INTERVAL,
                    PRACTICE_IMPACT_MS)
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

# Band layout (240x135):
#   y =  0..32  combat header (title + HP + MP per side, split at x=119)
#   y = 33..91  combatant slots OR terminal result banner
#   y = 92..114 feedback band: line 1 order/action + round, line 2 reason + damage
#   y =115..134 action selector: 4 command icons + status label
HEADER_BOTTOM = 32
BAND_TOP = 92
BAND_BOTTOM = 114
SELECTOR_TOP = 115
SELECTOR_BOTTOM = 134
SPLIT_X = 119

# Reason categories. The renderer paints line 2 with the color of the category
# and only uses the label dictionary for the human-readable copy.
REASON_LABELS = {
    "SIGUE ORDEN": "SIGUIO TU ORDEN",
    "A SU CRITERIO": "DECIDE EL PET",
    "SIN MP": "SIN MP",
    "EN RECARGA": "EN RECARGA",
    "PREFIERE DEFENDER": "PREFIRIO DEFENDER",
    "PREFIERE ATACAR": "PREFIRIO ATACAR",
    "RECUPERA": "RECUPERA MP",
    "ELIGE ORDEN": "ESPERANDO ORDEN",
    "ESPERANDO": "ESPERANDO ORDEN",
}
REASON_CATEGORY = {
    "SIGUE ORDEN": "ok",
    "A SU CRITERIO": "neutral",
    "SIN MP": "bad",
    "EN RECARGA": "bad",
    "PREFIERE DEFENDER": "warn",
    "PREFIERE ATACAR": "warn",
    "RECUPERA": "ok",
    "ELIGE ORDEN": "muted",
    "ESPERANDO": "muted",
}
REASON_COLORS = {
    "ok": GREEN,
    "bad": HP,
    "warn": YELLOW,
    "neutral": WHITE,
    "muted": MUTED,
}

FeedbackInfo = namedtuple("FeedbackInfo", (
    "awaiting", "order_label", "order_is_auto", "action_label",
    "reason_key", "reason_label", "is_substitution",
    "round", "damage",
))


def text(draw, xy, value, color=WHITE, small=False):
    draw.fontmode = "1"
    draw.text(xy, str(value), font=SMALL if small else FONT, fill=color)


def text_width(draw, value, small=True):
    return int(draw.textlength(str(value), font=SMALL if small else FONT))


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


def _draw_atlas(frame, build_dir, path, x, y, size, now_ms, flip=False,
                 frame_count=None, frame_interval_ms=100):
    """Render the ``now_ms``-th slice of ``path``. Frame count defaults to the
    number of cells actually packed in the atlas; ``frame_interval_ms`` is the
    duration of one frame in milliseconds. Negative ``now_ms`` clamps to the
    first cell, oversized ``now_ms`` wraps through the configured count.
    """
    atlas = _load_image(device_path(build_dir, path))
    cell = atlas.height
    actual = atlas.width // cell
    count = actual if frame_count is None else min(frame_count, actual)
    if count <= 0:
        return
    safe_ms = max(0, int(now_ms))
    interval = max(1, int(frame_interval_ms))
    index = (safe_ms // interval) % count
    sprite = atlas.crop((index * cell, 0, (index + 1) * cell, cell))
    mask = sprite.point([0] + [255] * 255, mode="L")
    sprite = sprite.convert("RGBA")
    sprite.putalpha(mask)
    sprite = sprite.resize((size, size), Image.Resampling.NEAREST)
    if flip:
        sprite = sprite.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    frame.paste(sprite, (x, y), sprite)


def _species_atlas(species, action):
    sprites = {
        "egg": ("Egg", "egg", {"idle": "idle"}),
        "baby": ("Baby", "sparkmon", {"idle": "idle", "walk": "walk", "eat": "eat"}),
        "rookie": ("Rookie", "firemon", {"idle": "idle", "punch": "punch", "cast": "cast", "block": "block", "walk": "walk", "hit": "hit", "hurt": "hurt"}),
        "champion": ("Champion", "flamemon", {"idle": "idle", "punch": "punch", "cast": "cast", "block": "cast", "walk": "walk"}),
        "ultimate": ("Ultimate", "dragfiremon", {"idle": "idle", "punch": "punch", "cast": "cast", "block": "cast", "walk": "fly"}),
    }
    stage, name, available = sprites.get(species, sprites["rookie"])
    requested = action if action in available else ("punch" if action in ("hit", "hurt") and "punch" in available else "idle")
    return f"/digimon1/{stage}/{name}_{available[requested]}_atlas.bmp"


def _practice_species_label(species):
    return {"egg": "EGG", "baby": "SPARKMON", "rookie": "FIREMON",
            "champion": "FLAMEMON", "ultimate": "DRAGFIRE"}.get(species, "VPET")


def pet_sprite(frame, build_dir, x, y, size, action, now_ms, flip=False, species="rookie", frame_interval_ms=100):
    requested = {0: "punch", 1: "cast", 2: "block", "walk": "walk", "eat": "eat"}.get(action, "idle")
    path = _species_atlas(species, requested)
    _draw_atlas(frame, build_dir, path, x, y, size, now_ms, flip,
                frame_interval_ms=frame_interval_ms)


def impact_sprite(frame, build_dir, x, y, size, kind, now_ms, flip=False, species="rookie"):
    """Render the hit (attacker) or hurt (defender) frame for PRACTICE_IMPACT_MS."""
    if kind == "hit":
        path = _species_atlas(species, "hit")
        count = PET_HIT_FRAME_COUNT
        interval_ms = int(PET_HIT_FRAME_INTERVAL * 1000)
    else:
        path = _species_atlas(species, "hurt")
        count = PET_HURT_FRAME_COUNT
        interval_ms = int(PET_HURT_FRAME_INTERVAL * 1000)
    _draw_atlas(frame, build_dir, path, x, y, size, now_ms, flip,
                frame_count=count, frame_interval_ms=interval_ms)


def render_technique_panel(frame, draw, build_dir, session, now_ms):
    from scripts.training_renderer import _metric
    progress = session.pet.techniques
    es = session.pet.language == "ES"
    draw.rectangle((0, 0, 239, 134), fill=INK)
    draw.rectangle((0, 0, 239, 19), fill=TEAL)
    paste_icon(frame, asset_icon(build_dir, "Training"), 4, 2)
    text(draw, (26, 4), "TECNICAS" if es else "TECHNIQUES")
    names = ("GOLPE", "LLAMA", "GUARDIA") if es else ("PUNCH", "FLAME", "GUARD")
    if session.page == "tech":
        text(draw, (6, 27), "EQUIPADAS" if es else "EQUIPPED", MUTED, small=True)
        equipped = sorted(progress.equipped)
        for slot in range(2):
            x = 83 + slot * 77
            draw.rectangle((x, 21, x + 73, 40), fill=PANEL)
            if slot < len(equipped):
                i = equipped[slot]
                paste_icon(frame, technique_icon(TECHNIQUES[i]["id"]), x + 2, 23)
                text(draw, (x + 22, 27), names[i], small=True)
            else:
                text(draw, (x + 14, 27), "VACIO" if es else "EMPTY", MUTED, small=True)
        draw.line((5, 45, 234, 45), fill=TEAL)
        i = session.index
        learned = i < 3 and progress.learned(i)
        pet_sprite(frame, build_dir, 10, 40, 68, i if learned else None, now_ms,
                   species=session.pet.species)
        for j in range(4):
            x = 4 + j * 28
            draw.rectangle((x, 107, x + 23, 130), fill=TEAL if i == j else PANEL,
                           outline=YELLOW if i == j else PANEL)
            icon = technique_icon(TECHNIQUES[j]["id"]) if j < 3 else asset_icon(build_dir, "Back")
            paste_icon(frame, icon, x + 4, 111)
        if i == 3:
            text(draw, (126, 52), "VOLVER" if es else "BACK", YELLOW)
            return
        text(draw, (126, 52), names[i] if learned else "???", YELLOW)
        text(draw, (126, 67), (("EQUIPADA" if es else "EQUIPPED") if i in equipped
             else ("EN RESERVA" if es else "IN RESERVE")) if learned else ("BLOQUEADA" if es else "LOCKED"), GREEN if learned else MUTED, small=True)
        rows = [("defense" if i == 2 else "power", "DANO /2" if es and i == 2 else "DAMAGE /2" if i == 2 else ("POTENCIA " if es else "POWER ") + str(TECHNIQUES[i]["power"]), WHITE),
                ("cost", ("RECUPERA 4 MP" if es else "RESTORE 4 MP") if i == 2 else ("COSTE " if es else "COST ") + str(TECHNIQUES[i]["mp"]) + " MP", MP),
                ("mastery", ("DOMINIO " if es else "MASTERY ") + "%d/100" % progress.mastery[i], MUTED)]
        if not learned:
            rows = [("training", "ENTRENAR" if es else "TRAIN", MUTED), ("lock", "%d / 2" % progress.training, YELLOW)]
        for row, (symbol, label, color) in enumerate(rows):
            y = 82 + row * 14
            paste_icon(frame, info_icon(symbol, 10), 126, y)
            text(draw, (140, y), label, color, small=True)
        draw.rectangle((126, 125, 232, 128), fill=PANEL)
        width = min(107, (progress.mastery[i] * 107 // 100) if learned else progress.training * 107 // 2)
        if width:
            draw.rectangle((126, 125, 125 + width, 128), fill=GREEN if learned else YELLOW)
        return
    i = session.tech
    tech = TECHNIQUES[i]
    paste_icon(frame, technique_icon(tech["id"]), 8, 25)
    text(draw, (32, 25), names[i], YELLOW)
    # Technique actions: punch, cast, block.
    pet_sprite(frame, build_dir, 0, 42, 68, i, now_ms,
               species=session.pet.species)
    _metric(draw, 43, "POTENCIA" if es else "POWER", "DANO /2" if i == 2 else str(tech["power"]), YELLOW)
    _metric(draw, 57, "USAR" if es else "USE", "+4 MP" if i == 2 else "%d MP" % tech["mp"], MP)
    _metric(draw, 71, "DOMINIO" if es else "MASTERY", "%d/100" % progress.mastery[i], GREEN)
    _metric(draw, 85, "ENTRENAR" if es else "TRAIN", "-4 ENE", HP)
    if session.message:
        text(draw, (6, 101), session.message, YELLOW, small=True)
    commands = ["ENTRENAR" if es else "TRAIN",
                ("QUITAR" if es else "REMOVE") if i in progress.equipped else ("EQUIPAR" if es else "EQUIP"),
                "VOLVER" if es else "BACK"]
    if not session.training:
        commands = commands[1:]
    for j, command in enumerate(commands):
        draw.rectangle((4 + j * 78, 116, 79 + j * 78, 133), outline=YELLOW if session.index == j else PANEL)
        text(draw, (8 + j * 78, 120), command, YELLOW if session.index == j else MUTED, small=True)


def render_tech(frame, draw, build_dir, session, now_ms):
    return render_technique_panel(frame, draw, build_dir, session, now_ms)


def render_detail(frame, draw, build_dir, session, now_ms):
    return render_technique_panel(frame, draw, build_dir, session, now_ms)


def battle_feedback(session):
    """Return a :class:`FeedbackInfo` describing the player's order, the pet's
    executed action, the real reason returned by ``choose()`` and the round
    damage. The renderer paints two explicit lines from this struct so the
    player can see at a glance what they asked, what the pet did, and why."""
    battle = session.battle
    if battle.round == 0:
        return FeedbackInfo(
            awaiting=True, order_label="AUTO", order_is_auto=True,
            action_label="-", reason_key="ELIGE ORDEN",
            reason_label=REASON_LABELS["ELIGE ORDEN"], is_substitution=False,
            round=0, damage=(0, 0),
        )
    order_is_auto = (session.last_order == -1)
    order_label = "AUTO" if order_is_auto else TECHNIQUES[session.last_order]["name"]
    action = battle.actions[0]
    action_label = TECHNIQUES[action]["name"] if action is not None else "NO ACTUO"
    reason_key = battle.reason or "ELIGE ORDEN"
    reason_label = REASON_LABELS.get(reason_key, reason_key)
    is_substitution = (not order_is_auto and action is not None
                        and action != session.last_order and not battle.result)
    return FeedbackInfo(
        awaiting=False, order_label=order_label, order_is_auto=order_is_auto,
        action_label=action_label, reason_key=reason_key, reason_label=reason_label,
        is_substitution=is_substitution, round=battle.round, damage=battle.damage,
    )


def _impact_active(session, now_ms):
    return 0 <= now_ms - session.updated_at < PRACTICE_IMPACT_MS and session.battle.round > 0


def _first_actor(battle):
    """Mirror PracticeBattle.step: whoever acts first this round by speed."""
    speed_diff = battle.player.stats[4] - battle.rival.stats[4]
    return 0 if speed_diff > 0 or (speed_diff == 0 and battle.round % 2 == 1) else 1


def _draw_combatant(frame, build_dir, session, now_ms, side):
    """Render the Firemon or rival at its slot, picking hit / hurt / guard /
    idle based on the actual outcome of the round (damage taken, action
    performed, who acted first). Rules:

    - **hit** on the attacker that landed damage (``own_action != 2``).
      In a simultaneous trade (both attack and both take damage), the first
      actor (by speed) keeps the hit sprite while the second actor (who took
      the first hit before retaliating) is shown the hurt sprite so the
      player can read who struck first. In a one-sided attack, the lone
      attacker always shows hit.
    - **hurt** on the defender that absorbed damage, either by guarding with
      reduced damage (``own_action == 2`` and ``damage_taken > 0``) or by
      being KOed before acting (``own_action is None`` and
      ``damage_taken > 0``).
    - **guard** sprite when the combatant guarded without taking damage.
    - **idle** when no action happened or the round is not in the impact
      window (banner already shown on top of the sprite when the battle has
      terminated).
    """
    battle = session.battle
    is_player = (side == "player")
    own_action = battle.actions[0] if is_player else battle.actions[1]
    other_action = battle.actions[1] if is_player else battle.actions[0]
    damage_taken = battle.damage[1] if is_player else battle.damage[0]
    x = 24 if is_player else 154
    flip = not is_player
    impact = _impact_active(session, now_ms)
    if not impact:
        pet_sprite(frame, build_dir, x, 33, 60, None, now_ms, flip,
                   session.pet.species if is_player else "rookie")
        return
    first = _first_actor(battle)
    is_first_actor = (is_player and first == 0) or (not is_player and first == 1)
    both_attackers = (own_action is not None and own_action != 2
                       and other_action is not None and other_action != 2)
    if own_action is not None and own_action != 2:
        # Attacker. In a trade, the first actor shows hit and the second
        # shows hurt; otherwise the attacker simply shows hit.
        if both_attackers and not is_first_actor:
            kind = "hurt"
        else:
            kind = "hit"
        impact_sprite(frame, build_dir, x, 33, 60, kind,
                      now_ms - session.updated_at, flip,
                      session.pet.species if is_player else "rookie")
        return
    if damage_taken > 0:
        impact_sprite(frame, build_dir, x, 33, 60, "hurt",
                      now_ms - session.updated_at, flip,
                      session.pet.species if is_player else "rookie")
        return
    if own_action == 2:
        pet_sprite(frame, build_dir, x, 33, 60, 2, now_ms, flip,
                   session.pet.species if is_player else "rookie")
        return
    pet_sprite(frame, build_dir, x, 33, 60, None, now_ms, flip,
               session.pet.species if is_player else "rookie")


def _order_icon(session, size=10):
    """Return the technique / auto icon for the player's requested order at
    the requested render size. Falls back to the auto glyph when the order
    is unknown so the band never shows a missing sprite."""
    if session.last_order == -1:
        base = technique_icon("auto")
    elif session.last_order is not None and 0 <= session.last_order < len(TECHNIQUES):
        base = technique_icon(TECHNIQUES[session.last_order]["id"])
    else:
        base = technique_icon("auto")
    return base.resize((size, size), Image.Resampling.NEAREST) if size != 16 else base


def _action_icon(action, size=10):
    if action is None or not (0 <= action < len(TECHNIQUES)):
        return technique_icon("auto").resize((size, size), Image.Resampling.NEAREST)
    base = technique_icon(TECHNIQUES[action]["id"])
    return base.resize((size, size), Image.Resampling.NEAREST) if size != 16 else base


def _draw_combat_header(draw, frame, battle, pet):
    """Top band: title, wide HP/MP bars and right-aligned ``value/max``
    numbers. Each side occupies half the screen, split at ``SPLIT_X``."""
    draw.rectangle((0, 0, 239, HEADER_BOTTOM), fill=INK)
    draw.line((SPLIT_X, 3, SPLIT_X, 30), fill=TEAL)
    # Left column: current pet form (x=4..118), right column: PRACTICA.
    for x, name, fighter, color_hp, color_mp in (
        (4, _practice_species_label(pet.species), battle.player, HP, MP),
        (125, "PRACTICA", battle.rival, HP, MP),
    ):
        text(draw, (x, 0), name)
        _draw_resource_row(frame, draw, x, 11, "hp", "HP",
                            fighter.hp, fighter.max_hp, color_hp)
        _draw_resource_row(frame, draw, x, 22, "mp", "MP",
                            fighter.mp, fighter.max_mp, color_mp)


def _draw_resource_row(frame, draw, x, y, icon_name, label, value, maximum, color):
    """Render ``[icon] LABEL [bar....] value/max`` at row ``y``. The bar is
    46 px wide and 6 px tall to be readable on a 240x135 panel without
    colliding with neighbouring rows. The numbers are right-anchored at
    ``x + 80`` so three-digit maxima like ``238/238`` still fit in either
    column without crossing the vertical split at ``SPLIT_X = 119``."""
    paste_icon(frame, info_icon(icon_name, 10), x, y - 2)
    text(draw, (x + 12, y - 1), label, color, small=True)
    bar(draw, x + 32, y + 2, 46, value, maximum, color, height=6)
    text(draw, (x + 80, y - 1), "%d/%d" % (value, maximum), small=True)


def _draw_result_banner(draw, session):
    """Victory / defeat / draw banner over the combatant area. The big
    result text is painted in its result color; the outline matches."""
    draw.rectangle((0, 33, 239, 91), fill=INK)
    banner_color = {"VICTORIA": GREEN, "DERROTA": HP, "EMPATE": YELLOW}.get(
        session.battle.result, YELLOW)
    draw.rectangle((10, 36, 229, 88), fill=PANEL, outline=banner_color, width=2)
    text(draw, (16, 40), session.battle.result, banner_color)
    summary = {
        "VICTORIA": "RIVAL DERROTADO",
        "DERROTA": "TE DERROTARON",
        "EMPATE": "LIMITE 30 RONDAS",
    }.get(session.battle.result, "")
    text(draw, (16, 56), summary, WHITE, small=True)
    if session.battle.round:
        text(draw, (16, 70), "RONDAS %d" % session.battle.round, MUTED, small=True)
    if session.message:
        text(draw, (16, 80), session.message, YELLOW, small=True)


def _draw_feedback_band(frame, draw, session, info):
    """Two explicit lines that show the cycle the player asked for and the
    reason the pet did (or did not) follow it. Line 1 paints ``HIZO`` in
    red when the pet substituted the order and green when it obeyed. Line
    2 paints the reason in a category color (green ok, red bad, yellow
    warn, white neutral, muted while waiting). Round number and damage
    are anchored to the right edge of the band."""
    draw.rectangle((0, BAND_TOP, 239, BAND_BOTTOM), fill=INK)
    # Line 1: [icon] PEDISTE <order>  ->  HIZO <action>          R#X
    paste_icon(frame, _order_icon(session, 10), 4, BAND_TOP + 1)
    pediste = "PEDISTE %s" % info.order_label
    text(draw, (18, BAND_TOP + 1), pediste, WHITE, small=True)
    arrow = "  >  "
    arrow_x = 18 + text_width(draw, pediste, small=True)
    text(draw, (arrow_x, BAND_TOP + 1), arrow, MUTED, small=True)
    hizo = "HIZO %s" % info.action_label
    hizo_x = arrow_x + text_width(draw, arrow, small=True)
    action_color = HP if info.is_substitution else GREEN
    text(draw, (hizo_x, BAND_TOP + 1), hizo, action_color, small=True)
    if info.round:
        round_label = "R%d" % info.round
        text(draw, (238 - text_width(draw, round_label, small=True), BAND_TOP + 1),
             round_label, MUTED, small=True)
    # Line 2: MOTIVO: <reason>                      PRACT -X | FIRE -Y
    reason_color = REASON_COLORS[REASON_CATEGORY.get(info.reason_key, "muted")]
    reason_text = "MOTIVO: %s" % info.reason_label
    text(draw, (4, BAND_TOP + 13), reason_text, reason_color, small=True)
    if not info.awaiting and (info.damage[0] or info.damage[1]):
        # damage[i] is the amount fighter i inflicts on the opponent:
        # damage[0] = damage Firemon dealt to Practica (PRACT's HP loss).
        # damage[1] = damage Practica dealt to Firemon (FIRE's HP loss).
        damage_text = "PRACT -%d | FIRE -%d" % (info.damage[0], info.damage[1])
        text(draw, (238 - text_width(draw, damage_text, small=True), BAND_TOP + 13),
             damage_text, HP, small=True)


def _draw_action_selector(frame, draw, build_dir, session):
    """Bottom band: 4 command icons on the left and a status block on the
    right with the command label and a coloured availability / cost hint.
    In the terminal state only the ``VOLVER`` back button is shown."""
    draw.rectangle((0, SELECTOR_TOP, 239, SELECTOR_BOTTOM), fill=INK)
    if session.battle.result:
        icon_button(frame, draw, asset_icon(build_dir, "Back"), 4,
                    SELECTOR_TOP + 1, True, size=18)
        text(draw, (28, SELECTOR_TOP + 3), "VOLVER", YELLOW)
        return
    commands = [-1] + list(session.pet.techniques.equipped) + [None]
    for i, command in enumerate(commands):
        icon = (asset_icon(build_dir, "Back") if command is None else
                technique_icon("auto" if command == -1 else TECHNIQUES[command]["id"]))
        unavailable = command not in (None, -1) and not session.battle.player.valid(command)
        x = 4 + i * 26
        icon_button(frame, draw, icon, x, SELECTOR_TOP, i == session.index,
                    size=20, unavailable=unavailable)
    command = commands[session.index]
    label = ("RETIRARSE" if command is None else
             "AUTO" if command == -1 else TECHNIQUES[command]["name"])
    text(draw, (114, SELECTOR_TOP), label, YELLOW)
    text(draw, (114, SELECTOR_TOP + 11), _selector_status(session, command), _selector_color(command, session), small=True)


def _selector_color(command, session):
    if command is None or command == -1:
        return YELLOW
    if not session.battle.player.valid(command):
        return HP
    return GREEN if command == 2 else MP


def _selector_status(session, command):
    if command is None:
        return "FIN BATALLA"
    if command == -1:
        return "PET DECIDE"
    tech = TECHNIQUES[command]
    if session.battle.player.cooldowns[command]:
        return "RECARGA %d" % session.battle.player.cooldowns[command]
    if session.battle.player.mp < tech["mp"]:
        return "SIN MP"
    if command == 2:
        return "RECUPERA 4 MP"
    return "COSTE %d MP" % tech["mp"]


def render_battle(frame, draw, build_dir, session, now_ms):
    battle = session.battle
    bg = _load_image(device_path(build_dir, BACKGROUND_PATH)).convert("RGB")
    frame.paste(bg.resize((240, 135), Image.Resampling.NEAREST))
    info = battle_feedback(session)
    if not battle.result:
        _draw_combatant(frame, build_dir, session, now_ms, "player")
        _draw_combatant(frame, build_dir, session, now_ms, "rival")
    _draw_combat_header(draw, frame, battle, session.pet)
    if battle.result:
        _draw_result_banner(draw, session)
    _draw_feedback_band(frame, draw, session, info)
    _draw_action_selector(frame, draw, build_dir, session)


def render_practice(build_dir, session, now_ms=0):
    frame = Image.new("RGB", (240, 135), INK)
    draw = ImageDraw.Draw(frame)
    renderers = {"tech": render_tech, "detail": render_detail, "battle": render_battle}
    renderers[session.page](frame, draw, Path(build_dir), session, now_ms)
    return frame
