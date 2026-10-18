"""Arena-only framing; one scale per clip preserves motion and body size."""
from PIL import Image

FRAME_SIZE = (96, 76)
BODY_HEIGHT = 60
GROUND_Y = 74
ACTIONS = {"idle", "punch", "cast", "hit", "hurt", "block"}


def normalize_frames(frames):
    bounds = [frame.getchannel("A").getbbox() for frame in frames]
    visible = [box for box in bounds if box]
    if not visible:
        raise ValueError("Battle animation has no visible pixels")
    union = (min(b[0] for b in visible), min(b[1] for b in visible),
             max(b[2] for b in visible), max(b[3] for b in visible))
    reference = next(box for box in bounds if box)
    width, height = union[2] - union[0], union[3] - union[1]
    scale = min(BODY_HEIGHT / (reference[3] - reference[1]),
                (FRAME_SIZE[0] - 4) / width, (GROUND_Y - 2) / height)
    size = (max(1, round(width * scale)), max(1, round(height * scale)))
    origin = ((FRAME_SIZE[0] - size[0]) // 2, GROUND_Y - size[1])
    result = []
    for frame in frames:
        canvas = Image.new("RGBA", FRAME_SIZE)
        canvas.alpha_composite(frame.crop(union).resize(size, Image.Resampling.NEAREST), origin)
        result.append(canvas)
    return result


def atlas_frames(atlas):
    cell = atlas.height
    if atlas.mode == "P":
        alpha = atlas.point([0] + [255] * 255, mode="L")
        rgba = atlas.convert("RGBA")
        rgba.putalpha(alpha)
    else:
        rgba = atlas.convert("RGBA")
    return normalize_frames([rgba.crop((x, 0, x + cell, cell))
                             for x in range(0, atlas.width, cell)])
