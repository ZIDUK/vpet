"""Two-button options menu state shared by simulator and CircuitPython."""

OPTION_BLUETOOTH = 0
OPTION_LANGUAGE = 1
OPTION_SOUND = 2
OPTION_SAVE = 3
OPTION_LOAD = 4
OPTION_DATE = 5
OPTION_TIME = 6
OPTION_EVOLVE = 7
OPTION_BACK = 8
OPTION_COUNT = 9
OPTION_ICONS = (
    "Bluetooth",
    "Language",
    "Sound",
    "Save",
    "Load",
    "Date",
    "Clock",
    "Evolve",
    "Back",
)

_NEXT_FORM = {
    "egg": "baby",
    "baby": "rookie",
    "rookie": "champion",
    "champion": "ultimate",
}


def force_next_form(pet):
    if pet.species == "ultimate":
        pet.reset_to_egg()
        return True
    nxt = _NEXT_FORM.get(pet.species)
    if not nxt:
        return False
    if pet.species == "egg":
        pet.complete_hatch(nxt)
    else:
        from core.evolution import Evolution
        Evolution._apply(pet, nxt)
    return True


def _days_in_month(year, month):
    if month == 2:
        leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
        return 29 if leap else 28
    return 30 if month in (4, 6, 9, 11) else 31


class OptionsSession:
    def __init__(self):
        self.mode = "options"
        self.index = 0
        self.message = ""
        self.values = []
        self.field = 0
        self.bluetooth_enabled = False
        self.bluetooth_status = "OFF"

    def next(self):
        self.message = ""
        if self.mode == "options":
            self.index = (self.index + 1) % OPTION_COUNT
        elif self.mode == "date":
            year, month, day = self.values
            if self.field == 0:
                year = 2024 if year >= 2099 else year + 1
            elif self.field == 1:
                month = 1 if month >= 12 else month + 1
            else:
                maximum = _days_in_month(year, month)
                day = 1 if day >= maximum else day + 1
            self.values = [year, month, min(day, _days_in_month(year, month))]
        elif self.mode == "time":
            if self.field == 0:
                self.values[0] = (self.values[0] + 1) % 24
            else:
                self.values[1] = (self.values[1] + 1) % 60

    def action(self, pet, services):
        self.message = ""
        if self.mode in ("date", "time"):
            field_count = 3 if self.mode == "date" else 2
            if self.field < field_count - 1:
                self.field += 1
            else:
                if self.mode == "date":
                    services.set_date(*self.values)
                    self.index = OPTION_DATE
                else:
                    services.set_time(*self.values)
                    self.index = OPTION_TIME
                self.mode = "options"
                self.message = "UPDATED"
            return True

        if self.index == OPTION_LANGUAGE:
            pet.language = "ES" if pet.language == "EN" else "EN"
        elif self.index == OPTION_SOUND:
            pet.sound_enabled = not pet.sound_enabled
        elif self.index == OPTION_SAVE:
            self.message = "SAVED" if services.save(pet) else "SAVE ERROR"
        elif self.index == OPTION_LOAD:
            self.message = "LOADED" if services.load(pet) else "NO SAVE"
        elif self.index == OPTION_BLUETOOTH:
            self.bluetooth_enabled = not self.bluetooth_enabled
            self.bluetooth_status = "ADVERTISING" if self.bluetooth_enabled else "OFF"
        elif self.index == OPTION_DATE:
            year, month, day, _, _ = services.get_datetime()
            self.values = [year, month, day]
            self.field = 0
            self.mode = "date"
        elif self.index == OPTION_TIME:
            _, _, _, hour, minute = services.get_datetime()
            self.values = [hour, minute]
            self.field = 0
            self.mode = "time"
        elif self.index == OPTION_EVOLVE:
            self.message = "EVOLVED" if force_next_form(pet) else "NO EVO"
        elif self.index == OPTION_BACK:
            return False
        return True
