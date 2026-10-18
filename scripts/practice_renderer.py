"""240x135 practice UI prototype; combat rules remain in core.practice."""
from collections import namedtuple
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from config import (BACKGROUND_PATH,
                    PET_HIT_FRAME_COUNT, PET_HURT_FRAME_COUNT,
                    PET_HIT_FRAME_INTERVAL, PET_HURT_FRAME_INTERVAL,
                    PRACTICE_IMPACT_MS)
from core.techniques import TECHNIQUES, REQUIRED_STAGE, REQUIRED_TRAINING, technique_name, technique_stage
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
#   y = 33..114 combatant slots OR terminal result banner
#   y =115..134 action selector: 4 command icons + status label
HEADER_BOTTOM = 32
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
REASON_LABELS_EN = {
    "SIGUE ORDEN": "FOLLOWED ORDER",
    "A SU CRITERIO": "PET DECIDES",
    "SIN MP": "NOT ENOUGH MP",
    "EN RECARGA": "ON COOLDOWN",
    "PREFIERE DEFENDER": "CHOSE TO GUARD",
    "PREFIERE ATACAR": "CHOSE TO ATTACK",
    "RECUPERA": "RESTORES MP",
    "ELIGE ORDEN": "AWAITING ORDER",
    "ESPERANDO": "AWAITING ORDER",
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
        "rookie": ("Rookie", "firemon", {"idle": "idle", "punch": "punch", "cast": "cast", "block": "block", "walk": "walk", "hit": "hit", "hurt": "hurt", "happy": "happy", "sad": "sad"}),
        "champion": ("Champion", "flamemon", {"idle": "idle", "punch": "punch", "cast": "cast", "block": "block", "walk": "walk", "hurt": "hurt", "hit_react": "hit_react", "dodge": "dodge", "happy": "happy", "sad": "sad"}),
        "ultimate": ("Ultimate", "dragfiremon", {"idle": "idle", "punch": "punch", "cast": "cast", "block": "block", "walk": "fly", "hurt": "hurt", "happy": "happy", "sad": "sad"}),
    }
    stage, name, available = sprites.get(species, sprites["rookie"])
    requested = action if action in available else ("punch" if action in ("hit", "hurt") and "punch" in available else "idle")
    return f"/digimon1/{stage}/{name}_{available[requested]}_atlas.bmp"


def _practice_species_label(species):
    return {"egg": "EGG", "baby": "SPARKMON", "rookie": "FIREMON",
            "champion": "FLAMEMON", "ultimate": "DRAGFIRE"}.get(species, "VPET")


def _english(session):
    return session.pet.language != "ES"


def _technique_label(action, english):
    return "NO ACTION" if english and action is None else "NO ACTUO" if action is None else technique_name(action, english)


