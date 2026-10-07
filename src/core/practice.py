"""Deterministic practice rules; integer arithmetic mirrored in PracticeBattle.h."""
from core.techniques import TECHNIQUES

AUTO = -1


class Fighter:
    def __init__(self, stats, equipped=(0, 1, 2), mastery=(0, 0, 0), personality=0, bond=50):
        self.stats = tuple(max(1, min(99, int(v))) for v in stats)
        if len(self.stats) != 6:
            raise ValueError("Expected HP MP OFF DEF SPD BRN")
        self.max_hp = 40 + self.stats[0] * 2
        self.max_mp = 10 + self.stats[1]
        self.hp, self.mp = self.max_hp, self.max_mp
        self.equipped = tuple(equipped)
        self.mastery = tuple(mastery)
        self.personality, self.bond = personality % 3, max(0, min(100, bond))
        self.cooldowns = [0, 0, 0]

    def valid(self, action):
        return (action in self.equipped and self.cooldowns[action] == 0
                and self.mp >= TECHNIQUES[action]["mp"])


def choose(fighter, requested=AUTO):
    scores = []
    for i, tech in enumerate(TECHNIQUES):
        if not fighter.valid(i):
            continue
        if i == 2:
            score = 5 + (35 if fighter.hp * 3 < fighter.max_hp else 0)
            score += 25 if fighter.mp < 8 else 0
            score += 15 if fighter.personality == 1 else 0
        else:
            score = tech["power"] + fighter.mastery[i] // 20
            score += 12 if fighter.personality == 0 else 0
            score += 12 if fighter.personality == 2 and i == 1 else 0
            score += fighter.stats[5] // 10 if i == 1 else 0
        score += 10 + fighter.bond // 2 if requested == i else 0
        scores.append((score, -i))
    if not scores:
        return 2, "RECUPERA"  # universal defensive fallback avoids a deadlock
    chosen = -max(scores)[1]
    if requested == AUTO:
        reason = "A SU CRITERIO"
    elif chosen == requested:
        reason = "SIGUE ORDEN"
    elif fighter.mp < TECHNIQUES[requested]["mp"]:
        reason = "SIN MP"
    elif fighter.cooldowns[requested]:
        reason = "EN RECARGA"
    else:
        reason = "PREFIERE DEFENDER" if chosen == 2 else "PREFIERE ATACAR"
    return chosen, reason


class PracticeBattle:
    def __init__(self, player, rival=None):
        self.player = player
        self.rival = rival or Fighter((25, 20, 24, 20, 22, 20), personality=1)
        self.round = 0
        self.result = None
        self.reason = "ELIGE ORDEN"
        self.actions = (None, None)
        self.damage = (0, 0)
        self.uses = [0, 0, 0]

    def step(self, requested=AUTO):
        if self.result is not None:
            return False
        if requested != AUTO and requested not in self.player.equipped:
            return False
        a, self.reason = choose(self.player, requested)
        b, _ = choose(self.rival)
        self.round += 1
        fighters = (self.player, self.rival)
        actions = (a, b)
        damage = [0, 0]
        # Decrement old cooldowns only after both decisions; new ones block next round.
        for fighter in fighters:
            fighter.cooldowns = [max(0, cd - 1) for cd in fighter.cooldowns]
        for i in (0, 1):
            if actions[i] == 2:
                fighters[i].mp = min(fighters[i].max_mp, fighters[i].mp + 4)
        speed_diff = self.player.stats[4] - self.rival.stats[4]
        first = 0 if speed_diff > 0 or (speed_diff == 0 and self.round % 2 == 1) else 1
        self.actions = (None, None)
        executed = [None, None]
        for i in (first, 1 - first):
            source, target, action = fighters[i], fighters[1 - i], actions[i]
            if source.hp <= 0:
                continue
            executed[i] = action
            if i == 0:
                self.uses[action] += 1
            tech = TECHNIQUES[action]
            source.mp -= tech["mp"]
            source.cooldowns[action] = tech["cooldown"]
            if action != 2:
                amount = max(1, tech["power"] + source.stats[2] // 3
                             + source.mastery[action] // 20 - target.stats[3] // 4)
                if actions[1 - i] == 2:
                    amount = max(1, amount // 2)
                damage[i] = min(target.hp, amount)
                target.hp = max(0, target.hp - amount)
        self.actions, self.damage = tuple(executed), tuple(damage)
        if self.rival.hp == 0:
            self.result = "VICTORIA"
        elif self.player.hp == 0:
            self.result = "DERROTA"
        elif self.round >= 30:
            self.result = "EMPATE"
        return True
