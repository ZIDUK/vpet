"""Small pixel-art status panel shared by CircuitPython and Pillow."""
from config import EVOLUTION_REGISTRY
from core.evolution import format_requirements

STATUS_WIDTH = 128
STATUS_HEIGHT = 112
STATUS_COLORS = (
    0x171820,  # frame
    0xD2AD6B,  # parchment
    0xF4DFA7,  # parchment highlight
    0xCB4B43,  # HP
    0xE89B3C,  # hunger
    0x4B9AC8,  # energy
    0x65AD59,  # mood
    0x4E3D32,  # ink
    0xFFD24A,  # selector
)

FONT = {
    " ": ("000",) * 5,
    "-": ("000", "000", "111", "000", "000"),
    "*": ("000", "101", "010", "101", "000"),
    "=": ("000", "111", "000", "111", "000"),
    "<": ("001", "010", "100", "010", "001"),
    ":": ("000", "010", "000", "010", "000"),
    "/": ("001", "001", "010", "100", "100"),
    ">": ("100", "010", "001", "010", "100"),
    "0": ("111", "101", "101", "101", "111"),
    "1": ("010", "110", "010", "010", "111"),
    "2": ("111", "001", "111", "100", "111"),
    "3": ("111", "001", "111", "001", "111"),
    "4": ("101", "101", "111", "001", "001"),
    "5": ("111", "100", "111", "001", "111"),
    "6": ("111", "100", "111", "101", "111"),
    "7": ("111", "001", "010", "010", "010"),
    "8": ("111", "101", "111", "101", "111"),
    "9": ("111", "101", "111", "001", "111"),
    "A": ("010", "101", "111", "101", "101"),
    "B": ("110", "101", "110", "101", "110"),
    "C": ("111", "100", "100", "100", "111"),
    "D": ("110", "101", "101", "101", "110"),
    "E": ("111", "100", "110", "100", "111"),
    "F": ("111", "100", "110", "100", "100"),
    "G": ("111", "100", "101", "101", "111"),
    "H": ("101", "101", "111", "101", "101"),
    "I": ("111", "010", "010", "010", "111"),
    "J": ("001", "001", "001", "101", "111"),
    "K": ("101", "101", "110", "101", "101"),
    "L": ("100", "100", "100", "100", "111"),
    "M": ("101", "111", "111", "101", "101"),
    "N": ("101", "111", "111", "111", "101"),
    "O": ("111", "101", "101", "101", "111"),
    "P": ("110", "101", "110", "100", "100"),
    "Q": ("111", "101", "101", "111", "001"),
    "R": ("110", "101", "110", "101", "101"),
    "S": ("111", "100", "111", "001", "111"),
    "T": ("111", "010", "010", "010", "010"),
    "U": ("101", "101", "101", "101", "111"),
    "V": ("101", "101", "101", "101", "010"),
    "W": ("101", "101", "111", "111", "101"),
    "X": ("101", "101", "010", "101", "101"),
    "Y": ("101", "101", "010", "010", "010"),
}


def _fill(target, x, y, width, height, color):
    for py in range(y, y + height):
        for px in range(x, x + width):
            target[px, py] = color


def _text_width(value, scale=1):
    return max(0, len(value) * 4 * scale - scale)


def _text(target, x, y, value, color=7, scale=1):
    cursor = x
    for character in value.upper():
        glyph = FONT.get(character, FONT[" "])
        for row, bits in enumerate(glyph):
            for column, bit in enumerate(bits):
                if bit == "1":
                    _fill(target, cursor + column * scale, y + row * scale, scale, scale, color)
        cursor += 4 * scale


