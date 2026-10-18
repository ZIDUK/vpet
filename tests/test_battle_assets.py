from PIL import Image, ImageDraw

from scripts.battle_assets import normalize_frames


def test_attack_and_idle_keep_same_body_scale_and_ground_without_frame_pumping():
    def frames(height):
        result = []
        for dx in (0, 8):
            im = Image.new("RGBA", (88, 88))
            ImageDraw.Draw(im).rectangle((18 + dx, 85 - height, 50 + dx, 84), fill="red")
            result.append(im)
        return result

    for source in (frames(80), frames(44), frames(66)):
        normalized = normalize_frames(source)
        bounds = [im.getbbox() for im in normalized]
        assert all(im.size == (96, 76) for im in normalized)
        assert all(abs(b[3] - b[1] - 60) <= 1 for b in bounds)
        assert all(b[3] == 74 for b in bounds)
        assert bounds[1][0] > bounds[0][0]  # motion is preserved, not recentered per frame


def test_wide_cast_effects_stay_inside_the_battle_slot():
    frames = [Image.new("RGBA", (88, 88)) for _ in range(2)]
    ImageDraw.Draw(frames[0]).rectangle((22, 18, 50, 84), fill="red")
    ImageDraw.Draw(frames[1]).rectangle((0, 12, 87, 84), fill="yellow")
    normalized = normalize_frames(frames)
    assert all(0 <= b[0] < b[2] <= 96 and 0 <= b[1] < b[3] <= 76
               for b in (im.getbbox() for im in normalized))
    assert normalized[1].getbbox()[3] == 74
