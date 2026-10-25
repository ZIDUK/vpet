"""Portable individual identity. Entropy and persistence belong to adapters."""


def _valid_id(value):
    return (isinstance(value, str) and len(value) == 32 and
            all(c in "0123456789abcdef" for c in value) and value != "0" * 32)


class PetProfile:
    def __init__(self, pet_id="", sex="", parent_a="", parent_b=""):
        if pet_id or sex or parent_a or parent_b:
            if not _valid_id(pet_id) or sex not in ("M", "F"):
                raise ValueError("Invalid individual profile")
            if parent_a or parent_b:
                if (not _valid_id(parent_a) or not _valid_id(parent_b) or
                        parent_a == parent_b or pet_id in (parent_a, parent_b)):
                    raise ValueError("Invalid parent references")
        self.pet_id, self.sex = pet_id, sex
        self.parent_a, self.parent_b = parent_a, parent_b

    @classmethod
    def from_words(cls, words, parent_a="", parent_b=""):
        if len(words) != 4 or any(type(w) is not int or not 0 <= w <= 0xFFFFFFFF for w in words):
            raise ValueError("Expected four unsigned 32-bit words")
        return cls("".join("%08x" % w for w in words), "F" if words[0] & 1 else "M", parent_a, parent_b)

    @classmethod
    def decode(cls, record):
        if record == "":
            return cls()
        if not isinstance(record, str) or len(record) > 103:
            raise ValueError("Invalid profile record")
        fields = record.split(":")
        if len(fields) != 5 or fields[0] != "1" or not fields[3] or not fields[4]:
            raise ValueError("Unsupported profile version or format")
        return cls(fields[1], fields[2], "" if fields[3] == "-" else fields[3],
                   "" if fields[4] == "-" else fields[4])

    def encode(self):
        # Validate again: callers cannot persist a partially edited identity.
        PetProfile(self.pet_id, self.sex, self.parent_a, self.parent_b)
        if not self.pet_id:
            return ""
        return "1:%s:%s:%s:%s" % (self.pet_id, self.sex, self.parent_a or "-", self.parent_b or "-")

    def __eq__(self, other):
        return isinstance(other, PetProfile) and self.encode() == other.encode()
