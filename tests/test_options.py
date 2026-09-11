"""Behavior checks for the shared two-button options controller."""

from core.options import (
    OPTION_BACK,
    OPTION_DATE,
    OPTION_LANGUAGE,
    OPTION_LOAD,
    OPTION_SAVE,
    OPTION_SOUND,
    OPTION_TIME,
    OPTION_BLUETOOTH,
    OPTION_COUNT,
    OPTION_EVOLVE,
    OptionsSession,
)
from core.pet import Pet, STATE_LIVE


class FakeServices:
    def __init__(self):
        self.saved = None
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


def test_next_wraps_around_all_options():
    session = OptionsSession()
    for expected in range(OPTION_COUNT):
        assert session.index == expected
        session.next()
    assert session.index == OPTION_BLUETOOTH


def test_bluetooth_is_the_first_option():
    session = OptionsSession()
    assert session.index == OPTION_BLUETOOTH
    assert OPTION_BLUETOOTH == 0

    assert session.action(_pet(), FakeServices()) is True
    assert session.bluetooth_status == "ADVERTISING"


def test_bluetooth_option_toggles_advertising_state():
    session = OptionsSession()
    session.index = OPTION_BLUETOOTH

    assert session.action(_pet(), FakeServices()) is True
    assert session.bluetooth_enabled is True
    assert session.bluetooth_status == "ADVERTISING"

    session.action(_pet(), FakeServices())
    assert session.bluetooth_enabled is False
    assert session.bluetooth_status == "OFF"


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


def test_evolve_option_forces_next_form():
    pet = _pet()
    session = OptionsSession()
    session.index = OPTION_EVOLVE

    assert session.action(pet, FakeServices()) is True
    assert pet.species == "champion"
    assert session.message == "EVOLVED"

    session.action(pet, FakeServices())
    assert pet.species == "ultimate"
    session.action(pet, FakeServices())
    assert pet.species == "ultimate"
    assert session.message == "NO EVO"


def test_back_closes_options_panel():
    session = OptionsSession()
    session.index = OPTION_BACK

    assert session.action(_pet(), FakeServices()) is False
