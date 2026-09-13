"""Evolution rules shared by the simulator and firmware catalog.

Timers compare `stage_age_seconds * scale` against `min_stage_age_seconds`.
Synthetic tests can still use `min_age_seconds` and `pet.age_seconds`.
"""

STABILITY_SECONDS = 30


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
        parts.append("BAT%d" % form_data["battles_required"])
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
