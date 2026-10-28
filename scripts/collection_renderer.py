"""Sprite-first collection screens; drawing never changes individuals or saves."""
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

from core.profile import PetProfile
from scripts.content_loader import definition_for
from scripts.sim_renderer import _paste_ui_icon

BACKGROUND, SURFACE, SELECTED = (15, 21, 25), (30, 41, 47), (43, 54, 60)
LINE, INK, MUTED = (61, 78, 85), (239, 246, 245), (151, 172, 181)
GOLD, MINT, CYAN = (255, 210, 77), (113, 225, 179), (106, 207, 234)
FONT, SMALL, TITLE = (ImageFont.load_default(size=size) for size in (10, 9, 12))


@lru_cache(maxsize=20)
def _sprite(build_dir, role):
    definition = definition_for(build_dir)
    clip = definition.clip(role, "idle", "training")
    path = definition.stage(role)["portrait"] if role == "egg" else clip["atlas"]
    with Image.open(build_dir / path.lstrip("/")) as original:
        image = original.copy() if role == "egg" else original.crop((0, 0, original.height, original.height))
        rgba = image.convert("RGBA")
        if image.mode == "P":
            rgba.putalpha(image.point([0] + [255] * 255, mode="L"))
    return rgba if role == "egg" else rgba.resize((clip["canvas"], clip["canvas"]), Image.Resampling.NEAREST)


