"""vPet entrypoint. Gets bundled into a single code.py by scripts/build.py.

Layout on the 128x128 display:
  y=0..68   : sprite (64x64) centered
  y=68..83  : 4 stat bars (5px tall)
  y=83..127 : 4 action buttons (24x24)
"""
import time

import hal
import displayio
from core.pet import Pet, STAT_ORDER, STAT_COLORS
from core.save import save_pet, load_pet
from ui.sprites import load_bmp, make_tile_grid
from ui.widgets import make_stat_bar, draw_stat_bar, make_button, make_selection_ring

# ---------- Menu config ----------
# 4 action buttons. Each has a letter label (F=Feed, H=Heal, P=Play, E=Rest)
# and an optional icon path. The icon is loaded from disk if the file exists.
BUTTON_LABELS = ["F", "H", "P", "E"]
BUTTON_ICONS = [
    "/UI/buttons/feed.bmp",    # bowl of food
    "/UI/buttons/heal.bmp",    # cross / potion
    "/UI/buttons/play.bmp",    # ball
    "/UI/buttons/rest.bmp",    # bed / Z
]
BUTTON_COLORS = [0xf0b41e, 0xd03030, 0x32c850, 0x2850a0]
BUTTON_X = [8 + i * 29 for i in range(4)]
BUTTON_Y = 92

BAR_X = [6 + i * 29 for i in range(4)]
BAR_Y = 78

# Default starting species. Change this once you have your own digimon.
# The species name maps to /<TitleCase>/<state>.bmp on the device.
DEFAULT_SPECIES = "placeholder"


# ---------- Init hardware ----------
display = hal.init_display()
next_btn, action_btn = hal.init_buttons()

# ---------- Init pet ----------
pet = Pet(species=DEFAULT_SPECIES, line="custom_line")
load_pet(pet)  # ignore failure on first boot

# ---------- Init displayio group ----------
g = displayio.Group()
display.root_group = g

# Background
bg_bmp = load_bmp("/Background/jungle.bmp")
g.append(make_tile_grid(bg_bmp, x=-16, y=0))

# Sprite (idle animation: N frames of 64x64 in a single BMP strip)
# Path is /<Species>/idle.bmp where <Species> is title-case of pet.species
sprite_species_dir = pet.species.capitalize()
SPRITE_PATH = f"/{sprite_species_dir}/idle.bmp"
idle_bmp = load_bmp(SPRITE_PATH, transparent_index=0)
sp_tg = make_tile_grid(idle_bmp, x=32, y=4, tile_width=64, tile_height=64)
g.append(sp_tg)
n_idle = idle_bmp.width // 64

# 4 stat bars
bar_bmps = []
for i, stat in enumerate(STAT_ORDER):
    bmp, tg = make_stat_bar(BAR_X[i], BAR_Y, STAT_COLORS[stat])
    g.append(tg)
    bar_bmps.append(bmp)

# 4 action buttons (with optional icon overlay)
for i, label in enumerate(BUTTON_LABELS):
    bg, bg_tg, icon_tg = make_button(
        BUTTON_X[i], BUTTON_Y,
        bg_color=BUTTON_COLORS[i],
        label=label,
        icon_path=BUTTON_ICONS[i],
    )
    g.append(bg_tg)
    if icon_tg is not None:
        g.append(icon_tg)

# Selection ring
_, sel_tg = make_selection_ring(BUTTON_X[0], BUTTON_Y)
g.append(sel_tg)

# ---------- State ----------
menu_idx = 0


def draw_bars():
    for i, stat in enumerate(STAT_ORDER):
        draw_stat_bar(bar_bmps[i], pet.get(stat))


def draw_menu():
    sel_tg.x = BUTTON_X[menu_idx]


draw_bars()
draw_menu()
print("vPet ready")


# ---------- Main loop ----------
frame = 0
last_frame = time.monotonic()
last_save = time.monotonic()
SAVE_INTERVAL = 30  # save every 30s

while True:
    next_btn.update()
    action_btn.update()
    if next_btn.fell:
        menu_idx = (menu_idx + 1) % 4
        draw_menu()
    if action_btn.fell:
        pet.apply_action(menu_idx)
        draw_bars()

    now = time.monotonic()
    if now - last_frame > 0.12:
        frame = (frame + 1) % n_idle
        sp_tg[0] = frame
        last_frame = now

    if pet.decay_if_due():
        draw_bars()

    if now - last_save > SAVE_INTERVAL:
        save_pet(pet)
        last_save = now

    time.sleep(0.05)
