from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from core.collection import Collection
from core.pet import Pet
from core.profile import PetProfile
from scripts.collection_renderer import render_collection
from scripts.collection_session import CollectionSession
from scripts.sim_services import SimulatorServices

ROOT = Path(__file__).resolve().parents[1]


def scene(tmp_path, language="ES"):
    pets = []
    for word, role in ((2, "rookie"), (3, "champion")):
        pet = Pet(species=role, state="live")
        pet.profile = PetProfile.from_words((word, 1, 2, 3))
        pet.language = language
        pet.stats = {"hp": 100, "h": 90, "e": 90, "p": 90}
        pet.roll_dna(word)
        pets.append(pet)
    services = SimulatorServices(tmp_path)
    services.collection = Collection.from_pet(*pets)
    return CollectionSession(pets[0], services)


def flame_pixels(image, box):
    return sum(r > 120 and r > g * 1.15 and r > b * 1.4
               for r, g, b in image.crop(box).convert("RGB").getdata())


@pytest.mark.parametrize("language", ["ES", "EN"])
@pytest.mark.parametrize("page", ["enable", "detail", "founder", "activate", "breed"])
def test_visual_dialogs_show_large_real_creatures_without_writes(tmp_path, language, page):
    session = scene(tmp_path, language)
    session.page, session.pair = page, (0, 1)
    before = session.collection.encode()
    image = render_collection(ROOT / "build-tdisplay", session)
    assert image.size == (240, 135)
    if page == "breed":
        assert flame_pixels(image, (8, 25, 92, 100)) > 150
        assert flame_pixels(image, (150, 25, 234, 100)) > 150
    else:
        assert flame_pixels(image, (5, 22, 235, 105)) > 250
    assert session.collection.encode() == before


def test_collection_is_four_visible_places_not_a_scrolling_text_list(tmp_path):
    session = scene(tmp_path)
    session.collection.founder((9, 1, 2, 3), 17, confirmed=True, sequence=1)
    image = render_collection(ROOT / "build-tdisplay", session)
    for box in ((6, 24, 117, 64), (123, 24, 234, 64), (6, 66, 117, 106)):
        assert flame_pixels(image, box) > 40
    assert image.getpixel((123, 66)) != image.getpixel((122, 65))


def test_collection_uses_the_whole_atlas_cell_including_feet():
    from scripts.collection_renderer import _sprite
    from scripts.content_loader import definition_for
    build = ROOT / "build-tdisplay"
    clip = definition_for(build).clip("rookie", "idle", "training")
    with Image.open(build / clip["atlas"].lstrip("/")) as atlas:
        cell = atlas.crop((0, 0, atlas.height, atlas.height))
        expected = cell.convert("RGBA")
        expected.putalpha(cell.point([0] + [255] * 255, mode="L"))
    expected = expected.resize((clip["canvas"], clip["canvas"]), Image.Resampling.NEAREST)
    assert _sprite(build, "rookie").tobytes() == expected.tobytes()


def test_parent_selection_pins_one_parent_and_requires_a_second_confirmation(tmp_path):
    session = scene(tmp_path)
    before = session.collection.encode()
    session.index = 5
    session.input("action")
    assert session.page == "pairs" and len(session.choices()) == 5
    session.input("action")
    assert session.parent_a == 0 and session.page == "pairs"
    session.input("next")
    assert session.index == 1
    session.input("action")
    assert session.page == "breed" and session.pair == (0, 1) and session.index == 0
    session.input("action")
    assert session.collection.encode() == before


@pytest.mark.parametrize("language", ["ES", "EN"])
def test_labels_fit_and_hide_technical_migration_and_hex_ids(tmp_path, monkeypatch, language):
    session = scene(tmp_path, language)
    calls = []
    original = ImageDraw.ImageDraw.text

    def capture(draw, xy, value, *args, **kwargs):
        bounds = draw.textbbox(xy, value, font=kwargs.get("font"), anchor=kwargs.get("anchor"))
        assert 0 <= bounds[0] <= bounds[2] <= 240, (value, bounds)
        assert 0 <= bounds[1] <= bounds[3] <= 135, (value, bounds)
        calls.append(value)
        return original(draw, xy, value, *args, **kwargs)

    monkeypatch.setattr(ImageDraw.ImageDraw, "text", capture)
    session.pair = (0, 1)
    for page in ("enable", "list", "detail", "preferences", "pairs", "breed", "founder", "activate"):
        session.page = page
        render_collection(ROOT / "build-tdisplay", session)
    assert not any("MIGRAR" in value.upper() for value in calls)
    assert not any(session.pet.profile.pet_id in value for value in calls)
