"""Pixel icon for the exploration entry on the top bar."""
from PIL import Image, ImageDraw


def render_explore_icon(size=20):
    """A signpost on a path. Square RGBA, readable at the menu icon size."""
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    def p(unit):
        return round(unit * (size - 1) / 15)

    draw.rectangle((p(1), p(12), p(14), p(14)), fill=(55, 155, 116, 255))
    draw.polygon(
        [(p(7), p(14)), (p(3), p(8)), (p(12), p(8))],
        fill=(208, 170, 96, 255),
    )
    draw.rectangle((p(7), p(4), p(8), p(12)), fill=(137, 75, 43, 255))
    draw.rectangle((p(2), p(2), p(12), p(6)), fill=(255, 205, 63, 255))
    draw.rectangle((p(2), p(2), p(12), p(6)), outline=(13, 20, 30, 255))
    return image


def render_guide_icon(size=20):
    image = Image.new("RGB", (size, size), (13, 20, 30))
    draw = ImageDraw.Draw(image)
    def p(unit):
        return round(unit * (size - 1) / 15)
    draw.rectangle((p(3), p(2), p(12), p(14)), fill=(240, 220, 150))
    draw.rectangle((p(2), p(1), p(4), p(14)), fill=(40, 145, 153))
    draw.rectangle((p(7), p(1), p(10), p(5)), fill=(238, 92, 80))
    for y in (7, 10, 12):
        draw.line((p(6), p(y), p(10), p(y)), fill=(44, 57, 68))
    return image
