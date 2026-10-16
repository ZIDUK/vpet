"""Generate isolated ES/EN journey previews without touching the player's save."""
import argparse
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))
from core.pet import Pet
from display_profiles import get_display_profile
from scripts.exploration_session import ExplorationSession
from scripts.sim_renderer import render_frame


def previews(build_dir, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    images = []
    for language in ("ES", "EN"):
        for page in ("routes", "stats", "confirm", "trip", "ready", "recall", "receipt"):
            pet = Pet(species="champion", state="live")
            pet.language = language
            now = 100000
            session = ExplorationSession(pet, lambda _: True, lambda: now)
            session.route, session.stat = "jornada", "off"
            session.page = page
            if page in ("trip", "ready", "recall", "receipt"):
                pet.exploration.start(pet, "jornada", "off", now - (14400 if page in ("trip", "recall") else 28800))
            if page == "ready":
                session.page = "trip"
            if page == "receipt":
                pet.exploration.claim(pet, now)
            image = render_frame(build_dir, pet, menu_index=3, panel_mode="explore",
                                 exploration_menu=session, profile=get_display_profile("tdisplay"))
            image.save(output / (language + "-" + page + ".png"))
            images.append(image)
    gallery = Image.new("RGB", (240 * 7, 135 * 2))
    for i, image in enumerate(images):
        gallery.paste(image, ((i % 7) * 240, (i // 7) * 135))
    gallery.resize((1680, 270)).save(output / "gallery.png")
    layout = Image.new('RGB', (720, 270))
    for row, language in enumerate(('ES', 'EN')):
        for column, page in enumerate(('routes', 'stats', 'confirm')):
            with Image.open(output / (language + '-' + page + '.png')) as panel:
                layout.paste(panel, (column * 240, row * 135))
    layout.resize((1440, 540), Image.Resampling.NEAREST).save(output / 'layout.png')
    returns = Image.new('RGB', (720, 270))
    for row, language in enumerate(('ES', 'EN')):
        for column, page in enumerate(('ready', 'recall', 'receipt')):
            with Image.open(output / (language + '-' + page + '.png')) as panel:
                returns.paste(panel, (column * 240, row * 135))
    returns.resize((1440, 540), Image.Resampling.NEAREST).save(output / 'returns.png')
    return images


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-dir", type=Path, default=ROOT / "build-tdisplay")
    parser.add_argument("--output", type=Path, default=ROOT / "out" / "exploration-previews")
    args = parser.parse_args()
    previews(args.build_dir, args.output)
