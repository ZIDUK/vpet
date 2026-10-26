"""Exploration navigation and whole-pet atomic start/claim transactions."""
from core.exploration import DURATIONS, STATS


class ExplorationSession:
    def __init__(self, pet, save, now):
        self.pet, self.save, self.now = pet, save, now
        self.index = 0
        self.route, self.stat = "patio", "off"
        self.message = ""
        self.page = "trip" if pet.exploration.away else "receipt" if pet.exploration.receipt else "routes"

    def choices(self):
        if self.pet.species in ("egg", "baby") or self.pet.dead:
            return ("back",)
        if self.page == "routes":
            return ("patio", "jornada", "noche", "back")
        if self.page == "stats":
            return (*STATS, "back")
        if self.page == "confirm":
            return ("start", "back")
        if self.page == "trip":
            return (("claim", "back") if not self.pet.exploration.remaining(self.now())
                    else ("back", "recall"))
        if self.page == "recall":
            return ("back", "claim")
        return ("done",)

    def _transaction(self, claim):
        snapshot = self.pet.to_dict()
        if claim:
            result = self.pet.exploration.claim(self.pet, self.now())
        else:
            result = self.pet.exploration.start(self.pet, self.route, self.stat, self.now())
        if not result:
            self.message = "blocked"
            return
        if claim:
            route = ("patio", "jornada", "noche").index(result["route"])
            score = 50 if result["good"] else -50
            score += min(30, result["ev"] * 10 + result["mastery"] * 5)
            self.pet.learning.record(self.pet.learning.next_sequence, 2, 0, route, max(-100, min(100, score)))
        try:
            saved = self.save(self.pet)
        except (OSError, ValueError):
            saved = False
        if not saved:
            self.pet.load_from_dict(snapshot)
            self.message = "save_failed"
            return
        self.page, self.index = ("receipt" if claim else "trip"), 0
        self.message = ""

    def input(self, command):
        self.index = min(self.index, len(self.choices()) - 1)
        if command == "next":
            self.index = (self.index + 1) % len(self.choices())
            self.message = ""
        elif command == "back":
            if self.page in ("stats", "confirm"):
                self.page, self.index = "routes", list(DURATIONS).index(self.route)
            elif self.page == "recall":
                self.page, self.index = "trip", 0
            else:
                return False
        elif command == "action":
            choice = self.choices()[self.index]
            if choice == "done":
                snapshot = self.pet.to_dict()
                self.pet.exploration.receipt = None
                try:
                    saved = self.save(self.pet)
                except (OSError, ValueError):
                    saved = False
                if saved:
                    self.page, self.index, self.message = "routes", 0, ""
                else:
                    self.pet.load_from_dict(snapshot)
                    self.message = "save_failed"
            elif choice == "back":
                if self.page in ("stats", "confirm"):
                    self.page, self.index = "routes", list(DURATIONS).index(self.route)
                elif self.page == "recall":
                    self.page, self.index = "trip", 0
                else:
                    return False
            elif choice in DURATIONS:
                self.route = choice
                self.page, self.index = ("stats" if choice == "jornada" else "confirm"), 0
            elif self.page == "stats":
                self.stat = choice
                self.page, self.index = "confirm", 0
            elif choice == "start":
                self._transaction(False)
            elif choice == "claim":
                self._transaction(True)
            elif choice == "recall":
                self.page, self.index = "recall", 0
        return True
