"""Generate reproducible native-resolution previews without changing a save."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from PIL import Image
from core.pet import Pet
from scripts.practice_session import PracticeSession
from scripts.practice_renderer import render_practice
from scripts.practice_icons import INFO_ICONS, info_icon
from scripts.training_session import TrainingSession
from scripts.training_renderer import render_training


def main():
    pet = Pet()
    pet.complete_hatch("rookie", entropy=12345)
    session = PracticeSession(pet, lambda _: True)
    output = ROOT / "out" / "practice-preview"
    output.mkdir(parents=True, exist_ok=True)
    frames = {}

    def capture(name, now=0):
        frame = render_practice(ROOT / "build-tdisplay", session, now)
        frame.save(output / (name + ".png"))
        frames[name] = frame

    capture("battle-entry")
    # All teaching is reached through the dumbbell's technique lessons.
    training = TrainingSession(pet, lambda _: True)
    training.input("next", 0)
    render_training(ROOT / "build-tdisplay", training, 0).save(output / "training.png")
    training.input("action", 1000)
    render_training(ROOT / "build-tdisplay", training, 1800).save(output / "training-result.png")
    for _ in range(5):
        training.input("next", 3000)
    training.input("action", 3000)
    session = training.techniques
    capture("tech")
    session.input("next", 0)
    capture("locked")
    session.input("action", 0)
    capture("locked-detail")
    session.input("action", 0)
    session.input("action", 0)
    session.input("next", 0)
    session.input("action", 0)
    capture("flame")
    session.input("back", 0)
    capture("equipped")
    session = PracticeSession(pet, lambda _: True)
    capture("battle-ready", 1000)
    session.input("next", 1000)
    session.input("next", 1000)
    capture("battle-order", 1000)
    session.input("action", 1000)
    capture("battle", 1800)
    session.input("next", 2600)
    session.input("next", 2600)
    capture("battle-cooldown", 2600)
    session.input("action", 2600)
    capture("battle-changed-order", 3400)
    pet.techniques.equip(1)
    pet.techniques.equip(2)
    session = PracticeSession(pet, lambda _: True)
    session.input("next", 0)
    session.input("next", 0)
    session.input("action", 1000)
    capture("battle-block", 1800)
    sheet = Image.new("RGB", (480, 270))
    for i, name in enumerate(("battle-entry", "equipped", "battle-order", "battle-changed-order")):
        frame = frames[name]
        sheet.paste(frame, ((i % 2) * 240, (i // 2) * 135))
    sheet.resize((960, 540), Image.Resampling.NEAREST).save(output / "overview.png")
    training_sheet = Image.new("RGB", (480, 270))
    for i, name in enumerate(("training", "training-result", "battle-entry", "battle-block")):
        with Image.open(output / (name + ".png")) as frame:
            training_sheet.paste(frame, ((i % 2) * 240, (i // 2) * 135))
    training_sheet.resize((960, 540), Image.Resampling.NEAREST).save(output / "training-overview.png")
    # Export the generated glyphs for inspection and later firmware asset work.
    for name in INFO_ICONS:
        info_icon(name).save(output / ("icon-" + name + ".png"))
    print(output / "overview.png")


if __name__ == "__main__":
    main()
