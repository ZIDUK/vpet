"""Approved next-evolution sheet, matching EvolutionUi's production raster."""
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from config import EVOLUTION_REGISTRY
from core.evolution import EVOLUTION_PORTRAITS
from core.evolution_progress import evolution_progress
from core.content import ROLES
from scripts.content_loader import definition_for

INK, WHITE, MUTED = (19, 23, 27), (242, 244, 238), (162, 181, 182)
YELLOW, GREEN, LINE = (255, 220, 70), (111, 208, 164), (40, 74, 75)
LABELS = {
    "time": ("TIME LEFT", "TIEMPO"), "mistakes": ("CARE ERRORS", "ERRORES"),
    "battles": ("BATTLES", "COMBATES"), "wins": ("WIN RATE", "VICTORIAS"),
    "hunger": ("FOOD", "COMIDA"), "energy": ("ENERGY", "ENERGIA"),
    "mood": ("MOOD", "ANIMO"), "health": ("HEALTH", "SALUD"), "weight": ("WEIGHT", "PESO"),
}
MESSAGES = {"reached": ("STAGE REACHED", "ETAPA SUPERADA"),
            "hidden": ("UNDISCOVERED", "POR DESCUBRIR"), "final": ("FINAL STAGE", "ETAPA FINAL"),
            "egg": ("HATCHING", "ECLOSIONANDO"), "unavailable": ("UNAVAILABLE", "NO DISPONIBLE")}


@lru_cache(maxsize=2)
def font(small=False):
    return ImageFont.load_default(size=9 if small else 10)


def row_value(row, spanish):
    current, target = row["current"], row["target"]
    if row["kind"] == "time":
        if row["met"]:
            return "CUMPLIDO" if spanish else "MET"
        if row["remaining"] < 60:
            return "<1m"
        minutes = (row["remaining"] + 59) // 60
        return "%dm" % minutes if minutes < 60 else "%dh%02dm" % divmod(minutes, 60)
    if row["kind"] == "mistakes":
        return "%d / <=%d" % (current, target)
    if row["kind"] == "weight":
        return "%d / %d-%d" % (current, target, row["upper"])
    if row["kind"] == "wins":
        return "%s / %d%%" % (current if row["upper"] else "--", target)
    return "%d / %d" % (current, target)


def draw_evolution_progress(frame, build_dir, pet, detail_index=0, scale=1):
    from scripts.sim_renderer import _load_image
    es = getattr(pet, "language", "EN") == "ES"
    info = evolution_progress(pet, EVOLUTION_REGISTRY, detail_index % 5, scale)
    definition = definition_for(build_dir)
    page = detail_index // 5 % info["pages"]
    draw = ImageDraw.Draw(frame)
    draw.fontmode = "1"

    def rect(x, y, w, h, color):
        draw.rectangle((x, y, x + w - 1, y + h - 1), fill=color)

    def width(value, small=False):
        return int(font(small).getlength(value, mode="1"))

    def text(x, y, value, color=WHITE, small=False):
        draw.text((x, y), value, font=font(small), fill=color)

    def centered(x, y, value, color=WHITE, small=False):
        text(x - width(value, small) // 2, y, value, color, small)

    rect(0, 24, 240, 111, INK)
    title = ("PROXIMA EVOLUCION" if es else "NEXT EVOLUTION") if info["state"] == "progress" else ("EVOLUCION" if es else "EVOLUTION")
    centered(120, 29, title)
    rect(5, 44, 230, 1, LINE)
    portrait = _load_image(Path(build_dir) / definition.stage(ROLES[info["stage"]])["portrait"].lstrip("/"))
    if info["state"] == "hidden":
        portrait = portrait.resize((36, 36), Image.Resampling.NEAREST)
        mask = portrait.point([0] + [255] * 255, mode="L")
        frame.paste(Image.new("RGB", (36, 36), MUTED), (18, 64), mask)
    else:
        # Match AssetStore's integer sampling, not Pillow's pixel-center mapping.
        scaled = Image.new("P", (64, 64))
        scaled.putpalette(portrait.getpalette())
        scaled.putdata([portrait.getpixel((x * portrait.width // 64, y * portrait.height // 64))
                        for y in range(64) for x in range(64)])
        portrait = scaled
        mask = portrait.point([0] + [255] * 255, mode="L")
        frame.paste(portrait.convert("RGB"), (4, 50), mask)
    name = "HUEVO" if es and info["stage"] == 0 else "???" if info["state"] == "hidden" else definition.name(ROLES[info["stage"]])
    centered(36, 119, name, small=True)
    if info["state"] != "progress":
        centered(155, 77, MESSAGES[info["state"]][es], YELLOW)
        return
    for slot, row in enumerate(info["rows"][page * 4:page * 4 + 4]):
        y = 50 + slot * 18
        value = row_value(row, es)
        if row["met"]:
            for i in range(3):
                rect(75 + i, y + 6 + i, 2, 1, GREEN)
            for i in range(6):
                rect(78 + i, y + 8 - i, 2, 1, GREEN)
        else:
            rect(76, y + 3, 7, 7, YELLOW)
            rect(77, y + 4, 5, 5, INK)
        text(88, y, LABELS[row["kind"]][es], MUTED)
        text(235 - width(value), y, value, WHITE)
        rect(88, y + 13, 147, 2, LINE)
        percent = 100 if row["met"] else 0
        if not row["met"] and row["kind"] not in ("mistakes", "weight") and row["target"]:
            percent = min(100, row["current"] * 100 // row["target"])
        if percent:
            rect(88, y + 13, 147 * percent // 100, 2, GREEN if row["met"] else YELLOW)
    centered(161, 124, "%s %d/%d" % ("REQUISITOS" if es else "REQUIREMENTS", page + 1, info["pages"]), MUTED, True)
