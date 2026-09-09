"""Two-button options menu state shared by simulator and CircuitPython."""

OPTION_LANGUAGE = 0
OPTION_SOUND = 1
OPTION_SAVE = 2
OPTION_LOAD = 3
OPTION_WIFI = 4
OPTION_DATE = 5
OPTION_TIME = 6
OPTION_BACK = 7
OPTION_COUNT = 8

PASSWORD_GROUPS = (
    ("UPPER", "ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
    ("LOWER", "abcdefghijklmnopqrstuvwxyz"),
    ("NUM", "0123456789"),
    ("SYM", "!@#$%^&*()-_=+[]{};:,.?/"),
)
PASSWORD_COMMANDS = ("MODE", "DEL", "CONNECT", "CANCEL")
MAX_WIFI_PASSWORD_LENGTH = 63


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
        self.networks = []
        self.values = []
        self.field = 0
        self.selected_ssid = ""
        self.password = ""
        self.password_group = 0
        self.password_key_index = 0
        self.network_status = "OFF"

    @property
    def password_keys(self):
        return tuple(PASSWORD_GROUPS[self.password_group][1]) + PASSWORD_COMMANDS

    @property
    def password_key(self):
        return self.password_keys[self.password_key_index]

    @property
    def password_group_label(self):
        return PASSWORD_GROUPS[self.password_group][0]

    def next(self):
        self.message = ""
        if self.mode == "options":
            self.index = (self.index + 1) % OPTION_COUNT
        elif self.mode == "wifi":
            self.index = (self.index + 1) % (len(self.networks) + 1)
        elif self.mode == "password":
            self.password_key_index = (
                self.password_key_index + 1
            ) % len(self.password_keys)
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
        if self.mode == "wifi":
            if self.index == len(self.networks):
                self.mode = "options"
                self.index = OPTION_WIFI
            else:
                self.selected_ssid = self.networks[self.index]
                self.password = ""
                self.password_group = 0
                self.password_key_index = 0
                self.mode = "password"
            return True
        if self.mode == "password":
            key = self.password_key
            if key == "MODE":
                self.password_group = (self.password_group + 1) % len(PASSWORD_GROUPS)
                self.password_key_index = 0
            elif key == "DEL":
                self.password = self.password[:-1]
            elif key == "CONNECT":
                self.message = services.connect_wifi(self.selected_ssid, self.password)
                self.network_status = (
                    "ONLINE" if self.message in ("ONLINE", "SIM ONLINE") else "NO INTERNET"
                )
                self.password = ""
                self.mode = "options"
                self.index = OPTION_WIFI
            elif key == "CANCEL":
                self.password = ""
                self.mode = "wifi"
                self.index = 0
            elif len(self.password) < MAX_WIFI_PASSWORD_LENGTH:
                self.password += key
            else:
                self.message = "MAX 63"
            return True
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
        elif self.index == OPTION_WIFI:
            self.networks = services.scan_wifi()
            self.mode = "wifi"
            self.index = 0
            self.message = "NO NETWORKS" if not self.networks else ""
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
        elif self.index == OPTION_BACK:
            return False
        return True
