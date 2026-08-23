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
BUTTON_LABELS = ["F", "H", "P", "E"]  # Feed, Heal, Play, rest (sleep)
BUTTON_COLORS = [0xf0b41e, 0xd03030, 0x32c850, 0x2850a0]
BUTTON_X = [8 + i * 29 for i in range(4)]
BUTTON_Y = 92

BAR_X = [6 + i * 29 for i in range(4)]
BAR_Y = 78

# ---------- Init hardware ----------
display = hal.init_display()
next_btn, action_btn = hal.init_buttons()

# ---------- Init pet ----------
pet = Pet()
load_pet(pet)  # ignore failure on first boot

# ---------- Init displayio group ----------
g = displayio.Group()
display.root_group = g

# Background
bg_bmp = load_bmp("/Background/registerjungle.bmp")
g.append(make_tile_grid(bg_bmp, x=-16, y=0))

# Sprite (placeholder until we have real Agumon frames)
idle_bmp = load_bmp("/Agumon/idle.bmp", transparent_index=0)
sp_tg = make_tile_grid(idle_bmp, x=32, y=4, tile_width=64, tile_height=64)
g.append(sp_tg)
n_idle = idle_bmp.width // 64

# 4 stat bars
bar_bmps = []
for i, stat in enumerate(STAT_ORDER):
    bmp, tg = make_stat_bar(BAR_X[i], BAR_Y, STAT_COLORS[stat])
    g.append(tg)
    bar_bmps.append(bmp)

# 4 action buttons
for i, label in enumerate(BUTTON_LABELS):
    _, tg = make_button(BUTTON_X[i], BUTTON_Y, BUTTON_COLORS[i], label)
    g.append(tg)

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
