"""Two-button Arena controller with durable, once-only result progress."""
from core.dna import COMBAT_STATS
from core.practice import Fighter, PracticeBattle
from core.adopted_items import ITEMS, COMBAT_CATEGORIES, award_victory_item
from core.techniques import TECHNIQUES, REQUIRED_TRAINING
import copy


class PracticeSession:
    def __init__(self, pet, save, training=False):
        self.pet, self.save = pet, save
        pet.techniques.mastery += [0] * max(0, len(TECHNIQUES) - len(pet.techniques.mastery))
        self.training = training
        self.page, self.index, self.tech = "tech" if training else "battle", 0, 0
        self.battle = None if training else PracticeBattle(Fighter(
            [pet.effective_combat_stat(s) for s in COMBAT_STATS], pet.techniques.equipped,
            pet.techniques.mastery, pet.dna[3] % 3, pet.techniques.bond,
            element="fire" if pet.species in ("rookie", "champion", "ultimate") else "neutral"))
        if self.battle is not None:
            self.battle.rival.element = "fire"  # The practice rival is Firemon.
        self.message = ""
        self.updated_at = 0
        self.awarded = False
        self.last_order = None
        self.next_round_at = None
        self.reward_item = None

    @property
    def busy(self):
        return (not self.training and self.page in ('battle', 'items')
                and (self.battle.result is None or not self.awarded))

    def combat_items(self):
        return [i['id'] for i in ITEMS if i['category'] in COMBAT_CATEGORIES
                and self.pet.adopted_inventory.get(i['id'], 0)]

    def _award_result(self):
        if self.awarded:
            return True
        snapshot = copy.deepcopy(self.pet.__dict__)
        if self.battle.result in ('VICTORIA', 'DERROTA'):
            self.pet.battles_this_form = min(2147483647, self.pet.battles_this_form + 1)
            counter = 'battles_won' if self.battle.result == 'VICTORIA' else 'battles_lost'
            if getattr(self.pet, counter) < 255:
                setattr(self.pet, counter, getattr(self.pet, counter) + 1)
        progress = self.pet.techniques
        for i, count in enumerate(self.battle.uses):
            progress.mastery[i] = min(100, progress.mastery[i] + count)
        progress.bond = min(100, progress.bond + 1)
        reward = award_victory_item(self.pet) if self.battle.result == 'VICTORIA' else None
        if not self.save(self.pet):
            self.pet.__dict__.clear()
            self.pet.__dict__.update(snapshot)
            self.message = 'ERROR AL GUARDAR'
            return False
        self.awarded, self.reward_item = True, reward
        self.message = ''
        return True

    def _round(self, order, now_ms):
        if self.pet.exploration.away:
            self.message = "DE EXPLORACION"
            return
        if not self.battle.step(order):
            return
        self.last_order = order
        self.updated_at = now_ms
        self.next_round_at = now_ms + 1450
        if self.battle.result and not self.awarded:
            self.page, self.index = 'battle', 0
            self._award_result()

    def tick(self, now_ms):
        if self.training or self.page not in ('battle', 'items') or self.battle.result is not None:
            return
        if self.next_round_at is None:
            self.next_round_at = now_ms + 500
            return
        if now_ms < self.next_round_at:
            return
        retreat = len(self.choices()) - 1
        order = -1 if self.page == 'items' or self.index in (0, retreat, retreat - 1) else self.pet.techniques.equipped[self.index - 1]
        self._round(order, now_ms)

    def choices(self):
        if self.page == 'items':
            return self.combat_items() + ['VOLVER']
        if self.page == "tech":
            return [t['name'] for t in TECHNIQUES] + ["VOLVER"]
        if self.page == "detail":
            equipped = self.tech in self.pet.techniques.equipped
            equip = "QUITAR" if equipped else "EQUIPAR"
            return (["ENTRENAR"] if self.training else []) + [equip, "VOLVER"]
        if self.battle.result:
            return ['VOLVER'] if self.awarded else ['REINTENTAR', 'VOLVER']
        return ["AUTO"] + [TECHNIQUES[i]["name"] for i in self.pet.techniques.equipped] + ['MOCHILA', "RETIRARSE"]

    def input(self, event, now_ms):
        if event == "next":
            self.index = (self.index + 1) % len(self.choices())
            return True
        if event == "back":
            if self.page == 'items':
                self.page, self.index = 'battle', 0
                self.message = ''
                return True
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
        if self.page == 'items':
            choices = self.choices()
            self.index = min(self.index, len(choices) - 1)
            key = choices[self.index]
            if key == 'VOLVER':
                self.page, self.index = 'battle', 0
                self.message = ''
                return True
            if self.pet.dead or getattr(self.pet, 'cold', False) or self.pet.exploration.away:
                self.message = 'SIN EFECTO'
                return True
            snapshot, battle = copy.deepcopy(self.pet.__dict__), copy.deepcopy(self.battle)
            if not self.battle.use_item(self.pet.adopted_inventory, key):
                self.message = 'SIN EFECTO'
            elif not self.save(self.pet):
                self.pet.__dict__.clear()
                self.pet.__dict__.update(snapshot)
                self.battle = battle
                self.message = 'ERROR AL GUARDAR'
            else:
                self.message = 'OBJETO USADO'
            self.index = min(self.index, len(self.choices()) - 1)
            return True
        if self.page == "tech":
            if self.index == len(TECHNIQUES):
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
            snapshot = copy.deepcopy(self.pet.__dict__)
            learned = progress.learned(self.tech, self.pet.species)
            if self.training and self.index == 0:
                ok = progress.train(self.pet, self.tech)
                if not ok:
                    self.message = "FALTA ENERGIA" if self.pet.get("e") < 4 else "PET NO APTO"
                elif not learned:
                    self.message = (("LLAMA APRENDIDA" if self.tech == 1 else "TECNICA APRENDIDA")
                                    if progress.learned(self.tech, self.pet.species) else
                                    "ENTRENAMIENTO %d/%d" % (progress.training, REQUIRED_TRAINING[self.tech]))
                else:
                    self.message = "ENTRENAMIENTO COMPLETO"
            else:
                ok = progress.equip(self.tech, self.pet.species)
                if ok:
                    self.message = "EQUIPADA" if self.tech in progress.equipped else "EN RESERVA"
                else:
                    self.message = "TECNICA BLOQUEADA" if not learned else "MINIMO UNA EQUIPADA"
            if ok and not self.save(self.pet):
                self.pet.__dict__.clear()
                self.pet.__dict__.update(snapshot)
                self.message = "ERROR AL GUARDAR"
            return True
        if self.battle.result:
            if not self.awarded and self.index == 0:
                self._award_result()
                self.index = 0
                return True
            return False
        if self.index == len(self.choices()) - 1:
            return False
        if self.index == len(self.choices()) - 2:
            self.page, self.index = 'items', 0
            return True
        order = -1 if self.index == 0 else self.pet.techniques.equipped[self.index - 1]
        self._round(order, now_ms)
        return True
