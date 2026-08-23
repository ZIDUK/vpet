"""Persistence: load/save Pet state to /settings.toml as JSON.

CircuitPython 10 has settings.toml that's read-only at boot, but we use
a separate file /pet_save.json that lives on the FS. (settings.toml is
respected as the source of WiFi creds; runtime data goes to its own file.)

Format (JSON):
{
  "species": "agumon",
  "line": "agumon_line",
  "stats": {"h": 70, "e": 70, "p": 70, "hp": 70},
  "battles_won": 0
}
"""
import json

SAVE_PATH = "/pet_save.json"


def save_pet(pet):
    """Write pet state to disk."""
    try:
        with open(SAVE_PATH, "w") as f:
            f.write(json.dumps(pet.to_dict()))
    except OSError:
        pass  # silently fail if disk full / read-only


def load_pet(pet):
    """Load pet state from disk if exists. Returns True if loaded."""
    try:
        with open(SAVE_PATH, "r") as f:
            data = json.loads(f.read())
        pet.load_from_dict(data)
        return True
    except (OSError, ValueError):
        return False
