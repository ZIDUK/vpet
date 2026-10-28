"""Explicit, cancellable two-button collection commands, independent of drawing."""
from core.profile import PetProfile


class CollectionSession:
    def __init__(self, pet, services):
        self.pet, self.services = pet, services
        self.page = "list" if services.collection is not None else "enable"
        self.index = 0
        self.target = 0
        self.message = ""
        self.parent_a = None
        self.pair = None

    @property
    def collection(self):
        return self.services.collection

    def choices(self):
        if self.page == "enable":
            return ("VOLVER", "ACTIVAR COLECCION")
        if self.page == "founder":
            return ("CANCELAR", "CREAR HUEVO")
        if self.page == "detail":
            return ("ACTIVA" if self.target == self.collection.active else "ACTIVAR", "PADRE", "PREFERENCIAS", "VOLVER")
        if self.page == "activate":
            return ("CANCELAR", "CAMBIAR MASCOTA")
        if self.page == "preferences":
            return ("VOLVER",)
        if self.page == "pairs":
            return tuple(str(i + 1) for i in range(4)) + ("VOLVER",)
        if self.page == "breed":
            return ("CANCELAR", "CONFIRMAR CRUCE")
        rows = []
        for i in range(4):
            if i >= len(self.collection.slots):
                rows.append("LIBRE")
                continue
            slot = self.collection.slots[i]
            profile = PetProfile.decode(slot["pet"]["profile"])
            form = slot["pet"]["species"]
            from core.pet import STAGE_FRIENDLY
            name = STAGE_FRIENDLY.get(form, form).upper()
            sex = "?" if form == "egg" else profile.sex
            rows.append("%d %s %s%s" % (i + 1, name, sex, " *" if i == self.collection.active else ""))
        return tuple(rows) + ("NUEVO HUEVO", "REPRODUCIR", "VOLVER")

    def candidates(self):
        pairs = self.pairs()
        if self.parent_a is None:
            return sorted({i for pair in pairs for i in pair})
        return sorted(b if a == self.parent_a else a for a, b in pairs
                      if self.parent_a in (a, b))

    def choose_parents(self, first=None):
        self.page, self.parent_a, self.index = "pairs", first, 0
        candidates = self.candidates()
        self.index = candidates[0] if candidates else 4
        self.message = "" if candidates else "SIN PAREJA APTA"

    def pairs(self):
        from core.breeding import check_pair
        return [(a, b) for a in range(len(self.collection.slots))
                for b in range(a + 1, len(self.collection.slots))
                if check_pair(self.collection.parent(a), self.collection.parent(b))]

    def input(self, command):
        self.index = min(self.index, len(self.choices()) - 1)
        if command == "next":
            allowed = self.candidates() + [4] if self.page == "pairs" else list(range(len(self.choices())))
            for _ in range(len(self.choices())):
                self.index = (self.index + 1) % len(self.choices())
                if self.index in allowed:
                    break
            self.message = ""
            return True
        if command == "back":
            if self.page in ("list", "enable"):
                return False
            if self.page == "pairs" and self.parent_a is not None:
                self.choose_parents()
                return True
            self.page, self.index, self.message = "list", 0, ""
            return True
        if command != "action":
            return True
        index, page = self.index, self.page
        if page == "enable":
            if index == 0:
                return False
            if not self.services.enable_collection(self.pet, confirmed=True):
                self.message = "ERROR AL GUARDAR"
                return True
            self.page, self.index = "list", 0
        elif page == "list":
            count = len(self.collection.slots)
            if index < count:
                self.target, self.page, self.index = index, "detail", 0
            elif index < 4 or index == 4:
                if count == 4:
                    self.message = "COLECCION LLENA"
                else:
                    self.page, self.index = "founder", 0
            elif index == 5:
                self.choose_parents()
            else:
                return False
        elif page == "detail":
            if index == 0 and self.target != self.collection.active:
                self.page, self.index = "activate", 0
            elif index == 2:
                self.page, self.index = "preferences", 0
            elif index == 1:
                self.choose_parents(self.target)
            else:
                self.page, self.index = "list", self.target
        elif page == "preferences":
            self.page, self.index = "detail", 2
        elif page == "pairs":
            if index == 4:
                self.page, self.index = "list", 0
            elif index in self.candidates() and self.parent_a is None:
                self.parent_a = index
            elif index in self.candidates():
                self.pair = (self.parent_a, index)
                self.page, self.index = "breed", 0
        else:
            if index == 0:
                self.page, self.index = "list", 0
                return True
            if page == "founder":
                ok = self.services.add_founder(self.pet, confirmed=True)
            elif page == "activate":
                ok = self.services.switch_individual(self.pet, self.target, confirmed=True)
            else:
                ok = self.services.breed_individuals(self.pet, *self.pair, confirmed=True)
            if ok:
                self.page, self.index, self.message = "list", 0, ""
            else:
                self.message = "OPERACION NO APLICADA"
        return True