def pet_sprite(frame, build_dir, x, y, size, action, now_ms, flip=False, species="rookie", frame_interval_ms=100):
    requested = {0: "punch", 1: "cast", 2: "block", 3: "cast", 4: "cast", "walk": "walk", "eat": "eat"}.get(action, "idle")
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
    names = [technique_name(i, not es) for i in range(len(TECHNIQUES))]
    if session.page == "tech":
        text(draw, (6, 27), "EQUIPADAS" if es else "EQUIPPED", MUTED, small=True)
        equipped = sorted(progress.equipped)
        capacity = progress.capacity(session.pet.species)
        text(draw, (62, 27), '%d/%d' % (len(equipped), capacity), MUTED, small=True)
        for slot in range(capacity):
            x = 115 + slot * 30
            draw.rectangle((x, 21, x + 25, 40), fill=PANEL)
            if slot < len(equipped):
                i = equipped[slot]
                paste_icon(frame, technique_icon(TECHNIQUES[i]["id"]), x + 5, 23)
            else:
                text(draw, (x + 10, 27), '-', MUTED, small=True)
        draw.line((5, 45, 234, 45), fill=TEAL)
        i = session.index
        learned = i < len(TECHNIQUES) and progress.learned(i, session.pet.species)
        pet_sprite(frame, build_dir, 10, 40, 68, i if learned else None, now_ms,
                   species=session.pet.species, frame_interval_ms=50)
        for j in range(len(TECHNIQUES) + 1):
            x = 4 + j * 20
            draw.rectangle((x, 107, x + 17, 130), fill=TEAL if i == j else PANEL,
                           outline=YELLOW if i == j else PANEL)
            icon = technique_icon(TECHNIQUES[j]["id"]) if j < len(TECHNIQUES) else asset_icon(build_dir, "Back")
            paste_icon(frame, icon, x + 1, 111)
        if i == len(TECHNIQUES):
            text(draw, (126, 52), "VOLVER" if es else "BACK", YELLOW)
            return
        text(draw, (126, 52), names[i] if learned else "???", YELLOW)
        text(draw, (126, 67), (("EQUIPADA" if es else "EQUIPPED") if i in equipped
             else ("EN RESERVA" if es else "IN RESERVE")) if learned else ("BLOQUEADA" if es else "LOCKED"), GREEN if learned else MUTED, small=True)
        rows = [("defense" if i == 2 else "power", "DANO /2" if es and i == 2 else "DAMAGE /2" if i == 2 else ("POTENCIA " if es else "POWER ") + str(TECHNIQUES[i]["power"]), WHITE),
                ("cost", ("RECUPERA 4 MP" if es else "RESTORE 4 MP") if i == 2 else ("COSTE " if es else "COST ") + str(TECHNIQUES[i]["mp"]) + " MP", MP),
                ("mastery", ("DOMINIO " if es else "MASTERY ") + "%d/100" % progress.mastery[i], MUTED)]
        if not learned:
            stage_ok = technique_stage(session.pet.species) >= REQUIRED_STAGE[i]
            requirement = ('FLAMEMON' if REQUIRED_STAGE[i] == 2 else 'DRAGFIREMON') if not stage_ok else '%d / %d' % (progress.training, REQUIRED_TRAINING[i])
            rows = [("training", "ENTRENAR" if es else "TRAIN", MUTED), ("lock", requirement, YELLOW)]
        for row, (symbol, label, color) in enumerate(rows):
            y = 82 + row * 14
            paste_icon(frame, info_icon(symbol, 10), 126, y)
            text(draw, (140, y), label, color, small=True)
        draw.rectangle((126, 125, 232, 128), fill=PANEL)
        width = min(107, (progress.mastery[i] * 107 // 100) if learned else
                    progress.training * 107 // max(1, REQUIRED_TRAINING[i]) if stage_ok else 0)
        if width:
            draw.rectangle((126, 125, 125 + width, 128), fill=GREEN if learned else YELLOW)
        return
    i = session.tech
    tech = TECHNIQUES[i]
    paste_icon(frame, technique_icon(tech["id"]), 8, 25)
    text(draw, (32, 25), names[i], YELLOW)
    # Technique actions: punch, cast, block.
    pet_sprite(frame, build_dir, 0, 42, 68, i, now_ms,
               species=session.pet.species, frame_interval_ms=50)
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
    english = _english(session)
    if battle.round == 0:
        return FeedbackInfo(
            awaiting=True, order_label="AUTO", order_is_auto=True,
            action_label="-", reason_key="ELIGE ORDEN",
            reason_label=REASON_LABELS_EN["ELIGE ORDEN"] if english else REASON_LABELS["ELIGE ORDEN"], is_substitution=False,
            round=0, damage=(0, 0),
        )
    order_is_auto = (session.last_order == -1)
    order_label = "AUTO" if order_is_auto else _technique_label(session.last_order, english)
    action = battle.actions[0]
    action_label = _technique_label(action, english)
    reason_key = battle.reason or "ELIGE ORDEN"
    labels = REASON_LABELS_EN if english else REASON_LABELS
    reason_label = labels.get(reason_key, reason_key)
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


def _combat_lunge(elapsed):
    if elapsed < 150 or elapsed >= 950:
        return 0
    if elapsed < 400:
        return (elapsed - 150) * 18 // 250
    if elapsed < 650:
        return 18
    return 18 - (elapsed - 650) * 18 // 300


def _draw_combatant(frame, build_dir, session, now_ms, side):
    battle = session.battle
    player = side == "player"
    slot = 0 if player else 1
    own, other = battle.actions[slot], battle.actions[1 - slot]
    species = session.pet.species if player else "rookie"
    elapsed = max(0, now_ms - session.updated_at)
    lunge = _combat_lunge(elapsed) if battle.round else 0
    x = (4 + lunge) if player else (140 - lunge)
    action = "idle"
    if _impact_active(session, now_ms):
        if own is not None and own != 2:
            second_attacker = other is not None and other != 2 and _first_actor(battle) != slot
            action = "hurt" if second_attacker else ("cast" if TECHNIQUES[own]['mp'] else "hit")
        elif battle.damage[1 - slot] > 0:
            action = "hurt"
        elif own == 2:
            action = "block"
    frames = _arena_frames(str(build_dir), _species_atlas(species, action))
    sprite = frames[((elapsed if action != "idle" else now_ms) // 80) % len(frames)]
    if not player:
        sprite = sprite.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    frame.paste(sprite, (x, 38), sprite)


@lru_cache(maxsize=32)
def _arena_frames(build_dir, path):
    from scripts.battle_assets import atlas_frames
    return atlas_frames(_load_image(device_path(Path(build_dir), path)))




def _draw_combat_header(draw, frame, battle, pet):
    """Top band: title, wide HP/MP bars and right-aligned ``value/max``
    numbers. Each side occupies half the screen, split at ``SPLIT_X``."""
    draw.rectangle((0, 0, 239, HEADER_BOTTOM), fill=INK)
    draw.line((SPLIT_X, 3, SPLIT_X, 30), fill=TEAL)
    # Left column: current pet form (x=4..118), right column: practice rival.
    rival_label = "PRACTICE" if pet.language != "ES" else "PRACTICA"
    for x, name, fighter, color_hp, color_mp in (
        (4, _practice_species_label(pet.species), battle.player, HP, MP),
        (125, rival_label, battle.rival, HP, MP),
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


def _draw_result_banner(frame, draw, build_dir, session, now_ms):
    """Show the result card with the current species' available reaction."""
    draw.rectangle((0, 33, 239, 114), fill=INK)
    banner_color = {"VICTORIA": GREEN, "DERROTA": HP, "EMPATE": YELLOW}.get(
        session.battle.result, YELLOW)
    draw.rectangle((10, 36, 229, 110), fill=PANEL, outline=banner_color, width=2)
    english = _english(session)
    result_label = session.battle.result
    if english:
        result_label = {"VICTORIA": "VICTORY", "DERROTA": "DEFEAT", "EMPATE": "DRAW"}.get(
            result_label, result_label)
    text(draw, (16, 40), result_label, banner_color)
    summary = ({
        "VICTORIA": "RIVAL DEFEATED",
        "DERROTA": "YOU WERE DEFEATED",
        "EMPATE": "30 ROUND LIMIT",
    } if english else {
        "VICTORIA": "RIVAL DERROTADO",
        "DERROTA": "TE DERROTARON",
        "EMPATE": "LIMITE 30 RONDAS",
    }).get(session.battle.result, "")
    text(draw, (16, 56), summary, WHITE, small=True)
    if session.battle.round:
        text(draw, (16, 70), ("ROUNDS %d" if english else "RONDAS %d") % session.battle.round, MUTED, small=True)
    if session.message:
        text(draw, (16, 91), session.message, YELLOW, small=True)
    elif session.reward_item:
        from core.adopted_items import BY_ID, short_name
        reward = 'ITEM +1 ' + short_name(BY_ID[session.reward_item], not english)
        text(draw, (16, 84), reward, GREEN, small=True)
    action = {"VICTORIA": "happy", "DERROTA": "sad"}.get(session.battle.result)
    if action and session.pet.species in ("rookie", "champion", "ultimate"):
        _draw_atlas(frame, build_dir, _species_atlas(session.pet.species, action),
                    164, 44, 64, max(0, now_ms - session.updated_at), frame_interval_ms=100)
    else:
        pet_sprite(frame, build_dir, 164, 44, 64, None, now_ms,
                   species=session.pet.species)




def _draw_action_selector(frame, draw, build_dir, session):
    """Bottom band: 4 command icons on the left and a status block on the
    right with the command label and a coloured availability / cost hint.
    In the terminal state only the ``VOLVER`` back button is shown."""
    draw.rectangle((0, SELECTOR_TOP, 239, SELECTOR_BOTTOM), fill=INK)
    if session.battle.result:
        if not session.awarded:
            for i, choice in enumerate(session.choices()):
                x = 4 + i * 118
                draw.rectangle((x, 116, x + 112, 133), outline=YELLOW if i == session.index else MUTED)
                text(draw, (x + 5, 118), ('RETRY' if choice == 'REINTENTAR' else 'BACK') if _english(session) else choice,
                     YELLOW if i == session.index else MUTED)
            return
        icon_button(frame, draw, asset_icon(build_dir, "Back"), 4,
                    SELECTOR_TOP + 1, True, size=18)
        text(draw, (28, SELECTOR_TOP + 3), "BACK" if _english(session) else "VOLVER", YELLOW)
        return
    commands = [-1] + list(session.pet.techniques.equipped) + ['bag', None]
    compact = len(commands) > 6
    for i, command in enumerate(commands):
        icon = (asset_icon(build_dir, 'Backpack') if command == 'bag' else asset_icon(build_dir, "Back") if command is None else
                technique_icon("auto" if command == -1 else TECHNIQUES[command]["id"]))
        unavailable = command not in (None, -1, 'bag') and not session.battle.player.valid(command)
        x = 4 + i * (18 if compact else 20)
        icon_button(frame, draw, icon, x, SELECTOR_TOP, i == session.index,
                    size=16 if compact else 18, unavailable=unavailable)
    command = commands[session.index]
    english = _english(session)
    label = ('BAG' if english else 'MOCHILA') if command == 'bag' else (("RETREAT" if english else "RETIRARSE") if command is None else
             "AUTO" if command == -1 else TECHNIQUES[command]["name"])
    if english and isinstance(command, int) and command >= 0:
        label = _technique_label(command, True)
    label_x = 132 if compact else 128
    text(draw, (label_x, SELECTOR_TOP), label, YELLOW)
    text(draw, (label_x, SELECTOR_TOP + 11), _selector_status(session, command), _selector_color(command, session), small=True)


def _selector_color(command, session):
    if command is None or command in (-1, 'bag'):
        return YELLOW
    if not session.battle.player.valid(command):
        return HP
    return GREEN if command == 2 else MP


def _selector_status(session, command):
    english = _english(session)
    if command == 'bag':
        return '%d ITEMS' % len(session.combat_items())
    if command is None:
        return "END BATTLE" if english else "FIN BATALLA"
    if command == -1:
        return "PET DECIDES" if english else "PET DECIDE"
    tech = TECHNIQUES[command]
    if session.battle.player.cooldowns[command]:
        return ("COOLDOWN %d" if english else "RECARGA %d") % session.battle.player.cooldowns[command]
    if session.battle.player.mp < tech["mp"]:
        return "NOT ENOUGH MP" if english else "SIN MP"
    if command == 2:
        return "HALF DAMAGE +4MP" if english else "MITIGA 50% +4MP"
    return ("COST %d MP" if english else "COSTE %d MP") % tech["mp"]


def render_battle(frame, draw, build_dir, session, now_ms):
    battle = session.battle
    bg = _load_image(device_path(build_dir, BACKGROUND_PATH)).convert("RGB")
    frame.paste(bg.resize((240, 135), Image.Resampling.NEAREST))
    if not battle.result:
        _draw_combatant(frame, build_dir, session, now_ms, "player")
        _draw_combatant(frame, build_dir, session, now_ms, "rival")
    _draw_combat_header(draw, frame, battle, session.pet)
    if battle.result:
        _draw_result_banner(frame, draw, build_dir, session, now_ms)
    _draw_action_selector(frame, draw, build_dir, session)


def render_practice(build_dir, session, now_ms=0):
    frame = Image.new("RGB", (240, 135), INK)
    draw = ImageDraw.Draw(frame)
    renderers = {"tech": render_tech, "detail": render_detail, "battle": render_battle, 'items': render_battle_items}
    renderers[session.page](frame, draw, Path(build_dir), session, now_ms)
    return frame


def render_battle_items(frame, draw, build_dir, session, now_ms):
    from core.adopted_items import BY_ID, short_name, item_blurb
    from core.inventory import inventory_window
    from scripts.sim_renderer import _paste_ui_icon
    from scripts.exploration_renderer import fitted_text
    english = _english(session)
    header(draw, 'BATTLE ITEMS' if english else 'MOCHILA DE COMBATE', 'R%d' % session.battle.round)
    fighter = session.battle.player
    text(draw, (5, 22), 'HP %d/%d    MP %d/%d' % (fighter.hp, fighter.max_hp, fighter.mp, fighter.max_mp), MP, small=True)
    choices = session.choices()
    indexes = tuple(range(len(choices)))
    for slot, index in enumerate(inventory_window(indexes, session.index)):
        y = 37 + slot * 25
        draw.rectangle((4, y, 235, y + 22), fill=PANEL, outline=YELLOW if index == session.index else TEAL)
        key = choices[index]
        if key == 'VOLVER':
            _paste_ui_icon(frame, build_dir, 'Back', 8, y + 3, 16)
            fitted_text(draw, (31, y + 3, 218, y + 19), 'BACK' if english else 'VOLVER', FONT, WHITE)
        else:
            item = BY_ID[key]
            _paste_ui_icon(frame, build_dir, 'Adopted:' + key, 8, y + 3, 16)
            fitted_text(draw, (31, y + 1, 144, y + 12), short_name(item, not english), SMALL, WHITE)
            fitted_text(draw, (31, y + 13, 144, y + 22), item_blurb(item, not english), SMALL, MP)
            fitted_text(draw, (151, y + 3, 229, y + 19), 'x%d' % session.pet.adopted_inventory[key], FONT, YELLOW, right=True)
    message = {'ERROR AL GUARDAR': 'SAVE FAILED', 'SIN EFECTO': 'NO EFFECT', 'OBJETO USADO': 'ITEM USED'}.get(session.message, session.message) if english else session.message
    if session.message:
        text(draw, (5, 117), message, YELLOW, small=True)
