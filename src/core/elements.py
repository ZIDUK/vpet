"""Elemental advantage rules shared by practice combat."""

ELEMENTS = frozenset((
    "fire", "plant", "water", "electric", "wind", "earth", "light", "dark", "neutral",
))

BEATS = {
    "fire": "plant",
    "plant": "water",
    "water": "fire",
    "electric": "wind",
    "wind": "earth",
    "earth": "electric",
    "light": "dark",
    "dark": "light",
}


def elemental_damage(base_damage, technique_element, target_element, guarding=False):
    """Apply Cyber Sleuth advantage, then the existing half-damage guard."""
    damage = max(1, int(base_damage))
    if BEATS.get(technique_element) == target_element:
        damage = damage * 3 // 2
    if guarding:
        damage = max(1, damage // 2)
    return damage
