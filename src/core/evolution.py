"""Evolution rules shared by the simulator and firmware catalog.

Timers compare `stage_age_seconds * scale` against `min_stage_age_seconds`.
Synthetic tests can still use `min_age_seconds` and `pet.age_seconds`.
"""

STABILITY_SECONDS = 30
EVOLUTION_NODE_COUNT = 8
EVOLUTION_WINDOW = 3
EVO_CHIP = 40
EVO_GAP = 6
EVO_X0 = 5
EVO_COLOR_Y = 50
EVO_DARK_Y = 94


def evolution_tree_node(index):
    index = int(index) % EVOLUTION_NODE_COUNT
    dark = index >= 5
    stage = index if index < 5 else index - 3
    return stage, dark


def evolution_tree_xy(index):
    stage, dark = evolution_tree_node(index)
    x = EVO_X0 + stage * (EVO_CHIP + EVO_GAP)
    y = EVO_DARK_Y if dark else EVO_COLOR_Y
    return x, y


EVOLUTION_PORTRAITS = ("Egg.bmp", "Sparkmon.bmp", "Firemon.bmp", "Flamemon.bmp", "Dragfiremon.bmp")
EVOLUTION_SHORT_NAMES = (("EGG", "HUEVO"), ("SPARK", "SPARK"), ("FIRE", "FIRE"), ("FLAME", "FLAME"), ("DRAG", "DRAG"))
EVOLUTION_REACH_FROM = (None, None, "baby", "rookie", "champion")


def evolution_current_stage(pet):
    return {"egg": 0, "baby": 1, "rookie": 2, "champion": 3, "ultimate": 4}.get(getattr(pet, "species", "egg"), 0)


def evolution_hidden(stage, dark, current_stage):
    return (dark and stage >= 2) or (not dark and stage > current_stage)


def requirements_to_reach(stage, registry, spanish=False):
    if stage <= 1:
        return "8S"
    form = (registry or {}).get(EVOLUTION_REACH_FROM[stage], {})
    return format_requirements(form, spanish)


def split_requirement_lines(text):
    parts = (text or "").split(" ", 1)
    first = parts[0]
    second = parts[1] if len(parts) > 1 else ""
    return first, second


def evolution_window(selected, size=EVOLUTION_WINDOW):
    selected = int(selected) % EVOLUTION_NODE_COUNT
    start = selected - 1
    if start < 0:
        start = 0
    if start + size > EVOLUTION_NODE_COUNT:
        start = EVOLUTION_NODE_COUNT - size
    return tuple(range(start, start + size))


def evolution_card(index, pet, registry, spanish=False):
    stage, dark = evolution_tree_node(index)
    current_stage = evolution_current_stage(pet)
    hidden = evolution_hidden(stage, dark, current_stage)
    if hidden:
        return {
            "stage": stage,
            "dark": dark,
            "hidden": True,
            "label": "???",
            "status": "???",
            "requirements": "",
            "snapshot": "",
            "portrait": EVOLUTION_PORTRAITS[stage],
        }
    status = "NOW" if stage == current_stage else "REACHED"
    if spanish:
        status = "AHORA" if status == "NOW" else "LOGRADO"
    snapshot = ""
    if stage == current_stage:
        snapshot = "%ds CM%d" % (int(getattr(pet, "stage_age_seconds", 0)), int(getattr(pet, "care_mistakes", 0)))
    names = EVOLUTION_SHORT_NAMES[stage]
    return {
        "stage": stage,
        "dark": dark,
        "hidden": False,
        "label": names[1] if spanish else names[0],
        "status": status,
        "requirements": requirements_to_reach(stage, registry, spanish),
        "snapshot": snapshot,
        "portrait": EVOLUTION_PORTRAITS[stage],
    }


class Evolution:
    def __init__(self, registry):
        self.registry = registry

    def check(self, pet, scale=1):
        if getattr(pet, "is_egg", False) or pet.species == "egg":
            return (None, None)
        form_data = self.registry.get(pet.species)
        if not form_data:
            return (None, None)
        if not form_data.get("automatic", True):
            return (None, None)
        if form_data.get("requirements_pending"):
            return (None, None)
        next_form = form_data.get("evolves_to")
        if not next_form:
            return (None, None)

        if "min_stage_age_seconds" in form_data:
            age = getattr(pet, "stage_age_seconds", pet.age_seconds)
            if age * scale < form_data.get("min_stage_age_seconds", 0):
                return (None, None)
        else:
            if pet.age_seconds < form_data.get("min_age_seconds", 0):
                return (None, None)

        max_cm = form_data.get("max_care_mistakes")
        if max_cm is not None and getattr(pet, "care_mistakes", 0) > max_cm:
            return (None, None)

        for stat, min_val in form_data.get("requirements", {}).items():
            if pet.get(stat) < min_val:
                return (None, None)

        battles_required = form_data.get("battles_required", 0)
        battles = getattr(pet, "battles_this_form", pet.battles_won)
        if battles < battles_required:
            return (None, None)
        wins = getattr(pet, "battles_won", 0)
        losses = getattr(pet, "battles_lost", 0)
        played = wins + losses
        if battles_required and played > 0 and wins * 100 < 60 * played:
            return (None, None)

        return (next_form, "stats + age + battles met")

    def evolve(self, pet, scale=1):
        new_form, reason = self.check(pet, scale)
        if new_form:
            self._apply(pet, new_form)
            return True
        return False

    def force(self, pet):
        form_data = self.registry.get(pet.species, {})
        new_form = form_data.get("evolves_to")
        if new_form:
            self._apply(pet, new_form)
            return True
        if pet.species == "ultimate":
            pet.reset_to_egg()
            return True
        return False

    @staticmethod
    def _apply(pet, new_form):
        pet.species = new_form
        for stat in pet.stats:
            pet.stats[stat] = min(100, pet.stats[stat] + 10)
        pet.reset_after_evolution()


def format_requirements(form_data, spanish=False):
    """Build Pedia text from catalog fields only. Empty string if pending/missing."""
    if not form_data or form_data.get("requirements_pending"):
        return ""
    if not form_data.get("evolves_to"):
        return "FINAL POR AHORA" if spanish else "FINAL FOR NOW"
    parts = []
    seconds = form_data.get("min_stage_age_seconds", form_data.get("min_age_seconds"))
    if seconds:
        hours = int(seconds) // 3600
        minutes = (int(seconds) % 3600) // 60
        parts.append("%dH" % hours if minutes == 0 else "%dH%dM" % (hours, minutes))
    if form_data.get("max_care_mistakes") is not None:
        parts.append("CM<=%d" % form_data["max_care_mistakes"])
    if form_data.get("battles_required"):
        parts.append("BAT%d WR60" % form_data["battles_required"])
    req = form_data.get("requirements") or {}
    if req:
        chunks = []
        labels = {"h": "H", "e": "E", "p": "P", "hp": "HP"}
        for key in ("h", "e", "p", "hp"):
            if key in req:
                chunks.append("%s%d" % (labels[key], req[key]))
        if chunks:
            parts.append(" ".join(chunks))
    return " ".join(parts)
