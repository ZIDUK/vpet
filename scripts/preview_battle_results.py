"""Render result reactions and navigation icons without touching player saves."""
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from core.pet import Pet
from scripts.practice_session import PracticeSession
from scripts.practice_renderer import render_practice
from scripts.sim_renderer import render_frame
from display_profiles import get_display_profile


def main():
    output = ROOT / "out/battle-result-review"
    output.mkdir(parents=True, exist_ok=True)
    build = ROOT / "build-tdisplay"
    gallery = Image.new("RGB", (720, 270))
    for row, language in enumerate(("ES", "EN")):
        pet = Pet(species="rookie", state="live")
        pet.language = language
        for column, result in enumerate(("VICTORIA", "DERROTA", "EMPATE")):
            session = PracticeSession(pet, lambda _: True)
            session.awarded = True
            session.battle.round = 30 if result == "EMPATE" else 10
            if result == "VICTORIA":
                session.battle.rival.hp = 0
                session.battle.player.hp = min(38, session.battle.player.max_hp)
            elif result == "DERROTA":
                session.battle.player.hp = 0
                session.battle.rival.hp = 32
            session.battle.result = result
            session.reward_item = "small_recovery" if result == "VICTORIA" else None
            frames = [render_practice(build, session, i * 100) for i in range(15)]
            frames[0].save(output / (language + "-" + result + ".png"))
            frames[0].resize((720, 405), Image.Resampling.NEAREST).save(
                output / (language + "-" + result + "-large.png"))
            frames[0].save(output / (language + "-" + result + ".gif"),
                           save_all=True, append_images=frames[1:], duration=100,
                           loop=0, disposal=2)
            gallery.paste(frames[0], (column * 240, row * 135))
    gallery.resize((1440, 540), Image.Resampling.NEAREST).save(output / "results.png")
    home = render_frame(build, pet, now_ms=0, profile=get_display_profile("tdisplay"))
    home.crop((0, 0, 240, 24)).resize((960, 96), Image.Resampling.NEAREST).save(output / "menu.png")
    tiles = Image.new("RGB", (40, 20))
    for x, name in ((0, "Explore"), (20, "Back")):
        with Image.open(build / "UIIcons" / (name + ".bmp")) as icon:
            tiles.paste(icon.convert("RGB"), (x, 0))
    tiles.resize((320, 160), Image.Resampling.NEAREST).save(output / "icons.png")
    print(output)


if __name__ == "__main__":
    main()
