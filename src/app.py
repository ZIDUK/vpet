"""vPet entrypoint. Gets bundled into a single code.py by scripts/build.py.

Layout on the 128x128 display:
  y=0..68   : sprite (64x64) centered
  y=68..83  : 4 stat bars (5px tall)
  y=83..127 : 4 action buttons (24x24)

Stage progression (the lifecycle of a pet):
  Egg → Baby → Rookie → Champion → Ultimate → Mega
The runtime sprite path is /<Stage>/<file>.bmp, e.g. /Egg/hatch_atlas.bmp.
"""
import time

import hal
import displayio
import supervisor
from core.pet import Pet, STAT_ORDER, STAT_COLORS, STATE_EGG, STATE_HATCHING
from core.save import save_pet, load_pet
from ui.sprites import load_bmp, make_tile_grid
from ui.widgets import make_stat_bar, draw_stat_bar, make_button, make_selection_ring

# Disable autoreload (so edits to other files don't restart us mid-loop).
supervisor.runtime.autoreload = False

# ---------- Menu config ----------
BUTTON_LABELS = ["F", "H", "P", "E"]
BUTTON_ICONS = [
    "/UI/buttons/feed.bmp",
    "/UI/buttons/heal.bmp",
    "/UI/buttons/play.bmp",
    "/UI/buttons/rest.bmp",
]
BUTTON_COLORS = [0xf0b41e, 0xd03030, 0x32c850, 0x2850a0]
BUTTON_X = [8 + i * 29 for i in range(4)]
BUTTON_Y = 92

BAR_X = [6 + i * 29 for i in range(4)]
BAR_Y = 78


# ---------- Sprite loading ----------

def load_pet_sprite(species, state, x=32, y=4):
    """Load the appropriate sprite for the pet's current stage and lifecycle state.

    Returns (tile_grid, n_frames). The caller must append the tile_grid to the
    display group.

    Sprite path convention: /digimon1/<Stage>/<file>.bmp
    where Stage = species.capitalize() (e.g. "egg" → "Egg", "baby" → "Baby").
    The runtime picks:
      - state=EGG / HATCHING → /digimon1/<Stage>/hatch_atlas.bmp  (multi-frame animation)
      - state=LIVE          → /digimon1/<Stage>/idle_atlas.bmp  (multi-frame idle)
    """
    stage_dir = species.capitalize()
    if state in (STATE_EGG, STATE_HATCHING):
        path = f"/digimon1/{stage_dir}/hatch_atlas.bmp"
    else:
        path = f"/digimon1/{stage_dir}/idle_atlas.bmp"
    bmp = load_bmp(path, transparent_index=0)
    tg = make_tile_grid(bmp, x=x, y=y, tile_width=64, tile_height=64)
    return tg, bmp.width // 64


# ---------- Init hardware ----------
display = hal.init_display()
next_btn, action_btn = hal.init_buttons()

# ---------- Init pet ----------
pet = Pet()
load_pet(pet)

if pet.state == STATE_EGG and pet.hatch_started_at is None:
    pet.hatch_started_at = time.monotonic()

# ---------- Init displayio group ----------
g = displayio.Group()
display.root_group = g

# Background — load WITHOUT transparent_index so palette[0] (background
# color of the jungle scene) stays opaque. The default load_bmp() makes
# palette index 0 transparent, which made the entire background invisible.
bg_bmp = load_bmp("/Background/jungle.bmp", transparent_index=None)
g.append(make_tile_grid(bg_bmp, x=0, y=0))

# Pet sprite
sp_tg, n_idle = load_pet_sprite(pet.species, pet.state)
g.append(sp_tg)

# 4 stat bars
bar_bmps = []
for i, stat in enumerate(STAT_ORDER):
    bmp, tg = make_stat_bar(BAR_X[i], BAR_Y, STAT_COLORS[stat])
    g.append(tg)
    bar_bmps.append(bmp)

# 4 action buttons
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


def swap_sprite(new_species, new_state):
    """Replace the sprite TileGrid with a new one for the given species/state."""
    global sp_tg, n_idle
    g.remove(sp_tg)
    sp_tg, n_idle = load_pet_sprite(new_species, new_state)
    g.insert(1, sp_tg)


draw_bars()
draw_menu()
# NOTE: don't print() here — it activates CIRCUITPYTHON_TERMINAL which
# takes over the display and shows the REPL on screen.
# (The code is running successfully; we just keep that fact silent on the
# device's own display.)


# ---------- Hatch animation state ----------
HATCH_FRAME_DURATION = 0.4   # seconds per frame
HATCH_LOOPS = 5              # total animation duration
HATCH_DURATION = HATCH_FRAME_DURATION * 4 * HATCH_LOOPS  # 4 frames * 5 loops
hatch_frame = 0
last_hatch_frame = time.monotonic()
hatch_completed = (pet.state not in (STATE_EGG, STATE_HATCHING))


# ---------- Main loop ----------
frame = 0
last_frame = time.monotonic()
last_save = time.monotonic()
SAVE_INTERVAL = 30

while True:
    # Re-assert our group as the display root. CP 10.2.1 may attach its
    # CIRCUITPYTHON_TERMINAL group to the display when the REPL is opened
    # by the serial monitor; we want our sprites to stay on screen.
    if display.root_group is not g:
        display.root_group = g

    next_btn.update()
    action_btn.update()

    if next_btn.fell:
        menu_idx = (menu_idx + 1) % 4
        draw_menu()
    if action_btn.fell and pet.is_live:
        pet.apply_action(menu_idx)
        draw_bars()

    now = time.monotonic()

    # Hatch animation
    if not hatch_completed:
        if pet.state == STATE_EGG and now - (pet.hatch_started_at or now) > 0:
            pet.start_hatch()
        if pet.is_hatching:
            if now - last_hatch_frame > HATCH_FRAME_DURATION:
                hatch_frame = (hatch_frame + 1) % 4
                sp_tg[0] = hatch_frame
                last_hatch_frame = now
            if pet.hatch_progress(HATCH_DURATION) >= 1.0:
                # Hatch complete — evolve to the baby stage.
                pet.complete_hatch("baby")
                swap_sprite(pet.species, pet.state)
                hatch_completed = True
                draw_bars()  # stats boosted

    # Idle animation for live pets
    if pet.is_live and n_idle > 1:
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
