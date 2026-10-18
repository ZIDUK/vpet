"""Review the real Arena render at fixed times, without loading a player save."""
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from core.pet import Pet
from scripts.practice_session import PracticeSession
from scripts.practice_renderer import render_practice


def main():
    output = ROOT / "out/arena-review"
    output.mkdir(parents=True, exist_ok=True)
    build = ROOT / "build-tdisplay"
    for language in ("ES", "EN"):
        overview = Image.new("RGB", (720, 405))
        for row, species in enumerate(("rookie", "champion", "ultimate")):
            pet = Pet(species=species, state="live")
            pet.language = language
            session = PracticeSession(pet, lambda _: True)
            session.pet.techniques.training = 3
            session.pet.techniques.equipped = [0, 1]
            session.battle.player.hp = session.battle.rival.hp = 100
            session.battle.player.max_hp = session.battle.rival.max_hp = 100
            session.battle.player.mp = session.battle.rival.mp = 30
            session.battle.player.max_mp = session.battle.rival.max_mp = 30
            session.battle.player.stats = [50] * 6
            session.battle.rival.stats = [20] * 6
            session.battle.round = 1
            session.battle.actions, session.battle.damage = (1, 2), (8, 0)
            session.index = 2
            overview.paste(render_practice(build, session, 1200), (0, row * 135))
            overview.paste(render_practice(build, session, 500), (240, row * 135))
            frames = [render_practice(build, session, ms) for ms in range(0, 1450, 80)]
            frames[0].save(output / f"{species}-{language}-arena.gif", save_all=True,
                           append_images=frames[1:], duration=80, loop=0)
            session.battle.result = "VICTORIA"
            session.awarded = True
            overview.paste(render_practice(build, session, 500), (480, row * 135))
        overview.resize((1440, 810), Image.Resampling.NEAREST).save(output / f"arena-{language}.png")
    print(output)


if __name__ == "__main__":
    main()