class _View:
    def __init__(self, build_dir, session):
        self.build, self.session, self.collection = Path(build_dir), session, session.collection
        self.es = getattr(session.pet, "language", "EN") == "ES"
        self.frame = Image.new("RGB", (240, 135), BACKGROUND)
        self.draw = ImageDraw.Draw(self.frame)

    def text(self, x, y, value, color=INK, font=FONT, anchor=None):
        self.draw.text((x, y), value, fill=color, font=font, anchor=anchor)

    def header(self, title):
        self.draw.rectangle((0, 0, 239, 20), fill=SURFACE)
        self.text(7, 3, title, font=TITLE)
        count = len(self.collection.slots) if self.collection is not None else 1
        count_label = ("4 PLAZAS" if self.es else "4 SLOTS") if self.session.page == "enable" else "%d/4" % count
        self.text(232, 5, count_label, GOLD, anchor="ra")

    def portrait(self, role, x, y, size, flip=False, muted=False):
        image = _sprite(self.build, role).resize((size, size), Image.Resampling.NEAREST)
        if flip:
            image = ImageOps.mirror(image)
        if muted:
            image = image.copy()
            image.putalpha(image.getchannel("A").point(lambda alpha: alpha // 3))
        self.frame.paste(image, (x, y), image)

    def icon(self, name, x, y, size=16):
        if name == "Egg":
            self.portrait("egg", x, y, size)
            return
        _paste_ui_icon(self.frame, self.build, name, x, y, size)

    def slot(self, index):
        return self.collection.slots[index] if self.collection is not None and index < len(self.collection.slots) else None

    def name(self, index):
        slot = self.slot(index)
        if slot is None:
            return "---"
        role = slot["pet"]["species"]
        return ("HUEVO" if self.es else "EGG") if role == "egg" else definition_for(self.build).stage(role)["name"]

    def pet(self, index, x, y, size, flip=False, muted=False):
        slot = self.slot(index)
        if slot:
            self.portrait(slot["pet"]["species"], x, y, size, flip, muted)
        else:
            if size < 30:
                self.text(x + size // 2, y + size // 2 - 5, "+", MUTED, SMALL, "ma")
                return
            self.draw.rectangle((x + 8, y + 5, x + size - 9, y + size - 6), outline=LINE)
            self.text(x + size // 2, y + size // 2 - 5, "?", MUTED, anchor="ma")

    def button(self, x, width, index, icon, label="", y=113):
        selected = self.session.index == index
        self.draw.rectangle((x, y, x + width - 1, 133), fill=SELECTED if selected else SURFACE,
                            outline=GOLD if selected else LINE)
        self.icon(icon, x + 4, y + 3, 14)
        if label:
            self.text(x + 22, y + 4, label, GOLD if selected else INK, SMALL)

    def confirmation(self, label):
        self.button(6, 108, 0, "Back", "CANCELAR" if self.es else "CANCEL")
        self.button(125, 109, 1, "Save", label)

    def grid(self):
        self.header("COLECCION" if self.es else "COLLECTION")
        for i in range(4):
            x, y = 6 + (i % 2) * 117, 24 + (i // 2) * 42
            chosen = self.session.index == i
            self.draw.rectangle((x, y, x + 110, y + 39), fill=SELECTED if chosen else SURFACE,
                                outline=GOLD if chosen else LINE)
            slot = self.slot(i)
            if slot:
                self.pet(i, x + 2, y + 2, 36)
                self.text(x + 40, y + 5, self.name(i), font=SMALL)
                profile = PetProfile.decode(slot["pet"]["profile"])
                self.text(x + 40, y + 22, "?" if slot["pet"]["species"] == "egg" else profile.sex, CYAN, SMALL)
                if i == self.collection.active:
                    self.text(x + 55, y + 22, "ACTIVA" if self.es else "ACTIVE", MINT, SMALL)
            else:
                self.text(x + 14, y + 7, "+", MUTED, TITLE)
                self.text(x + 40, y + 13, "LIBRE" if self.es else "EMPTY", MUTED, SMALL)
        self.button(6, 80, 4, "Egg", "HUEVO" if self.es else "EGG")
        self.button(93, 96, 5, "Heart", "CRUZAR" if self.es else "BREED")
        self.button(198, 36, 6, "Back")

    def detail(self):
        index, slot = self.session.target, self.slot(self.session.target)
        self.header(self.name(index))
        self.pet(index, 8, 27, 76)
        profile = PetProfile.decode(slot["pet"]["profile"])
        self.text(95, 30, "?" if slot["pet"]["species"] == "egg" else profile.sex, CYAN, TITLE)
        active = index == self.collection.active
        self.text(115, 32, ("ACTIVA" if self.es else "ACTIVE") if active else
                  ("RESERVA" if self.es else "RESERVE"), MINT if active else MUTED)
        cooldown = max(0, slot["cooldown_until"] - self.collection.clock_ms)
        remaining = max(0, 1800000 - slot["incubation_ms"]) if slot.get("birth") and slot["pet"]["species"] == "egg" else cooldown
        self.icon("Clock" if remaining else "Heart", 94, 57)
        duration = "%dh" % ((remaining + 3599999) // 3600000) if remaining >= 3600000 else "%dm" % ((remaining + 59999) // 60000)
        self.text(116, 60, duration if remaining else
                  ("SIN ESPERA" if self.es else "NO WAIT"), MUTED)
        icons = ("Load", "Heart", "Brain", "Back")
        labels = (("ACTIVA" if active else "ACTIVAR", "CRUZAR", "PREFERENCIAS", "VOLVER") if self.es else
                  ("ACTIVE" if active else "SELECT", "BREED", "PREFERENCES", "BACK"))
        self.icon(icons[self.session.index % 4], 94, 82)
        self.text(116, 85, labels[self.session.index % 4], CYAN, SMALL)
        self.button(6, 80, 0, "Load", ("ACTIVA" if self.es else "ACTIVE") if active else ("ACTIVAR" if self.es else "SELECT"))
        self.button(93, 44, 1, "Heart")
        self.button(144, 44, 2, "Brain")
        self.button(198, 36, 3, "Back")

    def parents(self, confirm=False):
        first, second = self.session.parent_a, self.session.index
        if confirm:
            first, second = self.session.pair or (None, None)
        elif first is None:
            first, second = (second if second < 4 else None), None
        elif second == first or second not in self.session.candidates():
            second = None
        title = ("CONFIRMAR CRUCE" if self.es else "CONFIRM BREED") if confirm else (
            ("ELIGE PAREJA" if self.es else "CHOOSE PARTNER") if self.session.parent_a is not None else
            ("ELIGE PRIMER VPET" if self.es else "CHOOSE FIRST VPET"))
        self.header(title)
        for index, x, flip in ((first, 13, False), (second, 163, True)):
            self.pet(index if index is not None else 4, x, 26, 64, flip)
            if index is not None:
                self.text(x + 32, 94, self.name(index), font=SMALL, anchor="ma")
        self.icon("Heart", 112, 40)
        self.draw.line((88, 70, 103, 70), fill=LINE)
        self.draw.line((137, 70, 152, 70), fill=LINE)
        if confirm:
            self.portrait("egg", 106, 66, 28)
            self.text(120, 95, "30m", CYAN, SMALL, "ma")
            self.confirmation("CRUZAR" if self.es else "BREED")
        else:
            candidates = self.session.candidates()
            for i in range(4):
                x = 8 + i * 32
                self.draw.rectangle((x, 110, x + 26, 134), outline=GOLD if self.session.index == i else
                                    MINT if self.session.parent_a == i else LINE)
                self.pet(i, x + 2, 111, 22, muted=i not in candidates and i != self.session.parent_a)
            self.button(198, 36, 4, "Back")
            if not candidates:
                self.text(120, 96, "SIN PAREJA APTA" if self.es else "NO ELIGIBLE PAIR", MUTED, SMALL, "ma")

    def preferences(self):
        self.header("PREFERENCIAS" if self.es else "PREFERENCES")
        self.pet(self.session.target, 6, 30, 64)
        pet = self.collection.pet_at(self.session.target)
        groups = (("Training", ("ATAQUE", "DEFENSA", "VELOCIDAD", "VIDA", "MP", "MENTE") if self.es else
                   ("ATTACK", "DEFENSE", "SPEED", "HP", "MP", "BRAIN")),
                  ("Battle", ("GOLPE", "LLAMA", "GUARDIA", "RAFAGA", "INFERNO") if self.es else
                   ("STRIKE", "FLAME", "GUARD", "BURST", "INFERNO")),
                  ("Explore", ("PATIO", "JORNADA", "NOCHE") if self.es else ("YARD", "JOURNEY", "NIGHT")))
        for domain, (icon, labels) in enumerate(groups):
            self.icon(icon, 80, 29 + domain * 25)
            policy = pet._learning
            known = policy is not None and any(policy.estimate(domain, 0, i).count or
                                               policy.estimate(domain, 0, i).bias for i in range(len(labels)))
            label = labels[policy.choose(domain, 0, (1 << len(labels)) - 1, 0)] if known else "---"
            self.text(104, 33 + domain * 25, label, CYAN if known else MUTED)
        self.button(198, 36, 0, "Back")

    def dialog(self):
        page = self.session.page
        self.header({"enable": "TU COLECCION" if self.es else "YOUR COLLECTION",
                     "founder": "NUEVO HUEVO" if self.es else "NEW EGG",
                     "activate": "CAMBIAR VPET" if self.es else "SWITCH VPET"}[page])
        if page == "enable":
            self.portrait(self.session.pet.species, 8, 26, 76)
            self.text(94, 34, "TU VPET" if self.es else "YOUR VPET", MINT)
            self.icon("Backpack", 94, 58)
            self.text(116, 61, "MISMA MOCHILA" if self.es else "SAME BACKPACK", MUTED, SMALL)
            self.text(94, 86, "PARTIDA CONSERVADA" if self.es else "PROGRESS KEPT", font=SMALL)
            self.confirmation("ACTIVAR" if self.es else "ENABLE")
        elif page == "founder":
            self.portrait("egg", 82, 23, 76)
            self.text(8, 82, "1 PLAZA" if self.es else "1 SLOT", MUTED, SMALL)
            self.text(232, 82, "SIN OBJETOS" if self.es else "NO ITEMS", MUTED, SMALL, "ra")
            self.confirmation("CREAR" if self.es else "CREATE")
        else:
            self.pet(self.session.target, 80, 24, 76)
            self.text(120, 98, self.name(self.session.target), MINT, SMALL, "ma")
            self.confirmation("ACTIVAR" if self.es else "SELECT")


def render_collection(build_dir, session):
    view = _View(build_dir, session)
    if session.page == "list":
        view.grid()
    elif session.page == "detail":
        view.detail()
    elif session.page in ("pairs", "breed"):
        view.parents(session.page == "breed")
    elif session.page == "preferences":
        view.preferences()
    else:
        view.dialog()
    if session.message:
        view.draw.rectangle((0, 91, 239, 108), fill=BACKGROUND)
        message = session.message if view.es else {
            "SIN PAREJA APTA": "NO ELIGIBLE PAIR", "COLECCION LLENA": "COLLECTION FULL",
            "ERROR AL GUARDAR": "SAVE ERROR", "OPERACION NO APLICADA": "NOT APPLIED"
        }.get(session.message, session.message)
        view.text(120, 94, message, GOLD, SMALL, "ma")
    return view.frame
