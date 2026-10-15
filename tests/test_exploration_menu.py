"""User navigation through route, stat, confirmation, trip and recall screens."""
from config import TDISPLAY_MENU_ICON_PATHS
from core.pet import Pet
from scripts.exploration_session import ExplorationSession


def session(species="rookie"):
    return ExplorationSession(Pet(species=species, state="live"), lambda _: True, lambda: 100000)


def test_explore_icon_sits_between_training_and_battle():
    icons = TDISPLAY_MENU_ICON_PATHS
    assert icons.index("/UIIcons/Explore.bmp") == icons.index("/UIIcons/Training.bmp") + 1
    assert icons.index("/UIIcons/Battle.bmp") == icons.index("/UIIcons/Explore.bmp") + 1
    assert len(icons) == 9


def test_jornada_requires_stat_then_explicit_departure():
    s = session()
    assert s.choices() == ("patio", "jornada", "noche", "back")
    s.input("next")
    s.input("action")
    assert s.page == "stats"
    s.input("next")
    s.input("next")
    s.input("action")
    assert s.page == "confirm" and s.stat == "off"
    assert not s.pet.exploration.away
    s.input("action")
    assert s.page == "trip" and s.pet.exploration.away


def test_return_is_explicit_and_back_never_claims():
    s = session()
    s.input("action")
    s.input("action")
    s.input("next")
    s.input("action")
    assert s.page == "recall" and s.index == 0
    s.input("back")
    assert s.page == "trip" and s.pet.exploration.away
    assert not s.input("back")
    assert s.pet.exploration.away


def test_six_stats_and_back_are_all_reachable_and_cancel_returns_to_route():
    s = session()
    s.index = 1
    s.input("action")
    visited = []
    for _ in range(7):
        visited.append(s.choices()[s.index])
        s.input("next")
    assert visited == ["hp", "mp", "off", "def", "spd", "brn", "back"]
    s.input("back")
    assert s.page == "routes" and s.index == 1
    s.input("action")
    s.index = 6
    s.input("action")
    assert s.page == "routes" and s.index == 1


def test_egg_and_baby_only_get_back():
    for species in ("egg", "baby"):
        s = session(species)
        assert s.choices() == ("back",)
        assert not s.input("action")
