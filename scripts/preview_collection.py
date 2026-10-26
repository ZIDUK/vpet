"""Render isolated collection fixtures; never reads or changes the user's save."""
import argparse
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from PIL import Image, ImageDraw, ImageFont
from core.pet import Pet
from core.profile import PetProfile
from core.collection import Collection
from scripts.sim_services import SimulatorServices
from scripts.collection_session import CollectionSession
from scripts.collection_renderer import render_collection


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "out/collection-preview.png")
    args = parser.parse_args()
    parents = []
    for index, species in ((2, "rookie"), (3, "champion")):
        pet = Pet(species=species, state="live")
        pet.profile = PetProfile.from_words((index, 1, 2, 3))
        pet.stats = {"hp": 100, "h": 90, "e": 90, "p": 90}
        pet.roll_dna(index)
        pet.learning.record(1, 0, 0, 2, 80)
        pet.learning.record(2, 2, 0, 1, 50)
        parents.append(pet)
    collection = Collection.from_pet(*parents)
    before_breeding = collection.encode()
    collection.breed(0, 1, (8, 9, 10, 11), 42, confirmed=True, sequence=1)
    gallery = Image.new("RGB", (1480, 1395), (8, 12, 13))
    draw = ImageDraw.Draw(gallery)
    with tempfile.TemporaryDirectory(prefix="vpet-collection-preview-") as temporary:
        services = SimulatorServices(temporary)
        services.collection = collection
        pages = ("list", "detail", "preferences", "founder", "pairs", "breed")
        for index, page in enumerate(pages):
            services.collection = Collection.decode(before_breeding) if page in ("pairs", "breed") else collection
            session = CollectionSession(parents[0], services)
            session.page = page
            session.target = 0
            x, y = (index % 2) * 740, (index // 2) * 465
            draw.text((x + 10, y + 10), page.upper(), fill="white", font=ImageFont.load_default(size=18))
            image = render_collection(ROOT / "build-tdisplay", session)
            gallery.paste(image.resize((720, 405), Image.Resampling.NEAREST), (x + 10, y + 40))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    gallery.save(args.output)
    print(args.output)


if __name__ == "__main__":
    main()
