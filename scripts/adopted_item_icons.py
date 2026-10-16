"""Original deterministic pixel art for adopted consumables, authored at 16px."""
from PIL import Image, ImageDraw

COLORS = {'hp': '#ee5656', 'mp': '#58bfe0', 'off': '#ee9f47',
          'def': '#8dbbe7', 'spd': '#62d8b2', 'brn': '#d395df',
          'h': '#d58b4a', 'e': '#f8d956', 'p': '#f27d9e',
          'weight': '#b7d887', 'injured': '#ee5656', 'trained_stat': '#ead283'}
GLYPHS = {
    'hp': [(7, 6), (8, 6), (7, 7), (8, 7), (5, 8), (6, 8), (7, 8),
           (8, 8), (9, 8), (10, 8), (7, 9), (8, 9), (7, 10), (8, 10)],
    'mp': [(8, 5), (6, 8), (7, 8), (8, 8), (9, 8), (7, 11)],
    'off': [(9, 5), (8, 6), (7, 7), (6, 8), (5, 9), (7, 9), (8, 10)],
    'def': [(5, 6), (6, 6), (7, 6), (8, 6), (9, 6), (10, 6),
            (5, 7), (10, 7), (6, 8), (9, 8), (7, 9), (8, 9)],
    'spd': [(5, 6), (6, 7), (7, 8), (6, 9), (5, 10), (8, 6),
            (9, 7), (10, 8), (9, 9), (8, 10)],
    'brn': [(6, 6), (7, 5), (8, 5), (9, 6), (5, 7), (10, 7),
            (6, 8), (9, 8), (7, 9), (8, 9), (7, 11), (8, 11)],
}


def render(item):
    image = Image.new('RGBA', (16, 16))
    d = ImageDraw.Draw(image)
    target = item['effects'][0]['target']
    color = COLORS[target]
    category = item['category']
    outline, white = '#111b24', '#f2f3dc'
    item_id = item['id']
    if item_id in ('meat', 'protein'):
        from scripts.item_icons import render_item_icon
        image = render_item_icon('ItemMeat' if item_id == 'meat' else 'ItemProtein', 16, framed=False)
        d = ImageDraw.Draw(image)
    elif item_id in ('giant_meat', 'sirloin'):
        d.rectangle((2, 10, 6, 11), fill=white)
        d.ellipse((4, 3, 13, 12), fill=outline)
        d.ellipse((5, 4, 12, 11), fill='#b96d35')
        for y in (6, 8):
            d.line((7, y, 10, y + 1), fill='#f2c077')
        if item_id == 'sirloin':
            d.rectangle((3, 12, 13, 13), fill='#b7c8c9')
    elif item_id == 'digimushroom':
        d.rectangle((6, 7, 9, 12), fill=white)
        d.ellipse((2, 3, 13, 9), fill=outline)
        d.ellipse((3, 4, 12, 8), fill='#c37647')
        d.point((5, 5), fill=white)
        d.point((9, 6), fill=white)
    elif item_id == 'speed_leaf':
        d.polygon(((3, 11), (5, 5), (12, 2), (11, 9), (5, 12)), fill=outline)
        d.polygon(((4, 10), (6, 6), (11, 3), (10, 8), (5, 11)), fill=color)
        d.line((4, 12, 10, 5), fill=white)
    elif item_id in ('sweet_nut', 'super_veggy', 'orange_banana'):
        if item_id == 'orange_banana':
            d.arc((2, 2, 13, 12), 10, 170, fill='#f5bd52', width=3)
        elif item_id == 'sweet_nut':
            d.ellipse((4, 4, 11, 12), fill='#ba8649', outline=outline)
            d.line((7, 6, 7, 10), fill=white)
        else:
            d.polygon(((4, 5), (6, 3), (11, 4), (12, 8), (8, 12)), fill='#65b582')
            d.line((8, 5, 8, 12), fill=white)
    elif category == 'combat_recovery':
        d.rectangle((4, 4, 11, 13), fill=outline)
        d.rectangle((5, 5, 10, 12), fill=color)
        d.rectangle((6, 2, 9, 4), fill=white)
        d.line((5, 6, 5, 10), fill=white)
        tier = item['effects'][0]['amount']
        for n in range((20, 50, 90, 100).index(tier) + 1):
            d.point((4 + n * 2, 13), fill=white)
    elif category == 'battle_boost':
        d.ellipse((2, 2, 13, 13), fill=outline)
        d.ellipse((3, 3, 12, 12), fill=color)
        d.ellipse((5, 5, 10, 10), fill=outline)
    elif category == 'permanent' and item['id'].endswith('_chip'):
        for n in (4, 7, 10):
            d.line((n, 1, n, 14), fill='#d8b65a')
            d.line((1, n, 14, n), fill='#d8b65a')
        d.rectangle((3, 3, 12, 12), fill=outline)
        d.rectangle((4, 4, 11, 11), fill=color)
    elif category == 'condition':
        d.rectangle((3, 4, 12, 12), fill=outline)
        d.rectangle((4, 5, 11, 11), fill=white)
        d.line((7, 6, 7, 10), fill=color)
        d.line((5, 8, 9, 8), fill=color)
        if item['id'] == 'medicine':
            d.rectangle((6, 2, 9, 3), fill=color)
    elif category == 'training_boost':
        d.rectangle((3, 2, 12, 13), fill=outline)
        d.rectangle((5, 3, 11, 12), fill='#ead283')
        d.rectangle((4, 3, 4, 12), fill='#58bfe0')
        d.line((7, 5, 10, 5), fill=outline)
        d.line((7, 7, 10, 7), fill=outline)
    else:
        d.ellipse((3, 5, 12, 13), fill=outline)
        d.ellipse((4, 6, 11, 12), fill=color)
        d.line((7, 2, 8, 5), fill='#55ae78', width=2)
        d.point((5, 7), fill=white)
    for xy in GLYPHS.get(target, ()):
        d.point(xy, fill=white if category != 'condition' else color)
    # Each item has a stable, distinct edge badge; tiers remain readable at 16px.
    from core.adopted_items import ITEMS
    badge = next(i for i, value in enumerate(ITEMS) if value['id'] == item['id']) + 1
    for bit in range(6):
        if badge & (1 << bit):
            d.point((5 + bit, 14), fill=color)
    return image.resize((32, 32), Image.Resampling.NEAREST)
