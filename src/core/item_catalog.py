"""Official v1 item definitions. Stable IDs and legacy menu slots never change."""

CATALOG_VERSION = 1
CATEGORIES = ("food", "recovery", "effort", "mood", "training_boost")


def _effect(kind, target, amount, cap):
    return {"kind": kind, "target": target, "amount": amount, "cap": cap}


def _item(item_id, index, category, icon, names, descriptions, blurbs, effects,
          limits, source, initial, unlimited=False, legacy_mixed=False):
    return {
        "id": item_id, "index": index, "category": category, "rarity": "common",
        "icon": icon, "names": dict(zip(("ES", "EN"), names)),
        "descriptions": dict(zip(("ES", "EN"), descriptions)),
        "blurbs": dict(zip(("ES", "EN"), blurbs)),
        "stack_max": None if unlimited else 1 if item_id == "guide" else 99,
        "effects": effects,
        "target": tuple(effect["target"] for effect in effects),
        "magnitude": tuple(effect["amount"] for effect in effects),
        "duration": "next_completed_training" if item_id == "guide" else "instant",
        "limits": ("hatched", "alive", *limits), "source": source, "initial_stock": initial,
        "unlimited": unlimited, "legacy_mixed": legacy_mixed,
        "firmware_available": True,
    }


ITEMS = (
    _item("meat", 0, "food", "ItemMeat", ("CARNE", "MEAT"),
          ("Carne asada para saciar el hambre y ganar peso.",
           "Roasted meat that restores hunger and increases weight."),
          ("+20 HAM +1 PESO", "+20 HUN +1 WT"),
          (_effect("restore", "h", 20, 100), _effect("weight", "weight", 1, 99)),
          ("feeding", "home", "awake", "one_overfeed_per_hunger_cycle"),
          "unlimited_feeding", 3, unlimited=True),
    _item("energy", 1, "recovery", "ItemEnergy", ("TONICO", "TONIC"),
          ("Tonico que recupera energia. Conserva el bono antiguo de EV de MP.",
           "Tonic that restores energy and retains its legacy MP EV bonus."),
          ("+25 ENE MP+2EV", "+25 ENE MP+2EV"),
          (_effect("restore", "e", 25, 100), _effect("ev", "mp", 2, 252)),
          ("backpack", "home", "energy_below_100"), "starter_kit", 2, legacy_mixed=True),
    _item("exp", 2, "effort", "ItemExp", ("ESTRELLA", "STAR"),
          ("Insignia de experiencia que aumenta esfuerzo y EV de mente.",
           "Experience badge that increases effort and mind EV."),
          ("+8 ESF BRN+2EV", "+8 EFF BRN+2EV"),
          (_effect("effort", "effort", 8, 100), _effect("ev", "brn", 2, 252)),
          ("backpack", "home"), "starter_kit", 1, legacy_mixed=True),
    _item("ring", 3, "mood", "ItemRing", ("AMULETO", "AMULET"),
          ("Amuleto generico que mejora el animo; no aumenta fuerza ni evoluciona al pet.",
           "A generic charm that improves mood; it does not increase strength or evolve the pet."),
          ("+15 ANIMO", "+15 MOOD"),
          (_effect("mood", "p", 15, 100),), ("backpack", "home"), "starter_kit", 1),
    _item("protein", 4, "food", "ItemProtein", ("PROTEINA", "PROTEIN"),
          ("Suplemento alimenticio que recupera energia y aumenta peso, sin EV.",
           "Food supplement that restores energy and increases weight, without EV."),
          ("+20 ENE +2 PESO", "+20 ENE +2 WT"),
          (_effect("restore", "e", 20, 100), _effect("weight", "weight", 2, 99)),
          ("feeding", "home", "awake", "energy_at_most_80", "once_per_hunger_cycle"),
          "unlimited_feeding", 2, unlimited=True),
    _item("medkit", 5, "recovery", "ItemMedkit", ("BOTIQUIN", "MEDKIT"),
          ("Primeros auxilios: elimina una lesion y recupera salud de cuidado.",
           "First aid: clears an injury and restores care health."),
          ("CURA +20 HP", "HEAL +20 HP"),
          (_effect("restore", "hp", 20, 100), _effect("heal_injury", "injured", 1, 1)),
          ("backpack", "home", "injured"), "starter_kit", 1),
    _item("guide", 7, "training_boost", "ItemGuide", ("GUIA", "GUIDE"),
          ("Manual que da +1 EV en la proxima sesion de atributo completada y guardada.",
           "Manual that grants +1 EV in the next completed and saved attribute session."),
          ("+1 EV/SESION", "+1 EV/TRAIN"),
          (_effect("training_ev_bonus", "trained_stat", 1, 252),),
          ("backpack", "home", "completed_attribute_training", "keep_on_cancel_or_save_failure", "keep_if_stat_full"),
          "full_jornada_good_care", 0),
)
ITEM_BY_ID = {item["id"]: item for item in ITEMS}
LEGACY_ITEMS = ITEMS[:6]
DEFAULT_STOCK = {item["id"]: item["initial_stock"] for item in LEGACY_ITEMS}


def item_at(index):
    return next((item for item in ITEMS if item["index"] == index), None)


def effect_amount(item_id, kind, target):
    return next(effect["amount"] for effect in ITEM_BY_ID[item_id]["effects"]
                if effect["kind"] == kind and effect["target"] == target)
