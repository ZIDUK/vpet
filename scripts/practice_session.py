"""Two-button controller; practice never mutates official battle counters."""
from core.dna import COMBAT_STATS
from core.practice import Fighter, PracticeBattle


class PracticeSession:
    def __init__(self, pet, save, training=False):
        self.pet, self.save = pet, save
        self.training = training
        self.page, self.index, self.tech = "tech" if training else "battle", 0, 0
        self.battle = None if training else PracticeBattle(Fighter(
            [pet.combat_stat(s) for s in COMBAT_STATS], pet.techniques.equipped,
            pet.techniques.mastery, pet.dna[3] % 3, pet.techniques.bond))
        self.message = ""
        self.updated_at = 0
        self.awarded = False
        self.last_order = None

    def choices(self):
        if self.page == "tech":
            return ["GOLPE", "LLAMA", "GUARDIA", "VOLVER"]
        if self.page == "detail":
            equipped = self.tech in self.pet.techniques.equipped
            equip = "QUITAR" if equipped else "EQUIPAR"
            return (["ENTRENAR"] if self.training else []) + [equip, "VOLVER"]
        if self.battle.result:
            return ["VOLVER"]
        from core.techniques import TECHNIQUES
        return ["A TU CRITERIO"] + [TECHNIQUES[i]["name"] for i in self.pet.techniques.equipped] + ["RETIRARSE"]

    def input(self, event, now_ms):
        if event == "next":
            self.index = (self.index + 1) % len(self.choices())
            return True
        if event == "back":
            # Leaving battle requires explicit RETIRARSE; a held NEXT cannot end it.
            if self.page == "battle":
                return True
            if self.page == "tech":
                return False
            self.page, self.index = "tech", self.tech
            self.message = ""
            return True
        if event != "action":
            return True
        if self.page == "tech":
            if self.index == 3:
                return False
            else:
                self.tech = self.index
                self.page, self.index = "detail", 0
            self.message = ""
            return True
        if self.page == "detail":
            if self.index == len(self.choices()) - 1:
                self.page, self.index = "tech", self.tech
                return True
            progress = self.pet.techniques
            learned = progress.learned(self.tech)
            if self.training and self.index == 0:
                ok = progress.train(self.pet, self.tech)
                if not ok:
                    self.message = "FALTA ENERGIA" if self.pet.get("e") < 4 else "PET NO APTO"
                elif not learned:
                    self.message = "LLAMA APRENDIDA" if progress.learned(self.tech) else "ENTRENAMIENTO 1/2"
                else:
                    self.message = "ENTRENAMIENTO COMPLETO"
            else:
                ok = progress.equip(self.tech)
                if ok:
                    self.message = "EQUIPADA" if self.tech in progress.equipped else "EN RESERVA"
                else:
                    self.message = "TECNICA BLOQUEADA" if not learned else "MINIMO UNA EQUIPADA"
            if ok and not self.save(self.pet):
                self.message = "ERROR AL GUARDAR"
            return True
        if self.battle.result or self.index == len(self.choices()) - 1:
            return False
        order = -1 if self.index == 0 else self.pet.techniques.equipped[self.index - 1]
        if self.battle.step(order):
            self.last_order = order
            self.updated_at = now_ms
            if self.battle.result and not self.awarded:
                progress = self.pet.techniques
                for i, count in enumerate(self.battle.uses):
                    progress.mastery[i] = min(100, progress.mastery[i] + count)
                progress.bond = min(100, progress.bond + 1)
                self.awarded = True
                self.message = "" if self.save(self.pet) else "ERROR AL GUARDAR"
            self.index = 0
        return True
