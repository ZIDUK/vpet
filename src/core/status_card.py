"""Right-hand Status fiche: labels, icons, and pet pin for the T-Display split.

The four Status pages (1/4 vital, 2/4 care, 3/4 battle, 4/4 DNA) share
the same data shape: a list of rows with an icon name, a localised
label, a value, and an optional extra string. The renderer reads the
shape, the catalog of strings lives in :mod:`core.i18n`, and the
domain values (HP, energy, age, weight, ...) come straight from the
pet. No new field is introduced here; the fiche is the only consumer.

The page count is pinned at 4; ``STATUS_PAGE_COUNT`` is referenced
from the renderer to drive the cyclic NEXT behaviour and the header
label.
"""

STATUS_PAGE_COUNT = 4
STATUS_SPLIT_X = 100
STATUS_CARD_Y = 54
STATUS_CARD_ROW = 27
STATUS_CARD_H = 24
HELIX_Y = 56
HELIX_WIDTH = 36
HELIX_HEIGHT = 74
HELIX_RUNGS = 6
DNA_STAT_NAMES = (("hp", "hp"), ("mp", "mp"), ("off", "off"),
                  ("def", "def"), ("spd", "spd"), ("brn", "brn"))


def pin_pet_x(pet_size, split_x=STATUS_SPLIT_X):
    return max(0, (int(split_x) - int(pet_size)) // 2)


# ---------------------------------------------------------------------------
# Page 1/4: vital. HP de crianza (current HP, not the combat pool),
# alimentacion (ham/hambre), energia y animo. HP lives on ``stats["hp"]``
# in the pet; the combat-stat HP (``combat_stat("hp") * 2 + 40``) is
# shown on the DNA page next to the other five stats so the two never
# share the same screen.
# ---------------------------------------------------------------------------


def vital_rows(pet, spanish):
    """Return the four vital rows. The shape is 4-tuple
    (icon, label, value_str, kind) where ``kind`` is a stable key the
    renderer uses to pick the bar color (red/orange/cyan/green)."""
    from core.i18n import tr
    return (
        ("Heart", tr(pet, "status.vital.hp_care.label"),
            tr(pet, "status.vital.hp_care.value", int(pet.stats["hp"])),
            "hp_care"),
        ("Feed", tr(pet, "status.vital.feed.label"),
            tr(pet, "status.vital.feed.value", int(pet.stats["h"])),
            "feed"),
        ("Energy", tr(pet, "status.vital.energy.label"),
            tr(pet, "status.vital.energy.value", int(pet.stats["e"])),
            "energy"),
        ("Brain", tr(pet, "status.vital.mood.label"),
            tr(pet, "status.vital.mood.value", int(pet.stats["p"])),
            "mood"),
    )


# ---------------------------------------------------------------------------
# Page 2/4: care. Six rows including cumulative injuries.
# The age is adapted to the most readable unit without changing the
# underlying ``stage_age_seconds`` value.
# ---------------------------------------------------------------------------


def care_rows(pet, spanish, clock_text, call_text):
    """Return the six care rows. The shape is 4-tuple
    (icon, label, value, extra). ``extra`` is the clock or call-reason
    string for the first row only; the rest are empty. The age is
    formatted as a short string with the most readable unit."""
    from core.i18n import format_age, tr
    extra = call_text or clock_text or ""
    age_value = format_age(pet,
                            getattr(pet, "stage_age_seconds",
                                    pet.age_seconds))
    return (
        ("Clock", tr(pet, "status.care.age.label"),
            age_value, extra),
        ("Feed", tr(pet, "status.care.overfeed.label"),
            int(getattr(pet, "overfeeds", 0)), ""),
        ("Heart", tr(pet, "status.care.care_err.label"),
            int(getattr(pet, "care_mistakes", 0)), ""),
        ("Training", tr(pet, "status.care.effort.label"),
            tr(pet, "status.care.effort.value", min(4, pet.effort_hearts())),
            ""),
        ("Battle", tr(pet, "status.care.battles.label"),
            tr(pet, "status.care.battles.value",
               int(getattr(pet, "battles_this_form", pet.battles_won))),
            ""),
        ("Medkit", tr(pet, "status.care.injuries.label"),
            tr(pet, "status.care.injuries.value", int(pet.injuries)), ""),
    )


# ---------------------------------------------------------------------------
# Page 3/4: battle. Peso, DP, %victorias, proteina, W-L. DP keeps its
# name (the user asked not to rename it). When the pet has no
# encounters the win-rate and W-L show "--" instead of a misleading 0%.
# ---------------------------------------------------------------------------


def battle_rows(pet, spanish):
    """Return the five battle rows. The shape is 3-tuple
    (icon, label, value). DP keeps its name; weight and W-L use
    clear labels. When the pet has no encounters, the win-rate and
    W-L show '--' instead of a misleading 0%."""
    from core.i18n import tr
    from core.nutrition import healthy_weight_range
    played = (getattr(pet, "battles_won", 0)
              + getattr(pet, "battles_lost", 0))
    if played == 0:
        wr = tr(pet, "status.battle.winrate.empty")
        wl = tr(pet, "status.battle.wl.empty")
    else:
        wr = tr(pet, "status.battle.winrate.value",
                 (pet.battles_won * 100) // played)
        wl = tr(pet, "status.battle.wl.value",
                 int(getattr(pet, "battles_won", 0)),
                 int(getattr(pet, "battles_lost", 0)))
    healthy_range = healthy_weight_range(getattr(pet, "species", ""))
    weight_label = tr(pet, "status.battle.weight.label")
    if healthy_range:
        low, high = healthy_range
        weight_label = ("PESO %d-%d" if spanish else "WEIGHT %d-%d") % (low, high)
    return (
        ("Weight", weight_label,
            tr(pet, "status.battle.weight.value",
               int(getattr(pet, "weight", 5)))),
        ("Battle", tr(pet, "status.battle.dp.label"),
            tr(pet, "status.battle.dp.value",
               min(3, int(getattr(pet, "dp", 1))))),
        ("Trophy", tr(pet, "status.battle.winrate.label"), wr),
        ("Protein", tr(pet, "status.battle.protein.label"),
            tr(pet, "status.battle.protein.value",
               min(7, int(getattr(pet, "protein", 0))))),
        ("Versus", tr(pet, "status.battle.wl.label"), wl),
    )


# ---------------------------------------------------------------------------
# Page 4/4: DNA. The full code XX-XX-XX-XX is rendered alongside the
# rotating helix; six combat stats use the current stage/gene ceiling and a
# separate accumulated EV column. The renderer draws this page; the helper
# here only returns the data.
# ---------------------------------------------------------------------------


def dna_stat_rows(pet):
    if not getattr(pet, "has_dna", lambda: False)():
        return []
    return [(key, pet.combat_stat(key), pet.ev_at(key)) for _, key in DNA_STAT_NAMES]
