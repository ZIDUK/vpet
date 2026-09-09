"""Evolution rules.

Each Digimon in a line has a JSON file in src/data/digimon/ with:
  - evolves_to: next form name (or null if final)
  - requirements: {stat: min_value, ...} that must be met
  - min_age_seconds: minimum age before evolution can trigger
  - battles_required: number of battles won required (0 = no requirement)

When Pet stats meet the current form's requirements for >= STABILITY_SECONDS,
evolution triggers.
"""
import time

# How long stats must be above thresholds before evolution triggers.
# Prevents random spikes from triggering premature evolution.
STABILITY_SECONDS = 30


class Evolution:
    def __init__(self, registry):
        """registry: dict of form_name -> {evolves_to, requirements, ...}"""
        self.registry = registry

    def check(self, pet):
        """Returns (new_form, reason) if evolution is ready, else (None, None)."""
        form_data = self.registry.get(pet.species)
        if not form_data:
            return (None, None)
        if not form_data.get("automatic", True):
            return (None, None)
        next_form = form_data.get("evolves_to")
        if not next_form:
            return (None, None)  # already at final form

        # Age check
        min_age = form_data.get("min_age_seconds", 0)
        if pet.age_seconds < min_age:
            return (None, None)

        # Stat check
        requirements = form_data.get("requirements", {})
        for stat, min_val in requirements.items():
            if pet.get(stat) < min_val:
                return (None, None)

        # Battles check
        battles_required = form_data.get("battles_required", 0)
        if pet.battles_won < battles_required:
            return (None, None)

        return (next_form, "stats + age + battles met")

    def evolve(self, pet):
        """Trigger evolution. Returns True if evolved, False otherwise."""
        new_form, reason = self.check(pet)
        if new_form:
            self._apply(pet, new_form)
            return True
        return False

    def force(self, pet):
        """Evolve to the registered next form without checking requirements."""
        form_data = self.registry.get(pet.species, {})
        new_form = form_data.get("evolves_to")
        if not new_form:
            return False
        self._apply(pet, new_form)
        return True

    @staticmethod
    def _apply(pet, new_form):
        pet.species = new_form
        for stat in pet.stats:
            pet.stats[stat] = min(100, pet.stats[stat] + 10)
