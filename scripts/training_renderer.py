"""Training carousel reached from the dumbbell icon, at native 240x135."""
from pathlib import Path

from PIL import Image, ImageDraw

from core.training import TRAINING_TYPES, TRAINING_ENERGY_COST, training_values, training_block_reason
from scripts.practice_icons import info_icon
from scripts.practice_renderer import (INK, MUTED, YELLOW, GREEN, TEAL,
                                      asset_icon, bar, icon_button, info_label, paste_icon,
                                      pet_sprite, render_practice, text)
from scripts.training_session import TRAINING_ANIMATION_MS


def render_training(build_dir, session, now_ms=0):
    build_dir = Path(build_dir)
    if session.techniques is not None:
        return render_practice(build_dir, session.techniques, now_ms)
    frame = Image.new("RGB", (240, 135), INK)
    draw = ImageDraw.Draw(frame)
    draw.rectangle((0, 0, 239, 20), fill=TEAL)
    paste_icon(frame, asset_icon(build_dir, "Training"), 4, 2)
    text(draw, (26, 5), "ENTRENAMIENTO")
    text(draw, (210, 5), "%d/8" % (session.index + 1), MUTED, small=True)
    active = session.busy(now_ms)
    item = TRAINING_TYPES[session.index] if session.index < len(TRAINING_TYPES) else None
    animation = item["animation"] if item and active else None
    pet_sprite(frame, build_dir, 4, 23, 78, animation,
               now_ms - session.updated_at if active else now_ms)
    if item:
        info_label(frame, draw, item["icon"], 88, 26, item["name"], YELLOW, small=False)
        before, after = session.gain or training_values(session.pet, session.index)
        text(draw, (88, 43), "%d > %d" % (before, after), GREEN, small=False)
        info_label(frame, draw, "mastery", 88, 58, "MEJORA +%d" % (after - before))
        info_label(frame, draw, "energy", 88, 73, "COSTE %d ENERGIA" % TRAINING_ENERGY_COST, MUTED)
    elif session.index == len(TRAINING_TYPES):
        text(draw, (88, 27), "TECNICAS", YELLOW)
        info_label(frame, draw, "training", 88, 46, "APRENDIZAJE")
        info_label(frame, draw, "mastery", 88, 62, "DOMINIO", GREEN)
    else:
        text(draw, (88, 27), "VOLVER", YELLOW)
    info_label(frame, draw, "energy", 88, 88, "ENERGIA %d/100" % session.pet.get("e"), MUTED)
    message = session.message or (training_block_reason(session.pet, session.index) if item else "")
    if message:
        # Feedback has its own band; sprite and labels finish before this row.
        draw.rectangle((0, 99, 239, 110), fill=INK)
        text(draw, (6, 99), message, YELLOW, small=True)
    if active:
        bar(draw, 0, 111, 240, now_ms - session.updated_at, TRAINING_ANIMATION_MS, GREEN, height=2)
    icons = [info_icon(t["icon"]) for t in TRAINING_TYPES]
    icons += [asset_icon(build_dir, "Pedia"), asset_icon(build_dir, "Back")]
    for i, icon in enumerate(icons):
        icon_button(frame, draw, icon, 4 + i * 29, 115, i == session.index, size=20)
    return frame
