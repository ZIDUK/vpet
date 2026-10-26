"""Four individuals, one authoritative bag. I/O and entropy belong to adapters."""
import copy
import json
import math

from core.pet import Pet
from core.profile import PetProfile

CAPACITY = 4
MAX_BYTES = 65536
COOLDOWN_SECONDS = 86400
INCUBATION_MS = 1800000
SHARED_KEYS = ("inventory", "adopted_items", "language", "sound_enabled")


def integer(value, minimum, maximum):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError("Invalid collection number")
    return value


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate collection key")
        result[key] = value
    return result


def slot_for(pet, incubation=0, ancestors=()):
    body = pet.to_dict()
    if not PetProfile.decode(body["profile"]).pet_id:
        raise ValueError("An individual needs a durable identity")
    for key in SHARED_KEYS:
        body.pop(key, None)
    return {"pet": body, "cooldown_until": 0, "incubation_ms": incubation,
            "ancestors": list(ancestors), "birth": None}


class Collection:
    def __init__(self):
        self.slots = []
        self.active = 0
        self.shared = {}
        self.clock_ms = 0
        self.clock_offset = 0
        self.sequence = 0
        self.receipt = None
        self.storage_generation = 0

    @classmethod
    def from_pet(cls, active, reserve=None):
        result = cls()
        result.slots = [slot_for(active)]
        data = active.to_dict()
        result.shared = {key: copy.deepcopy(data[key]) for key in SHARED_KEYS}
        if reserve is not None:
            parked = slot_for(reserve)
            if reserve.profile.pet_id == active.profile.pet_id:
                if parked != result.slots[0]:
                    raise ValueError("Conflicting snapshots of one individual")
            else:
                result.slots.append(parked)
        return result

    def current(self):
        return self.pet_at(self.active)

    def pet_at(self, index):
        integer(index, 0, len(self.slots) - 1)
        data = copy.deepcopy(self.slots[index]["pet"])
        data.update(copy.deepcopy(self.shared))
        pet = Pet()
        pet.load_from_dict(data)
        pet.restore_dna(data["dna"])
        return pet

    def capture(self, pet):
        if pet.profile.encode() != self.slots[self.active]["pet"]["profile"]:
            raise ValueError("Active identity mismatch")
        old = self.slots[self.active]
        slot = slot_for(pet, old["incubation_ms"], old["ancestors"])
        slot["cooldown_until"] = old["cooldown_until"]
        slot["birth"] = copy.deepcopy(old["birth"])
        self.slots[self.active] = slot
        data = pet.to_dict()
        self.shared = {key: copy.deepcopy(data[key]) for key in SHARED_KEYS}

    @staticmethod
    def require_idle(pet, busy=False):
        if busy or pet.cold or pet.sleep.asleep or pet.exploration.away:
            raise ValueError("Finish the active session before changing individuals")

    def switch(self, active, index, confirmed=False, busy=False):
        integer(index, 0, len(self.slots) - 1)
        if not confirmed:
            raise ValueError("Confirmation required")
        self.require_idle(active, busy)
        self.capture(active)
        self.active = index
        return self.current()

    def _command(self, sequence, kind, confirmed):
        integer(sequence, 1, 0xFFFFFFFF)
        if not confirmed:
            raise ValueError("Confirmation required")
        if sequence <= self.sequence:
            if self.receipt and self.receipt["sequence"] == sequence and self.receipt["kind"] == kind:
                return self.receipt["slot"]
            raise ValueError("Old command")
        if sequence != self.sequence + 1:
            raise ValueError("Noncontiguous command")
        if len(self.slots) >= CAPACITY:
            raise ValueError("Collection full")
        return None

    def founder(self, words, entropy, confirmed=False, sequence=0):
        retry = self._command(sequence, "founder", confirmed)
        if retry is not None:
            return retry
        integer(entropy, 0, 0xFFFFFFFF)
        pet = Pet()
        pet.profile = PetProfile.from_words(words)
        if any(s["pet"]["profile"].split(":")[1] == pet.profile.pet_id for s in self.slots):
            raise ValueError("Duplicate identity")
        # Fix genes at receipt time; hatch must not reroll them or grant a bag.
        pet.roll_dna(entropy)
        self.slots.append(slot_for(pet))
        self.sequence = sequence
        self.receipt = {"sequence": sequence, "kind": "founder", "slot": len(self.slots) - 1}
        return self.receipt["slot"]

    def parent(self, index):
        from core.breeding import Parent
        pet = self.pet_at(index)
        profile = pet.profile
        return Parent(pet_id=profile.pet_id, sex=profile.sex, line_id=pet.line,
                      adult=pet.species in ("rookie", "champion", "ultimate"),
                      health=pet.stats["hp"], hunger=pet.stats["h"], energy=pet.stats["e"],
                      happiness=pet.stats["p"], injured=pet.injured, dead=pet.dead,
                      asleep=pet.sleep.asleep, away=pet.exploration.away, paused=pet.cold,
                      cooldown_remaining=max(0, self.slots[index]["cooldown_until"] - self.clock_ms),
                      parents=tuple(p for p in (profile.parent_a, profile.parent_b) if p),
                      grandparents=tuple(self.slots[index]["ancestors"]))

    def breed(self, a, b, words, seed, confirmed=False, sequence=0):
        retry = self._command(sequence, "breeding", confirmed)
        if retry is not None:
            return retry
        from core.breeding import check_pair, offspring_dna
        if not check_pair(self.parent(a), self.parent(b)):
            raise ValueError("Parents are not eligible")
        first, second = self.pet_at(a), self.pet_at(b)
        child = Pet(line=first.line)
        child.profile = PetProfile.from_words(words, first.profile.pet_id, second.profile.pet_id)
        if any(s["pet"]["profile"].split(":")[1] == child.profile.pet_id for s in self.slots):
            raise ValueError("Duplicate child identity")
        child.restore_dna(list(offspring_dna(first.dna, second.dna, seed)))
        if hasattr(first, "learning"):
            from core.learning import LearningState
            child.learning = LearningState.inherited(first.learning, second.learning)
        ancestors = [p for pet in (first, second) for p in (pet.profile.parent_a, pet.profile.parent_b) if p]
        self.slots.append(slot_for(child, INCUBATION_MS, ancestors))
        self.slots[-1]["birth"] = {"sequence": sequence, "seed": seed, "rules": 1,
                                    "parents": [first.profile.pet_id, second.profile.pet_id]}
        for index in (a, b):
            self.slots[index]["cooldown_until"] = self.clock_ms + COOLDOWN_SECONDS * 1000
        self.sequence = sequence
        self.receipt = {"sequence": sequence, "kind": "breeding", "slot": len(self.slots) - 1}
        return self.receipt["slot"]

    def advance_ms(self, elapsed, paused=False):
        integer(elapsed, 0, 86400000)
        if type(paused) is not bool:
            raise ValueError("Invalid pause flag")
        if paused or not elapsed:
            return False
        if self.clock_ms + elapsed > 0x1FFFFFFFFFFFFF:
            raise ValueError("Collection clock exhausted")
        self.clock_ms += elapsed
        slot = self.slots[self.active]
        if not slot["incubation_ms"]:
            return False
        slot["incubation_ms"] = max(0, slot["incubation_ms"] - elapsed)
        if slot["incubation_ms"]:
            return False
        child = self.current()
        child.complete_hatch("baby", preserve_dna=True)
        self.capture(child)
        return True

    def encode(self):
        document = {"version": 1, "active": self.active, "shared": self.shared,
                    "clock_ms": self.clock_ms, "clock_offset": self.clock_offset, "sequence": self.sequence,
                    "receipt": self.receipt, "slots": self.slots}
        record = json.dumps(document, separators=(",", ":"), sort_keys=True, allow_nan=False)
        if len(record.encode("utf-8")) > MAX_BYTES:
            raise ValueError("Collection exceeds storage budget")
        return record

    @classmethod
    def decode(cls, record):
        if not isinstance(record, str) or len(record.encode("utf-8")) > MAX_BYTES:
            raise ValueError("Invalid collection size")
        try:
            d = json.loads(record, object_pairs_hook=unique_object,
                           parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Invalid number")))
            if not isinstance(d, dict) or set(d) != {"version", "active", "shared", "clock_ms", "clock_offset", "sequence", "receipt", "slots"}:
                raise ValueError("Invalid collection structure")
            integer(d["version"], 1, 1)
            slots = d["slots"]
            if not isinstance(slots, list) or not 1 <= len(slots) <= CAPACITY:
                raise ValueError("Invalid capacity")
            integer(d["active"], 0, len(slots) - 1)
            integer(d["clock_ms"], 0, 0x1FFFFFFFFFFFFF)
            if type(d["clock_offset"]) not in (int, float) or not math.isfinite(d["clock_offset"]) or abs(d["clock_offset"]) > 1e12:
                raise ValueError("Invalid calendar offset")
            integer(d["sequence"], 0, 0xFFFFFFFF)
            if set(d["shared"]) != set(SHARED_KEYS):
                raise ValueError("Invalid shared bag")
            if d["shared"]["language"] not in ("ES", "EN") or type(d["shared"]["sound_enabled"]) is not bool:
                raise ValueError("Invalid shared settings")
            integer(d["shared"]["adopted_items"]["version"], 1, 1)
            for bag in (d["shared"]["inventory"], d["shared"]["adopted_items"]["counts"]):
                if not isinstance(bag, dict):
                    raise ValueError("Invalid bag")
                for count in bag.values():
                    integer(count, 0, 255)
            identities = set()
            for slot in slots:
                if set(slot) != {"pet", "cooldown_until", "incubation_ms", "ancestors", "birth"}:
                    raise ValueError("Invalid slot")
                profile = PetProfile.decode(slot["pet"]["profile"])
                if not profile.pet_id or profile.pet_id in identities:
                    raise ValueError("Invalid identity")
                identities.add(profile.pet_id)
                integer(slot["cooldown_until"], 0, 0x1FFFFFFFFFFFFF)
                integer(slot["incubation_ms"], 0, INCUBATION_MS)
                if not isinstance(slot["ancestors"], list) or len(slot["ancestors"]) > 4:
                    raise ValueError("Invalid ancestry")
                for ancestor in slot["ancestors"]:
                    PetProfile(ancestor, "M")
                birth = slot["birth"]
                if birth is not None:
                    if set(birth) != {"sequence", "seed", "rules", "parents"}:
                        raise ValueError("Invalid birth receipt")
                    integer(birth["sequence"], 1, d["sequence"])
                    integer(birth["seed"], 0, 0xFFFFFFFF)
                    integer(birth["rules"], 1, 1)
                    if birth["parents"] != [profile.parent_a, profile.parent_b] or not all(birth["parents"]):
                        raise ValueError("Invalid birth parents")
                body = slot["pet"]
                if any(key in body for key in SHARED_KEYS) or body["species"] not in ("egg", "baby", "rookie", "champion", "ultimate"):
                    raise ValueError("Invalid body")
                if body["state"] not in ("egg", "hatching", "live"):
                    raise ValueError("Invalid lifecycle")
                if slot["incubation_ms"] and (birth is None or body["species"] != "egg" or body["state"] != "egg"):
                    raise ValueError("Only a breeding egg can be incubating")
                if set(body["stats"]) != {"h", "e", "p", "hp"}:
                    raise ValueError("Invalid care")
                for value in body["stats"].values():
                    integer(value, 0, 100)
                if len(body["dna"]) != 4:
                    raise ValueError("Invalid genes")
                for value in body["dna"]:
                    integer(value, 0, 255)
                for value in body["ev"].values():
                    integer(value, 0, 252)
                probe = Pet()
                probe.load_from_dict({**body, **d["shared"]})
                probe.restore_dna(body["dna"])
                normalized = probe.to_dict()
                if any(normalized[key] != d["shared"][key] for key in SHARED_KEYS):
                    raise ValueError("Shared bag would lose data on load")
                for key in SHARED_KEYS:
                    normalized.pop(key)
                if normalized != body:
                    raise ValueError("Individual would lose data on load")
            receipt = d["receipt"]
            if d["sequence"] == 0:
                if receipt is not None:
                    raise ValueError("Invalid receipt")
            elif (not isinstance(receipt, dict) or set(receipt) != {"sequence", "kind", "slot"} or
                  receipt["sequence"] != d["sequence"] or receipt["kind"] not in ("founder", "breeding")):
                raise ValueError("Invalid receipt")
            else:
                integer(receipt["slot"], 0, len(slots) - 1)
            result = cls()
            result.slots, result.shared = slots, d["shared"]
            result.active, result.clock_ms = d["active"], d["clock_ms"]
            result.clock_offset = d["clock_offset"]
            result.sequence, result.receipt = d["sequence"], receipt
            return result
        except (KeyError, TypeError, AttributeError, OverflowError, RecursionError) as exc:
            raise ValueError("Invalid collection record") from exc
