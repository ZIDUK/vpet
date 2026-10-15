"""Portable, deterministic expedition rewards; clocks are injected Unix seconds."""

STATS = ("hp", "mp", "off", "def", "spd", "brn")
DURATIONS = {"patio": 1800, "jornada": 28800, "noche": 28800}
GOOD_CARE_MINIMUM = 50
WEEK_SECONDS = 604800


def _integer(value, maximum=2**53 - 1):
    try:
        return max(0, min(maximum, int(value)))
    except (TypeError, ValueError, OverflowError):
        return 0


def week_id(now):
    # Unix epoch was Thursday; local civil seconds use Monday as week boundary.
    return (_integer(now) + 259200) // WEEK_SECONDS


class Exploration:
    def __init__(self, data=None):
        data = data if isinstance(data, dict) and data.get("version") == 1 else {}
        self.week = _integer(data.get("week"))
        self.week_ev = _integer(data.get("week_ev"), 8)
        self.week_mastery = _integer(data.get("week_mastery"), 4)
        self.guide = bool(data.get("guide", False))
        self.guide_pending = bool(data.get("guide_pending", False)) and not self.guide
        self.trip = None
        trip = data.get("trip")
        if isinstance(trip, dict) and isinstance(trip.get("route"), str) and trip["route"] in DURATIONS:
            route = trip["route"]
            stat = trip.get("stat")
            started = trip.get("started")
            if (type(started) is int and 0 <= started <= 2**53 - 1
                    and (route != "jornada" or stat in STATS)):
                self.trip = {"route": route, "stat": stat if route == "jornada" else None,
                             "started": started,
                             "good": bool(trip.get("good", False)),
                             "learning": bool(trip.get("learning", False))}
        receipt = data.get("receipt")
        self.receipt = None
        if isinstance(receipt, dict) and isinstance(receipt.get("route"), str) and receipt["route"] in DURATIONS:
            self.receipt = {"route": receipt["route"],
                            "stat": receipt.get("stat") if receipt.get("stat") in STATS else None,
                            "good": bool(receipt.get("good")), "full": bool(receipt.get("full")),
                            "elapsed": _integer(receipt.get("elapsed"), DURATIONS[receipt["route"]]),
                            "energy": _integer(receipt.get("energy"), 25),
                            "ev": _integer(receipt.get("ev"), 2),
                            "mastery": _integer(receipt.get("mastery"), 2),
                            "learning": _integer(receipt.get("learning"), 1),
                            "guide": bool(receipt.get("guide")), "learned": bool(receipt.get("learned"))}
            if self.receipt["stat"] is None:
                self.receipt["ev"] = 0
        if self.trip:
            self.receipt = None

    @property
    def away(self):
        return self.trip is not None

    def to_dict(self):
        return {"version": 1, "week": self.week, "week_ev": self.week_ev,
                "week_mastery": self.week_mastery, "guide": self.guide,
                "guide_pending": self.guide_pending,
                "trip": dict(self.trip) if self.trip else None,
                "receipt": dict(self.receipt) if self.receipt else None}

    def remaining(self, now):
        if not self.trip:
            return 0
        elapsed = max(0, _integer(now) - self.trip["started"])
        return max(0, DURATIONS[self.trip["route"]] - elapsed)

    def start(self, pet, route, stat, now):
        if self.away or not pet.is_live or pet.species in ("egg", "baby") or pet.dead:
            return False
        if route not in DURATIONS or (route == "jornada" and stat not in STATS):
            return False
        self.trip = {"route": route, "stat": stat if route == "jornada" else None,
                     "started": _integer(now),
                     "good": not pet.injured and all(pet.get(s) >= GOOD_CARE_MINIMUM for s in ("h", "e", "p")),
                     "learning": not pet.techniques.learned(1)}
        self.receipt = None
        return True

    def preview(self, pet, now):
        if not self.trip:
            return None
        t = self.trip
        duration = DURATIONS[t["route"]]
        elapsed = min(duration, max(0, _integer(now) - t["started"]))
        reset_week = week_id(now) > self.week
        spent_ev = 0 if reset_week else self.week_ev
        spent_mastery = 0 if reset_week else self.week_mastery
        result = {"route": t["route"], "stat": t["stat"], "good": t["good"],
                  "elapsed": elapsed, "full": elapsed == duration,
                  "energy": 0, "ev": 0, "mastery": 0, "learning": 0,
                  "guide": False, "learned": False}
        if t["route"] == "patio":
            amount = (25 if t["good"] else 10) * elapsed // duration
            result["energy"] = max(0, min(amount, 100 - pet.get("e")))
        elif t["route"] == "jornada":
            result["ev"] = min(elapsed // 14400, 8 - spent_ev, 252 - pet.ev_at(t["stat"]))
            result["guide"] = t["good"] and elapsed == duration and not (self.guide or self.guide_pending)
        elif t["learning"]:
            result["learning"] = int(elapsed == duration and not pet.techniques.learned(1))
            result["learned"] = bool(result["learning"] and pet.techniques.training >= 1)
        else:
            result["mastery"] = min(elapsed // 14400, 4 - spent_mastery, 100 - pet.techniques.mastery[1])
        return result

    def claim(self, pet, now):
        reward = self.preview(pet, now)
        if reward is None:
            return None
        current_week = week_id(now)
        if current_week > self.week:
            self.week, self.week_ev, self.week_mastery = current_week, 0, 0
        pet.stats["e"] += reward["energy"]
        if reward["ev"]:
            pet.gain_ev(reward["stat"], reward["ev"])
            self.week_ev += reward["ev"]
        if reward["mastery"]:
            pet.techniques.mastery[1] += reward["mastery"]
            self.week_mastery += reward["mastery"]
        if reward["learning"]:
            pet.techniques.training = min(255, pet.techniques.training + 1)
        if reward["guide"]:
            self.guide = True
        self.trip = None
        self.receipt = reward
        return reward

    def use_guide(self, pet, stat):
        if not self.guide or self.away or stat not in STATS or pet.ev_at(stat) >= 252:
            return 0
        pet.gain_ev(stat, 1)
        self.guide = False
        if self.guide_pending:
            self.guide, self.guide_pending = True, False
        return 1


def departure_reward(pet, route, stat, now):
    preview = Exploration(pet.exploration.to_dict())
    if not preview.start(pet, route, stat, now):
        return None
    return preview.preview(pet, now + DURATIONS[route])
