from core.pet import Pet
from scripts.sim_services import SimulatorServices


def test_collection_option_keeps_existing_ids_and_opens_without_migration(tmp_path):
    from core.options import OPTION_BACK, OPTION_PAUSE, OPTION_COLLECTION, OPTION_ORDER, OptionsSession
    assert (OPTION_BACK, OPTION_PAUSE, OPTION_COLLECTION) == (8, 9, 10)
    assert OPTION_ORDER[-3:] == (9, 10, 8)
    services = SimulatorServices(tmp_path)
    pet = Pet()
    assert services.start(pet)
    session = OptionsSession()
    session.index = OPTION_COLLECTION
    assert session.action(pet, services)
    assert session.message == "COLLECTION"
    assert services.collection is None


def test_collection_menu_requires_separate_confirmation_for_founder(tmp_path):
    from scripts.collection_session import CollectionSession
    services = SimulatorServices(tmp_path)
    pet = Pet()
    assert services.start(pet)
    session = CollectionSession(pet, services)
    assert session.page == "enable"
    assert session.input("next")
    assert session.input("action")
    assert session.page == "list" and services.collection is not None
    session.index = 1
    assert session.input("action")
    assert session.page == "founder"
    assert len(services.collection.slots) == 1
    assert session.input("back")
    assert len(services.collection.slots) == 1
    session.index = 1
    session.input("action")
    session.input("next")
    session.input("action")
    assert len(services.collection.slots) == 2


def test_collection_render_is_read_only_and_uses_real_portraits(tmp_path):
    from scripts.collection_session import CollectionSession
    from scripts.collection_renderer import render_collection
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    services = SimulatorServices(tmp_path)
    pet = Pet()
    assert services.start(pet) and services.enable_collection(pet, confirmed=True)
    session = CollectionSession(pet, services)
    before = services.collection.encode()
    image = render_collection(root / "build-tdisplay", session)
    assert image.size == (240, 135)
    assert len(image.getcolors(240 * 135) or ()) > 20
    assert services.collection.encode() == before
