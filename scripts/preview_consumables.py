"""Render isolated ES/EN inventory and Arena screenshots without player saves."""
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT))
from core.pet import Pet
from core.adopted_items import menu_index
from display_profiles import get_display_profile
from scripts.sim_renderer import render_frame
from scripts.practice_renderer import render_practice
from scripts.practice_session import PracticeSession


def previews(build_dir=ROOT / 'build-tdisplay', output=ROOT / 'out/consumables-runtime'):
    output.mkdir(parents=True, exist_ok=True)
    images = []
    for language in ('ES', 'EN'):
        pet = Pet(species='rookie', state='live')
        pet.language = language
        pet.dna = [91, 54, 32, 17]
        pet.adopted_inventory['training_manual'] = 1
        for page, selected in (('bag', 'small_recovery'), ('manual', 'training_manual')):
            image = render_frame(build_dir, pet, panel_mode='inventory',
                                 panel_index=menu_index(selected),
                                 profile=get_display_profile('tdisplay'))
            image.save(output / (language + '-' + page + '.png'))
            images.append(image)
        session = PracticeSession(pet, lambda _: True)
        session.battle.player.hp = 1
        session.battle.player.mp = 0
        session.page = 'items'
        image = render_practice(build_dir, session, 500)
        image.save(output / (language + '-arena-bag.png'))
        images.append(image)
        session.page, session.index = 'battle', 0
        session.battle.player.hp = session.battle.player.max_hp
        session.battle.player.mp = session.battle.player.max_mp
        session.battle.player.personality = 0
        session.battle.player.bond = 100
        session.battle.rival.hp = 1
        session._round(0, 500)
        image = render_practice(build_dir, session, 500)
        image.save(output / (language + '-reward.png'))
        images.append(image)
    gallery = Image.new('RGB', (960, 270))
    for i, image in enumerate(images):
        gallery.paste(image, ((i % 4) * 240, (i // 4) * 135))
    gallery.resize((1920, 540), Image.Resampling.NEAREST).save(output / 'gallery.png')


if __name__ == '__main__':
    previews()
