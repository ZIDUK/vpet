"""Behavior checks for the shared two-button options controller."""

from core.options import (
    OPTION_BACK,
    OPTION_DATE,
    OPTION_LANGUAGE,
    OPTION_LOAD,
    OPTION_SAVE,
    OPTION_SOUND,
    OPTION_TIME,
    OPTION_WIFI,
    OptionsSession,
)
from core.pet import Pet, STATE_LIVE
from scripts.sim_services import SimulatorServices


class FakeServices:
    def __init__(self):
        self.saved = None
        self.connected = None
        self.date = (2026, 9, 5)
        self.time = (10, 15)

    def save(self, pet):
        self.saved = pet.to_dict()
        return True

    def load(self, pet):
        if self.saved is None:
            return False
        pet.load_from_dict(self.saved)
        return True

    def scan_wifi(self):
        return ["HOME", "PHONE"]

    def connect_wifi(self, ssid, password):
        self.connected = (ssid, password)
        return "ONLINE"

    def get_datetime(self):
        return (*self.date, *self.time)

    def set_date(self, year, month, day):
        self.date = (year, month, day)

    def set_time(self, hour, minute):
        self.time = (hour, minute)


def _pet():
    return Pet(species="rookie", state=STATE_LIVE)


def test_language_and_sound_are_toggled():
    pet = _pet()
    services = FakeServices()
    session = OptionsSession()

    session.index = OPTION_LANGUAGE
    assert session.action(pet, services) is True
    session.index = OPTION_SOUND
    assert session.action(pet, services) is True

    assert pet.language == "ES"
    assert pet.sound_enabled is False


def test_save_and_load_restore_current_pet_state():
    pet = _pet()
    services = FakeServices()
    session = OptionsSession()
    pet.stats["hp"] = 81

    session.index = OPTION_SAVE
    session.action(pet, services)
    pet.stats["hp"] = 12
    session.index = OPTION_LOAD
    session.action(pet, services)

    assert pet.stats["hp"] == 81
    assert session.message == "LOADED"


def test_wifi_selection_opens_password_editor():
    pet = _pet()
    services = FakeServices()
    session = OptionsSession()
    session.index = OPTION_WIFI

    session.action(pet, services)
    assert session.mode == "wifi"
    assert session.networks == ["HOME", "PHONE"]
    session.next()
    session.action(pet, services)

    assert session.mode == "password"
    assert session.selected_ssid == "PHONE"
    assert services.connected is None


def test_password_editor_types_changes_mode_deletes_and_connects():
    pet = _pet()
    services = FakeServices()
    session = OptionsSession()
    session.networks = ["HOME"]
    session.mode = "wifi"

    session.action(pet, services)
    session.action(pet, services)  # A
    session.password_key_index = len(session.password_keys) - 4  # MODE
    session.action(pet, services)
    session.password_key_index = 1
    session.action(pet, services)  # b
    session.password_key_index = len(session.password_keys) - 3  # DEL
    session.action(pet, services)
    session.password_key_index = len(session.password_keys) - 2  # CONNECT
    session.action(pet, services)

    assert services.connected == ("HOME", "A")
    assert session.mode == "options"
    assert session.message == "ONLINE"
    assert session.password == ""


def test_password_editor_can_enter_lowercase_numbers_and_symbols():
    session = OptionsSession()
    session.mode = "password"
    session.selected_ssid = "HOME"

    for group, character in ((1, "z"), (2, "7"), (3, "!")):
        session.password_group = group
        session.password_key_index = session.password_keys.index(character)
        session.action(_pet(), FakeServices())

    assert session.password == "z7!"


def test_date_editor_changes_each_field_then_commits():
    pet = _pet()
    services = FakeServices()
    session = OptionsSession()
    session.index = OPTION_DATE

    session.action(pet, services)
    session.next()
    session.action(pet, services)
    session.next()
    session.action(pet, services)
    session.next()
    session.action(pet, services)

    assert services.date == (2027, 10, 6)
    assert session.mode == "options"
    assert session.index == OPTION_DATE


def test_time_editor_wraps_hours_and_commits():
    pet = _pet()
    services = FakeServices()
    services.time = (23, 59)
    session = OptionsSession()
    session.index = OPTION_TIME

    session.action(pet, services)
    session.next()
    session.action(pet, services)
    session.next()
    session.action(pet, services)

    assert services.time == (0, 0)
    assert session.mode == "options"


def test_back_closes_options_panel():
    session = OptionsSession()
    session.index = OPTION_BACK

    assert session.action(_pet(), FakeServices()) is False


def test_simulator_saves_wifi_password_and_auto_reconnects(tmp_path, monkeypatch):
    services = SimulatorServices(tmp_path)
    monkeypatch.setattr(services, "_has_internet", lambda: True)

    assert services.connect_wifi("HOME", "Secret7!") == "SIM ONLINE"
    assert services.wifi_path.read_text() == '{"ssid": "HOME", "password": "Secret7!"}'

    restored = SimulatorServices(tmp_path)
    monkeypatch.setattr(restored, "_has_internet", lambda: True)
    assert restored.auto_connect() == "SIM ONLINE"
    assert restored.connected_ssid == "HOME"
