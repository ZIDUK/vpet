"""Right-hand Status fiche: labels, icons, and pet pin for the T-Display split."""

STATUS_PAGE_COUNT = 4
STATUS_SPLIT_X = 100
STATUS_CARD_Y = 54
STATUS_CARD_ROW = 27
STATUS_CARD_H = 24
HELIX_Y = 56
HELIX_WIDTH = 36
HELIX_HEIGHT = 74
HELIX_RUNGS = 6
DNA_STAT_NAMES = (("HP", "hp"), ("MP", "mp"), ("OFF", "off"), ("DEF", "def"), ("SPD", "spd"), ("BRN", "brn"))


def pin_pet_x(pet_size, split_x=STATUS_SPLIT_X):
    return max(0, (int(split_x) - int(pet_size)) // 2)


def vital_rows(pet, spanish):
    return (
        ("Heart", "PV" if spanish else "HP", pet.stats["hp"]),
        ("Feed", "HAM" if spanish else "HUN", pet.stats["h"]),
        ("Energy", "ENE", pet.stats["e"]),
    )


def care_rows(pet, spanish, clock_text, call_text):
    extra = call_text or clock_text or ""
    return (
        (
            "Clock",
            "EDAD" if spanish else "AGE",
            "%ds" % int(getattr(pet, "stage_age_seconds", pet.age_seconds)),
            extra,
        ),
        ("Feed", "OF", int(getattr(pet, "overfeeds", 0)), ""),
        ("Heart", "CM", int(getattr(pet, "care_mistakes", 0)), ""),
        ("Training", "ESF" if spanish else "EFF", "%d/4" % min(4, pet.effort_hearts()), ""),
        ("Battle", "BAT", int(getattr(pet, "battles_this_form", pet.battles_won)), ""),
    )


def battle_rows(pet, spanish):
    played = getattr(pet, "battles_won", 0) + getattr(pet, "battles_lost", 0)
    wr = "--" if played == 0 else "%d%%" % ((pet.battles_won * 100) // played)
    return (
        ("Weight", "PES" if spanish else "WT", int(getattr(pet, "weight", 5))),
        ("Battle", "DP", "%d/3" % min(3, getattr(pet, "dp", 1))),
        ("Trophy", "WR", wr),
        ("Protein", "PR", "%d/7" % min(7, getattr(pet, "protein", 0))),
        ("Versus", "W-L", "%d-%d" % (getattr(pet, "battles_won", 0), getattr(pet, "battles_lost", 0))),
    )


def dna_stat_rows(pet):
    if not getattr(pet, "has_dna", lambda: False)():
        return []
    return [(label, pet.combat_stat(key), pet.ev_at(key)) for label, key in DNA_STAT_NAMES]
