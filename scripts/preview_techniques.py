"""Review the expanded equipment UI without modifying a player save."""
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]

from core.pet import Pet
from scripts.practice_session import PracticeSession
from scripts.practice_renderer import render_practice


def main():
    output = ROOT / 'out/technique-review'
    output.mkdir(parents=True, exist_ok=True)
    for language in ('ES', 'EN'):
        sheet = Image.new('RGB', (720, 405))
        for row, (species, equipped, selected) in enumerate((
                ('rookie', [0, 1], 1), ('champion', [0, 1, 3], 3),
                ('ultimate', [0, 1, 3, 4], 4))):
            pet = Pet(species=species, state='live')
            pet.language = language
            pet.techniques.training = 6
            pet.techniques.equipped = equipped
            session = PracticeSession(pet, lambda _: True, training=True)
            session.index = selected
            sheet.paste(render_practice(ROOT / 'build-tdisplay', session, 800), (0, row * 135))
            session.page, session.tech, session.index = 'detail', selected, 1
            sheet.paste(render_practice(ROOT / 'build-tdisplay', session, 800), (240, row * 135))
            arena = PracticeSession(pet, lambda _: True)
            arena.index = len(equipped)
            sheet.paste(render_practice(ROOT / 'build-tdisplay', arena, 800), (480, row * 135))
        sheet.resize((1440, 810), Image.Resampling.NEAREST).save(output / ('techniques-' + language + '.png'))
    print(output)


if __name__ == '__main__':
    main()
