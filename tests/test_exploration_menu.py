"""Exploration icon and its internal routes in the simulator menu."""
from config import TDISPLAY_MENU_ICON_PATHS
from core.exploration_menu import ExplorationMenu


def test_explore_icon_sits_between_training_and_battle():
    icons = TDISPLAY_MENU_ICON_PATHS
    training = icons.index("/UIIcons/Training.bmp")
    explore = icons.index("/UIIcons/Explore.bmp")
    battle = icons.index("/UIIcons/Battle.bmp")
    assert explore == training + 1
    assert battle == explore + 1
    assert len(icons) == 9


def test_routes_are_patio_jornada_and_night():
    menu = ExplorationMenu()
    assert [row["id"] for row in menu.rows()] == ["patio", "jornada", "noche", "back"]
    assert menu.rows(spanish=True)[0]["label"] == "PATIO"
    assert menu.rows(spanish=True)[0]["detail"] == "30M"
    assert menu.rows(spanish=True)[1]["detail"] == "8H"


def test_jornada_opens_the_six_stats_and_remembers_the_choice():
    menu = ExplorationMenu()
    menu.index = 1
    assert menu.action() == "stats"
    assert [row["id"] for row in menu.rows()][:6] == [
        "hp", "mp", "off", "def", "spd", "brn",
    ]
    menu.index = 2
    assert menu.action() == ("jornada", "off")
    assert menu.choice == ("jornada", "off")
    assert menu.page == "routes"


def test_egg_and_baby_only_get_back():
    menu = ExplorationMenu(species="egg")
    assert [row["id"] for row in menu.rows()] == ["back"]
    menu = ExplorationMenu(species="baby")
    assert menu.action() == "back"
    menu = ExplorationMenu(species="rookie")
    menu.index = 0
    assert menu.action() == ("patio", None)