def _bar(target, y, label, value, color):
    value = max(0, min(100, int(value)))
    _text(target, 6, y + 1, label)
    _fill(target, 25, y, 73, 8, 0)
    _fill(target, 27, y + 2, 69, 4, 2)
    _fill(target, 27, y + 2, 69 * value // 100, 4, color)
    number = str(value)
    _text(target, 121 - _text_width(number), y + 1, number)


def draw_status(target, pet, age_seconds=None):
    """Draw into an object supporting target[x, y] = palette_index."""
    if age_seconds is None:
        age_seconds = int(pet.age_seconds)
    age_seconds = max(0, int(age_seconds))

    _fill(target, 0, 0, STATUS_WIDTH, STATUS_HEIGHT, 0)
    _fill(target, 3, 3, STATUS_WIDTH - 6, STATUS_HEIGHT - 6, 1)
    _fill(target, 5, 5, STATUS_WIDTH - 10, 13, 0)
    _text(target, (STATUS_WIDTH - _text_width("STATUS", 2)) // 2, 6, "STATUS", 2, 2)

    spanish = pet.language == "ES"
    form = {
        "champion": "FLAMEMON",
        "ultimate": "DRAGFIREMON",
    }.get(pet.species, "FIREMON")
    _text(target, (STATUS_WIDTH - _text_width(form)) // 2, 21, form, 7)
    _bar(target, 31, "HP", pet.stats["hp"], 3)
    _bar(target, 44, "HUN", pet.stats["h"], 4)
    _bar(target, 57, "ENR", pet.stats["e"], 5)
    _bar(target, 70, "MOO", pet.stats["p"], 6)

    stage_age = int(getattr(pet, "stage_age_seconds", age_seconds))
    minutes = min(99, stage_age // 60)
    seconds = stage_age % 60
    age_label = "EDAD" if spanish else "AGE"
    battles_label = "BATALLAS" if spanish else "BATTLES"
    cm_label = "CM %02d" % min(99, getattr(pet, "care_mistakes", 0))
    call = getattr(pet, "call_reason", None)
    if call == "hunger":
        call_label = "LLAM HAM" if spanish else "CALL HUN"
    elif call == "strength":
        call_label = "LLAM FUE" if spanish else "CALL STR"
    else:
        call_label = ""
    _text(target, 8, 84, "%s %02d:%02d %s" % (age_label, minutes, seconds, cm_label), 7)
    _text(target, 8, 93, "%s %02d" % (battles_label, min(99, getattr(pet, "battles_this_form", pet.battles_won))), 7)
    if call_label:
        _text(target, 8, 102, call_label, 7)


def _panel(target, title):
    _fill(target, 0, 0, STATUS_WIDTH, STATUS_HEIGHT, 0)
    _fill(target, 3, 3, STATUS_WIDTH - 6, STATUS_HEIGHT - 6, 1)
    _fill(target, 5, 5, STATUS_WIDTH - 10, 13, 0)
    _text(target, (STATUS_WIDTH - _text_width(title, 2)) // 2, 6, title, 2, 2)


def draw_inventory(target, pet, selected_index=0):
    """Draw the selectable consumables list and its current quantities."""
    from core.inventory import (
        INVENTORY_ITEMS,
        clamp_visible_inventory_index,
        visible_inventory_indexes,
    )

    spanish = pet.language == "ES"
    _panel(target, "INVENTARIO" if spanish else "INVENTORY")
    names = ("CARNE", "ENERGIA", "EXP", "ANILLO") if spanish else ("MEAT", "ENERGY", "EXP", "RING")
    visible = visible_inventory_indexes(pet)
    current = clamp_visible_inventory_index(pet, selected_index)
    selected_slot = visible.index(current) if current in visible else 0
    window_start = 0 if selected_slot < 4 else selected_slot - 3
    for slot, index in enumerate(visible[window_start:window_start + 4]):
        y = 24 + slot * 20
        border = 8 if index == current else 0
        _fill(target, 8, y, 112, 16, border)
        _fill(target, 10, y + 2, 108, 12, 2)
        if index < len(INVENTORY_ITEMS):
            _, key, _, _ = INVENTORY_ITEMS[index]
            _text(target, 15, y + 5, names[index], 7)
            _text(target, 96, y + 5, "X%02d" % min(99, pet.inventory.get(key, 0)), 7)
        else:
            _text(target, 15, y + 5, "VOLVER" if spanish else "BACK", 7)


def draw_evolution_guide(target, pet):
    """Draw the known evolution line and highlight the current form."""
    spanish = pet.language == "ES"
    title = "EVOLUCION" if spanish else "EVOLUTION"
    line_label = "TU LINEA" if spanish else "YOUR LINE"
    _panel(target, title)
    _text(target, (STATUS_WIDTH - _text_width(line_label)) // 2, 22, line_label, 7)

    stages = ("rookie", "champion", "ultimate")
    card_x = (2, 45, 88)
    names = ("FIRE", "FLAME", "DRAG")
    for index, stage in enumerate(stages):
        x = card_x[index]
        _fill(target, x, 31, 38, 43, 8 if pet.species == stage else 0)
        _fill(target, x + 2, 33, 34, 39, 2)
        _text(target, x + 10, 65, names[index], 7)
    _text(target, 40, 46, ">", 7)
    _text(target, 83, 46, ">", 7)

    prefix = "ACTUAL" if spanish else "CURRENT"
    current_name = {
        "baby": "SPARKMON",
        "champion": "FLAMEMON",
        "ultimate": "DRAGFIREMON",
    }.get(pet.species, "FIREMON")
    current = "%s %s" % (prefix, current_name)
    _text(target, (STATUS_WIDTH - _text_width(current)) // 2, 77, current, 7)
    form = EVOLUTION_REGISTRY.get(pet.species, {})
    text = format_requirements(form, spanish)
    if text:
        words = text.split()
        _text(target, 7, 94, " ".join(words[:3]), 7)
        if len(words) > 3:
            _text(target, 7, 103, " ".join(words[3:]), 7)


def draw_options(target, pet, session, current_datetime):
    """Draw the main options list."""
    spanish = pet.language == "ES"
    labels = (
        ("BLE", "IDIOMA", "SONIDO", "GUARDAR", "CARGAR", "FECHA", "HORA", "EVO", "VOLVER")
        if spanish
        else ("BLE", "LANGUAGE", "SOUND", "SAVE", "LOAD", "DATE", "TIME", "EVOLVE", "BACK")
    )
    _panel(target, "OPTIONS")
    year, month, day, hour, minute = current_datetime
    values = (
        session.bluetooth_status,
        pet.language,
        ("SI" if pet.sound_enabled else "NO") if spanish else ("ON" if pet.sound_enabled else "OFF"),
        "",
        "",
        "%02d-%02d-%02d" % (year % 100, month, day),
        "%02d:%02d" % (hour, minute),
        "",
        "",
    )
    for index, label in enumerate(labels):
        y = 16 + index * 9
        if index == session.index:
            _fill(target, 6, y, 116, 9, 8)
            _fill(target, 8, y + 1, 112, 7, 2)
        _text(target, 11, y + 2, label, 7)
        value = values[index]
        if value:
            _text(target, 116 - _text_width(value), y + 2, value, 7)
    if session.message:
        message = session.message[:24]
        _text(target, (STATUS_WIDTH - _text_width(message)) // 2, 102, message, 7)


def draw_datetime_editor(target, pet, session):
    """Draw date or time values and highlight the field being edited."""
    spanish = pet.language == "ES"
    is_date = session.mode == "date"
    title = ("FECHA" if spanish else "DATE") if is_date else ("HORA" if spanish else "TIME")
    _panel(target, title)
    if is_date:
        values = ("%04d" % session.values[0], "%02d" % session.values[1], "%02d" % session.values[2])
        labels = ("ANO", "MES", "DIA") if spanish else ("YEAR", "MON", "DAY")
        positions = (20, 63, 91)
    else:
        values = ("%02d" % session.values[0], "%02d" % session.values[1])
        labels = ("HORA", "MIN") if spanish else ("HOUR", "MIN")
        positions = (40, 76)
    for index, value in enumerate(values):
        x = positions[index]
        width = _text_width(value, 2) + 6
        _fill(target, x - 3, 38, width, 17, 8 if index == session.field else 0)
        _fill(target, x - 1, 40, width - 4, 13, 2)
        _text(target, x, 41, value, 7, 2)
        _text(target, x, 62, labels[index], 7)
    instruction = "N CAMBIA A SIG" if spanish else "N CHANGE A NEXT"
    _text(target, (STATUS_WIDTH - _text_width(instruction)) // 2, 88, instruction, 7)
