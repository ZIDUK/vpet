"""Pure breeding decisions, independent of Pet, identity generation and storage.

Parent IDs use the existing profile's 32 lowercase hex digits (nonzero).
line_id is an opaque ASCII content token, at most 63 characters; the adapter
must establish that the line is installed and adult means rookie or later.
Ancestry is limited to two parents and four grandparents; empty IDs are unknown.
Any shared known ancestor, or either candidate among the other's ancestors,
blocks the pair. Missing ancestry and relatives beyond these two generations
cannot be detected; success is not a guarantee of unrelatedness.

cooldown_remaining is an externally calculated uint32 duration: only zero is
eligible. This module neither advances time nor spends, assigns IDs or creates
profiles. Callers must commit the externally seeded outcome atomically.
"""


class Parent:
    """Value input. Defaults are ineligible; check_pair validates every field."""

    def __init__(self, pet_id="", sex="", line_id="", adult=False,
                 health=0, hunger=0, energy=0, happiness=0,
                 injured=False, dead=False, asleep=False, away=False,
                 paused=False, busy=False, cooldown_remaining=0,
                 parents=(), grandparents=()):
        self.pet_id, self.sex, self.line_id = pet_id, sex, line_id
        self.adult = adult
        self.health, self.hunger = health, hunger
        self.energy, self.happiness = energy, happiness
        self.injured, self.dead, self.asleep = injured, dead, asleep
        self.away, self.paused, self.busy = away, paused, busy
        self.cooldown_remaining = cooldown_remaining
        self.parents = tuple(parents) if isinstance(parents, (tuple, list)) else parents
        self.grandparents = tuple(grandparents) if isinstance(grandparents, (tuple, list)) else grandparents


def _valid_id(value):
    return (isinstance(value, str) and len(value) == 32 and
            value != "0" * 32 and all(c in "0123456789abcdef" for c in value))


def _valid_parent(p):
    if not isinstance(p, Parent) or not _valid_id(p.pet_id) or p.sex not in ("M", "F"):
        return False
    if (not isinstance(p.line_id, str) or not 1 <= len(p.line_id) <= 63 or
            any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-/" for c in p.line_id)):
        return False
    flags = (p.adult, p.injured, p.dead, p.asleep, p.away, p.paused, p.busy)
    if any(type(flag) is not bool for flag in flags) or not p.adult or any(flags[1:]):
        return False
    for value, minimum in ((p.health, 80), (p.hunger, 60), (p.energy, 70), (p.happiness, 60)):
        if type(value) is not int or not minimum <= value <= 100:
            return False
    if type(p.cooldown_remaining) is not int or p.cooldown_remaining != 0:
        return False
    for refs, bound in ((p.parents, 2), (p.grandparents, 4)):
        if not isinstance(refs, (tuple, list)) or len(refs) > bound:
            return False
        if any(ref != "" and (not _valid_id(ref) or ref == p.pet_id) for ref in refs):
            return False
    known_parents = [ref for ref in p.parents if ref]
    return len(known_parents) == len(set(known_parents))


def check_pair(a, b):
    """Return eligibility without changing parents, care, ancestry or cooldown."""
    if not _valid_parent(a) or not _valid_parent(b):
        return False
    if a.pet_id == b.pet_id or a.sex == b.sex or a.line_id != b.line_id:
        return False
    ancestors_a = {ref for ref in (*a.parents, *a.grandparents) if ref}
    ancestors_b = {ref for ref in (*b.parents, *b.grandparents) if ref}
    return (a.pet_id not in ancestors_b and b.pet_id not in ancestors_a and
            not bool(ancestors_a & ancestors_b))


def _uint32_seed(seed):
    if type(seed) is not int or not 0 <= seed <= 0xFFFFFFFF:
        raise ValueError("Expected an unsigned 32-bit seed")
    return seed


class _Stream:
    def __init__(self, seed):
        self.state = _uint32_seed(seed)

    def draw(self):
        # Every operation wraps exactly like uint32_t in the C++ core.
        self.state = (self.state + 0x9E3779B9) & 0xFFFFFFFF
        value = ((self.state ^ (self.state >> 16)) * 0x85EBCA6B) & 0xFFFFFFFF
        value = ((value ^ (value >> 13)) * 0xC2B2AE35) & 0xFFFFFFFF
        return value ^ (value >> 16)

    def iv_mask(self):
        mask = self.draw() & 63
        while mask in (0, 63):
            mask = self.draw() & 63
        return mask


def iv_source_mask(seed):
    """Six IV source bits (1=B), rejecting zero/full masks; values may coincide."""
    return _Stream(seed).iv_mask()


def _valid_dna(dna):
    return (isinstance(dna, (bytes, bytearray, tuple, list)) and len(dna) == 4 and
            all(type(value) is int and 0 <= value <= 255 for value in dna))


def offspring_dna(a, b, seed):
    """Return four packed bytes; low nibble precedes high at every byte.

    Version 1 algorithm: seed a uint32 stream, select its first nonzero/nonfull
    six-bit mask, then draw once per locus in order (six IVs, two trait nibbles).
    IVs use the mask, traits use bit 6 of their draw. Low five bits equal zero
    trigger mutation (1/32); bit 5 chooses +1 when set, otherwise -1, clamped
    to 0..15. Parents and seed order are significant. No identity is derived.
    """
    if not _valid_dna(a) or not _valid_dna(b):
        raise ValueError("Expected exactly four unsigned DNA bytes per parent")
    stream = _Stream(seed)
    mask = stream.iv_mask()
    result = [0, 0, 0, 0]
    for locus in range(8):
        draw = stream.draw()
        from_b = (mask >> locus) & 1 if locus < 6 else (draw >> 6) & 1
        source = b if from_b else a
        shift = 4 * (locus % 2)
        value = (source[locus // 2] >> shift) & 15
        if draw & 31 == 0:
            value = max(0, min(15, value + (1 if draw & 32 else -1)))
        result[locus // 2] |= value << shift
    return bytes(result)
