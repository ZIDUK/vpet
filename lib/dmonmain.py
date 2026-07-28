import board
import busio
import displayio
import terminalio
import asyncio
from adafruit_st7735r import ST7735R
from digitalio import DigitalInOut, Direction, Pull
from adafruit_debouncer import Debouncer
from random import randint
import gc
from adafruit_display_shapes.rect import Rect
from adafruit_display_text.label import Label
from adafruit_button.sprite_button import SpriteButton

gc.collect()
gc.enable()
start_mem = gc.mem_free()
print("Point 1 Available memory: {} bytes".format(start_mem))

# ---------- Demo mode toggle ----------
# Set AGUMON_DEMO = True to cycle through the 8 Agumon animations
# (idle, walk, eat, attack, hurt, sleep, happy, evolve) on a clean screen.
# Button0 = next animation, Button2 = exit demo back to normal mode.
AGUMON_DEMO = True

# ---------- Hardware ----------
PINS = {
    "mosi":  board.GP11,
    "clk":   board.GP10,
    "reset": board.GP12,
    "cs":    board.GP9,
    "dc":    board.GP8,
    "key0":  board.GP15,
    "key1":  board.GP17,
    "key2":  board.GP2,
    "key3":  board.GP3,
}
SCREEN_W = 168
SCREEN_H = 132

# 0 = no view active; 1..8 = active view
view_live = 0
view_option = 0
view_screen = 0

# Set to True by the demo task to break out of the loop
exit_demo = False
# While True, key_manipulation ignores button events (the demo task owns them)
demo_active = False

# ---------- Display ----------
displayio.release_displays()
spi = busio.SPI(clock=PINS["clk"], MOSI=PINS["mosi"])
display_bus = displayio.FourWire(spi, command=PINS["dc"],
                                 chip_select=PINS["cs"], reset=PINS["reset"])
display = ST7735R(display_bus, width=SCREEN_W, height=SCREEN_H,
                  rotation=-90, bgr=False)

# ---------- Physical buttons ----------
sw0 = DigitalInOut(PINS["key0"]); sw0.direction = Direction.INPUT; sw0.pull = Pull.UP
sw1 = DigitalInOut(PINS["key1"]); sw1.direction = Direction.INPUT; sw1.pull = Pull.UP
sw2 = DigitalInOut(PINS["key2"]); sw2.direction = Direction.INPUT; sw2.pull = Pull.UP
button0 = Debouncer(sw0)
button1 = Debouncer(sw1)
button2 = Debouncer(sw2)

# ---------- Display rects ----------
topBar      = Rect(0,   0, SCREEN_W, 18,  fill=0x8fa68c)
bottomBar   = Rect(0, 114, SCREEN_W, 18,  fill=0x8fa68c)
statusRect1 = Rect(0,  15, SCREEN_W, 100, fill=0x8fa68c)
statusRect2 = Rect(0,  15, SCREEN_W, 100, fill=0x8fa68c)
statusRect3 = Rect(0,  15, SCREEN_W, 100, fill=0x8fa68c)
eatingRect  = Rect(0,  15, SCREEN_W, 100, fill=0x8fa68c)

# ---------- Labels ----------
def _lbl(text, x, y):
    l = Label(terminalio.FONT, text=text, color=0x000000)
    l.x, l.y = x, y
    return l

lb_Hungry   = _lbl("HUNGRY",   10, 70)
lb_Strength = _lbl("STRENGTH", 10, 30)
lb_Effort   = _lbl("EFFORT",   10, 70)
lb_Dp       = _lbl("DP",       10, 30)
lb_meat     = _lbl("MEAT",     80, 50)
lb_pill     = _lbl("PILL",     80, 95)
lb_weight   = _lbl("Age",      80, 50)
lb_age      = _lbl("Weigth",   80, 95)

# ---------- Tab button geometry ----------
TAB_Y       = 0
TAB_H       = 18
TAB_W       = int(SCREEN_W / 5.5)
TAB_DN_Y    = 114
TAB_DN_H    = 18
TAB_DN_W    = int(SCREEN_W / 5.5)

# ---------- SpriteButton helper ----------
def _sbtn(x, y, w, h, bmp, sel):
    return SpriteButton(x=x, y=y, width=w, height=h,
                        label_font=terminalio.FONT,
                        bmp_path=bmp, selected_bmp_path=sel,
                        transparent_index=0)

# Top row (cycle 1..4)
btn_stats_view    = _sbtn(0,            0, TAB_W,   TAB_H, "icons/statb2.bmp",    "icons/statb1.bmp")
btn_eat_view      = _sbtn(TAB_W,        0, TAB_W,   TAB_H, "icons/eat2.bmp",      "icons/eat1.bmp")
btn_training_view = _sbtn(TAB_W * 2,    0, TAB_W,   TAB_H, "icons/training2.bmp", "icons/training1.bmp")
btn_battle_view   = _sbtn(TAB_W * 3,    0, TAB_W,   TAB_H, "icons/battle2.bmp",   "icons/battle1.bmp")
# Bottom row (cycle 5..8)
btn_poop_view     = _sbtn(0,            TAB_DN_Y, TAB_DN_W, TAB_DN_H, "icons/poop2.bmp",   "icons/poop1.bmp")
btn_light_view    = _sbtn(TAB_DN_W,     TAB_DN_Y, TAB_DN_W, TAB_DN_H, "icons/light2.bmp",  "icons/light1.bmp")
btn_band_view     = _sbtn(TAB_DN_W * 2, TAB_DN_Y, TAB_DN_W, TAB_DN_H, "icons/band2.bmp",   "icons/band1.bmp")
btn_callout_view  = _sbtn(TAB_DN_W * 3, TAB_DN_Y, TAB_DN_W, TAB_DN_H, "icons/call2.bmp",   "icons/call1.bmp")

ALL_TAB_BUTTONS = (btn_stats_view, btn_eat_view, btn_training_view, btn_battle_view,
                   btn_poop_view, btn_light_view, btn_band_view, btn_callout_view)

# Eating sub-buttons
Eating1Button = _sbtn(15, 40, 24, 24, "icons/transarrow.bmp", "icons/arrow.bmp")
Eating2Button = _sbtn(15, 80, 24, 24, "icons/transarrow.bmp", "icons/arrow.bmp")
ALL_EAT_BTNS  = (Eating1Button, Eating2Button)

# ---------- Preload every bitmap we'll ever show ----------
# Each Greymon animation is a single BMP that contains 4 frames as a tile
# strip; the TileGrid selects which frame via grid[0].
# (filename, tile_w, tile_h, x, y, cycles_per_action)
ANIM_DEFS = (
    ("/Greymon/dmonidle.bmp",    64, 78, 40, 35, 4),
    ("/Greymon/dmonwalk.bmp",    62, 78, 40, 35, 10),
    ("/Greymon/dmoneatmeat.bmp", 64, 78, 40, 35, 4),
    ("/Greymon/dmonsleep.bmp",   64, 50, 40, 60, 40),
    ("/Greymon/dmonvictory.bmp", 64, 78, 40, 35, 4),
)

anim = {}  # name -> (bitmap, palette, tile_w, tile_h, cycles)
for path, tw, th, _x, _y, cycles in ANIM_DEFS:
    bmp = displayio.OnDiskBitmap(path)
    pal = bmp.pixel_shader
    pal.make_transparent(0)
    anim[path.split("/")[-1]] = (bmp, pal, tw, th, cycles)

bg_bmp = displayio.OnDiskBitmap("/Background/registerjungle.bmp")
meat_bmp = displayio.OnDiskBitmap("/icons/meat.bmp")
meat_pal = meat_bmp.pixel_shader; meat_pal.make_transparent(0)
pill_bmp = displayio.OnDiskBitmap("/icons/pill.bmp")
pill_pal = pill_bmp.pixel_shader; pill_pal.make_transparent(0)
statuswa_bmp = displayio.OnDiskBitmap("/icons/statuswa.bmp")
statuswa_pal = statuswa_bmp.pixel_shader; statuswa_pal.make_transparent(0)
heartf_bmp = displayio.OnDiskBitmap("/icons/heartf.bmp")
heartf_pal = heartf_bmp.pixel_shader; heartf_pal.make_transparent(0)
hearte_bmp = displayio.OnDiskBitmap("/icons/hearte.bmp")
hearte_pal = hearte_bmp.pixel_shader; hearte_pal.make_transparent(0)

# New bitmaps for Poop / Light / Training views
poop_bmp = displayio.OnDiskBitmap("/icons/poop2.bmp")
poop_pal = poop_bmp.pixel_shader; poop_pal.make_transparent(0)
light_bmp = displayio.OnDiskBitmap("/icons/light2.bmp")
light_pal = light_bmp.pixel_shader; light_pal.make_transparent(0)
attacka_bmp = displayio.OnDiskBitmap("/Greymon/dmonattacka.bmp")
attacka_pal = attacka_bmp.pixel_shader; attacka_pal.make_transparent(0)

# ---------- View groups (one per menu) ----------
Stats_View    = displayio.Group()
Eating_View   = displayio.Group()
Training_View = displayio.Group()
Battle_View   = displayio.Group()
Poop_View     = displayio.Group()
Light_View    = displayio.Group()
Bandage_View  = displayio.Group()
Callout_View  = displayio.Group()

ALL_VIEWS = (Stats_View, Eating_View, Training_View, Battle_View,
             Poop_View, Light_View, Bandage_View, Callout_View)

# View button ↔ view group (1-based index in switch_view)
VIEW_MAP = (
    (btn_stats_view,    Stats_View),
    (btn_eat_view,      Eating_View),
    (btn_training_view, Training_View),
    (btn_battle_view,   Battle_View),
    (btn_poop_view,     Poop_View),
    (btn_light_view,    Light_View),
    (btn_band_view,     Bandage_View),
    (btn_callout_view,  Callout_View),
)

# ---------- Async view helpers (replaces the blocking time.sleep(0.1)) ----------
async def layerVisibility(state, layer, target):
    try:
        if state == "show":
            await asyncio.sleep_ms(80)  # yield so display has time to flush
            layer.append(target)
        elif state == "hide":
            layer.remove(target)
    except ValueError:
        pass

async def show_only(target):
    """Hide all menu views, then show target (None = none)."""
    for v in ALL_VIEWS:
        await layerVisibility("hide", view_layer, v)
    if target is not None:
        await layerVisibility("show", view_layer, target)

async def switch_view(idx):
    """idx is 1..8 or 0 for no view."""
    global view_live
    for btn in ALL_TAB_BUTTONS:
        btn.selected = False
    if idx == 0:
        await show_only(None)
    else:
        btn, view = VIEW_MAP[idx - 1]
        btn.selected = True
        await show_only(view)
    view_live = idx
    print("View {} On".format(idx))

async def switch_option(idx):
    """Eating sub-option: 1 or 2."""
    global view_option
    ALL_EAT_BTNS[0].selected = (idx == 1)
    ALL_EAT_BTNS[1].selected = (idx == 2)
    view_option = idx
    print("Option {} On".format(idx))

# Stats sub-screens within Stats_View
STATS_SUBVIEWS = []
async def switch_stats_screen(idx):
    global view_screen
    for v in STATS_SUBVIEWS:
        await layerVisibility("hide", Stats_View, v)
    if 1 <= idx <= len(STATS_SUBVIEWS):
        await layerVisibility("show", Stats_View, STATS_SUBVIEWS[idx - 1])
    view_screen = idx
    print("Stats screen {} On".format(idx))

# ---------- Root display layers ----------
# anim_layer: bg, tab buttons, digimon animations (z-bottom)
# view_layer: menu views (z-top, always drawn on top of the digimon)
splash = displayio.Group()
anim_layer = displayio.Group()
view_layer = displayio.Group()
splash.append(anim_layer)
splash.append(view_layer)
display.root_group = splash

# ---------- Pre-create one TileGrid per animation (reused forever) ----------
def _anim_grid(name, x, y):
    bmp, pal, tw, th, _ = anim[name]
    return displayio.TileGrid(bmp, pixel_shader=pal, x=x, y=y,
                              tile_width=tw, tile_height=th, default_tile=0)

idle_grid    = _anim_grid("dmonidle.bmp",    40, 35)
walk_grid    = _anim_grid("dmonwalk.bmp",    40, 35)
eatmeat_grid = _anim_grid("dmoneatmeat.bmp", 40, 35)
sleep_grid   = _anim_grid("dmonsleep.bmp",   40, 60)
victory_grid = _anim_grid("dmonvictory.bmp", 40, 35)

idle_group    = displayio.Group(); idle_group.append(idle_grid)
walk_group    = displayio.Group(); walk_group.append(walk_grid)
eatmeat_group = displayio.Group(); eatmeat_group.append(eatmeat_grid)
sleep_group   = displayio.Group(); sleep_group.append(sleep_grid)
victory_group = displayio.Group(); victory_group.append(victory_grid)

# Background + bars
bg_tile  = displayio.TileGrid(bg_bmp, pixel_shader=bg_bmp.pixel_shader)
bg_group = displayio.Group()
bg_group.append(bg_tile)
bg_group.append(topBar)
bg_group.append(bottomBar)
anim_layer.append(bg_group)

# ---------- Pre-build the eating sub-view ----------
v_eat = displayio.Group()
v_eat.append(eatingRect)
for b in ALL_EAT_BTNS:
    v_eat.append(b)
v_eat.append(displayio.TileGrid(meat_bmp, pixel_shader=meat_pal, x=40, y=40))
v_eat.append(displayio.TileGrid(pill_bmp, pixel_shader=pill_pal, x=40, y=80))
v_eat.append(lb_meat)
v_eat.append(lb_pill)
Eating_View.append(v_eat)

# ---------- Pre-build the three stats sub-views ----------
def _stats_subview(rect, *elements):
    g = displayio.Group()
    g.append(rect)
    for e in elements:
        g.append(e)
    return g

STATS_SUBVIEWS.append(_stats_subview(
    statusRect1, lb_age, lb_weight,
    displayio.TileGrid(statuswa_bmp, pixel_shader=statuswa_pal, x=5, y=50),
))
STATS_SUBVIEWS.append(_stats_subview(
    statusRect2, lb_Hungry, lb_Strength,
    displayio.TileGrid(heartf_bmp, pixel_shader=heartf_pal, x=5, y=80),
    displayio.TileGrid(hearte_bmp, pixel_shader=hearte_pal, x=5, y=35),
))
STATS_SUBVIEWS.append(_stats_subview(
    statusRect3, lb_Effort, lb_Dp,
    displayio.TileGrid(heartf_bmp, pixel_shader=heartf_pal, x=5, y=80),
    displayio.TileGrid(hearte_bmp, pixel_shader=hearte_pal, x=5, y=35),
))

# ---------- Populate the other menu views ----------
# Poop view: drop a poop icon centered on screen
poop_tile = displayio.TileGrid(poop_bmp, pixel_shader=poop_pal, x=72, y=55)
Poop_View.append(poop_tile)

# Light view: a light bulb that blinks (toggle .hidden in a loop)
light_tile = displayio.TileGrid(light_bmp, pixel_shader=light_pal, x=72, y=55)
Light_View.append(light_tile)

# Training view: Greymon attacka (4 frames, 64x76 each) cycling
attacka_tile = displayio.TileGrid(attacka_bmp, pixel_shader=attacka_pal,
                                  x=40, y=35, tile_width=64, tile_height=76,
                                  default_tile=0)
Training_View.append(attacka_tile)

# ---------- Tab buttons (always visible on splash) ----------
for b in ALL_TAB_BUTTONS:
    anim_layer.append(b)

# ---------- Digimon animation state ----------
N_FRAMES = 4
current_frame = 0
global_position = 40

# ---------- Initial state ----------
for btn in ALL_TAB_BUTTONS:
    btn.selected = False
Eating1Button.selected = True  # matches original boot state

gc.collect()
end_mem = gc.mem_free()
print("Point 2 Available memory: {} bytes".format(end_mem))
print("Code section 1-2 used {} bytes".format(start_mem - end_mem))

# ---------- Animation helpers ----------
async def display_animation(group):
    try:
        anim_layer.append(group)
    except ValueError:
        pass

async def destroy_animation(group):
    try:
        anim_layer.remove(group)
    except ValueError:
        pass

async def _animate(grid, group, cycles, x_step=0, x_min=None, x_max=None):
    """Run a single action. Mutates grid.x and grid[0] (frame index)."""
    global current_frame, global_position
    await display_animation(group)
    for _ in range(cycles):
        if x_step and x_min is not None and grid.x > x_min:
            grid.x -= x_step
        elif x_step and x_max is not None and grid.x < x_max:
            grid.x += x_step
        if x_step:
            global_position = grid.x
        grid[0] = current_frame
        await asyncio.sleep_ms(250)
        current_frame = (current_frame + 1) % N_FRAMES
    await destroy_animation(group)

async def move_digimon_idle():    await _animate(idle_grid,    idle_group,    4)
async def move_digimon_eatmeat(): await _animate(eatmeat_grid, eatmeat_group, 4)
async def move_digimon_sleep():   await _animate(sleep_grid,   sleep_group,   40)
async def move_digimon_victory(): await _animate(victory_grid, victory_group, 4)
async def move_digimon_left():
    await _animate(walk_grid, walk_group, 10, x_step=3, x_min=2)
async def move_digimon_right():
    await _animate(walk_grid, walk_group, 10, x_step=3, x_max=70)

# ---------- Lazy-loaded animations ----------
# Pre-loading all 11 dmonanim*.bmp would exceed Pico W RAM (~150KB free).
# Instead each one loads from flash on demand, plays, then frees. The first
# run of a given animation has a small flash-read delay; subsequent runs hit
# the flash cache.
async def _play_lazy(path, tw, th, cycles, x_step=0, x_min=None, x_max=None,
                    x=40, y=35):
    """Load a BMP, play its animation, then free the memory."""
    global current_frame, global_position
    bmp = displayio.OnDiskBitmap(path)
    pal = bmp.pixel_shader
    pal.make_transparent(0)
    grid = displayio.TileGrid(bmp, pixel_shader=pal, x=x, y=y,
                              tile_width=tw, tile_height=th, default_tile=0)
    group = displayio.Group()
    group.append(grid)
    await display_animation(group)
    for _ in range(cycles):
        if x_step and x_min is not None and grid.x > x_min:
            grid.x -= x_step
        elif x_step and x_max is not None and grid.x < x_max:
            grid.x += x_step
        if x_step:
            global_position = grid.x
        grid[0] = current_frame
        await asyncio.sleep_ms(250)
        current_frame = (current_frame + 1) % N_FRAMES
    await destroy_animation(group)
    del grid, group, bmp, pal
    gc.collect()

async def move_digimon_anim01(): await _play_lazy("/Greymon/dmonanim01.bmp",  64, 64, 4)
async def move_digimon_anim02(): await _play_lazy("/Greymon/dmonanim02.bmp",  64, 64, 4)
async def move_digimon_anim03(): await _play_lazy("/Greymon/dmonanim03.bmp",  64, 64, 4)
async def move_digimon_anim04(): await _play_lazy("/Greymon/dmonanim04.bmp",  64, 64, 4)
async def move_digimon_anim05(): await _play_lazy("/Greymon/dmonanim05.bmp",  64, 64, 4)
async def move_digimon_anim06(): await _play_lazy("/Greymon/dmonanim06.bmp",  64, 64, 4)
async def move_digimon_anim07(): await _play_lazy("/Greymon/dmonanim07.bmp",  64, 64, 3)
async def move_digimon_anim08(): await _play_lazy("/Greymon/dmonanim08.bmp",  64, 64, 3)
async def move_digimon_anim09(): await _play_lazy("/Greymon/dmonanim09.bmp",  64, 64, 1)
async def move_digimon_anim10(): await _play_lazy("/Greymon/dmonanim10.bmp",  64, 64, 4)
async def move_digimon_anim11(): await _play_lazy("/Greymon/dmonanim11.bmp",  64, 64, 2)

# ---------- Agumon animations (32x32 per frame, lazy-loaded) ----------
# Each BMP is a horizontal strip; the frame count varies (8-11).
# (path, n_frames, cycles_per_loop, display_seconds_hint)
AGUMON_ANIMS = (
    ("/Agumon/agumon_idle.bmp",   9, 2,  "IDLE"),
    ("/Agumon/agumon_walk.bmp",   10, 2, "WALK"),
    ("/Agumon/agumon_eat.bmp",    9, 2,  "EAT"),
    ("/Agumon/agumon_attack.bmp", 10, 2, "ATTACK"),
    ("/Agumon/agumon_hurt.bmp",   10, 2, "HURT"),
    ("/Agumon/agumon_sleep.bmp",  8, 2,  "SLEEP"),
    ("/Agumon/agumon_happy.bmp",  11, 2, "HAPPY"),
    ("/Agumon/agumon_evolve.bmp", 6, 1,  "EVOLVE"),
)

async def _play_agumon(path, n_frames, cycles, x=68, y=50, frame_ms=180):
    """Play a 32x32-frame Agumon strip. Loads from flash, plays, frees.
    Polls buttons each frame: button0 = skip current anim, button2 = exit demo."""
    global exit_demo
    bmp = displayio.OnDiskBitmap(path)
    pal = bmp.pixel_shader
    pal.make_transparent(0)
    grid = displayio.TileGrid(bmp, pixel_shader=pal, x=x, y=y,
                              tile_width=32, tile_height=32, default_tile=0)
    group = displayio.Group()
    group.append(grid)
    await display_animation(group)
    total = n_frames * cycles
    try:
        for i in range(total):
            # Poll buttons inline so we don't need asyncio.wait
            button0.update()
            button2.update()
            if button0.fell:
                # Skip: bail out early, finally will clean up
                return
            if button2.fell:
                exit_demo = True
                return
            grid[0] = i % n_frames
            await asyncio.sleep_ms(frame_ms)
    finally:
        await destroy_animation(group)
        try:
            del grid, group, bmp, pal
        except Exception:
            pass
        gc.collect()

# ---------- Agumon demo mode ----------
# Hides normal UI, cycles through all 8 Agumon animations with a label.
# Button0 = skip to next, Button2 = exit demo.
_demo_label = _lbl("AGUMON DEMO", 10, 30)

async def agumon_demo():
    """Cycle through every Agumon animation. Exits when exit_demo is True."""
    global exit_demo, view_live, demo_active
    exit_demo = False
    demo_active = True
    # Hide all the normal menu views
    await show_only(None)
    # Pull tab buttons and eat sub-buttons out of the render tree so they
    # don't overlay the Agumon sprite. (SpriteButton may not honor .hidden,
    # so we remove/re-add from anim_layer instead.)
    saved_btns = list(ALL_TAB_BUTTONS) + list(ALL_EAT_BTNS)
    for b in saved_btns:
        try:
            anim_layer.remove(b)
        except ValueError:
            pass
    view_live = 0

    # Add label
    view_layer.append(_demo_label)
    print("Agumon demo start")
    i = 0
    while not exit_demo:
        path, n_frames, cycles, name = AGUMON_ANIMS[i]
        _demo_label.text = "AGUMON: " + name
        print("  playing {} ({} frames)".format(name, n_frames))
        # _play_agumon polls buttons itself (no asyncio.wait needed)
        try:
            await _play_agumon(path, n_frames, cycles)
        except Exception as e:
            print("anim failed:", e)
            gc.collect()
        i = (i + 1) % len(AGUMON_ANIMS)
        gc.collect()
    # Restore
    try:
        view_layer.remove(_demo_label)
    except ValueError:
        pass
    for b in saved_btns:
        try:
            anim_layer.append(b)
        except ValueError:
            pass
    demo_active = False
    print("Agumon demo end")

# ---------- View-local animations ----------
async def light_blink():
    """Blink the light bulb forever. When Light_View is hidden the tile is
    not rendered, so the toggle is a no-op visually but harmless."""
    while True:
        light_tile.hidden = False
        await asyncio.sleep_ms(450)
        light_tile.hidden = True
        await asyncio.sleep_ms(450)

async def training_animate():
    """Cycle attacka frames forever. Same lazy-when-hidden semantics as
    light_blink: no visual effect when Training_View is not on screen."""
    while True:
        for f in range(4):
            attacka_tile[0] = f
            await asyncio.sleep_ms(220)

# ---------- Main animation loop (random digimon behavior) ----------
async def move_main_screen():
    while True:
        pick = randint(1, 17)  # 6 original + 11 new lazy animations
        if   pick ==  1: await move_digimon_left()
        elif pick ==  2: await move_digimon_idle()
        elif pick ==  3: await move_digimon_sleep()
        elif pick ==  4: await move_digimon_victory()
        elif pick ==  5: await move_digimon_eatmeat()
        elif pick ==  6: await move_digimon_right()
        elif pick ==  7: await move_digimon_anim01()
        elif pick ==  8: await move_digimon_anim02()
        elif pick ==  9: await move_digimon_anim03()
        elif pick == 10: await move_digimon_anim04()
        elif pick == 11: await move_digimon_anim05()
        elif pick == 12: await move_digimon_anim06()
        elif pick == 13: await move_digimon_anim07()
        elif pick == 14: await move_digimon_anim08()
        elif pick == 15: await move_digimon_anim09()
        elif pick == 16: await move_digimon_anim10()
        else:            await move_digimon_anim11()
        gc.collect()  # reclaim any temp allocations

# ---------- Button handling ----------
async def key_manipulation():
    global view_live, view_option, view_screen
    while True:
        button0.update()
        button1.update()
        button2.update()

        # Demo mode owns the buttons — just keep the debouncers ticking
        if demo_active:
            await asyncio.sleep_ms(10)
            continue

        if button0.fell:
            new_view = view_live + 1
            if new_view > len(VIEW_MAP):
                new_view = 0
            await switch_view(new_view)
            if new_view != 2:  # not the eating view
                view_option = 0

        if button1.fell:
            if view_live == 1:
                new_screen = view_screen + 1
                if new_screen > len(STATS_SUBVIEWS):
                    new_screen = 0
                await switch_stats_screen(new_screen)
            elif view_live == 2:
                new_opt = view_option + 1
                if new_opt > len(ALL_EAT_BTNS):
                    new_opt = 0
                if new_opt > 0:
                    await switch_option(new_opt)

        if button2.fell:
            await switch_view(0)

        # Always yield so move_main_screen can run, even mid-menu
        await asyncio.sleep_ms(10)

# ---------- Main ----------
print("dmonmain loaded, AGUMON_DEMO =", AGUMON_DEMO)

async def main():
    print("main() entered, AGUMON_DEMO =", AGUMON_DEMO)
    if AGUMON_DEMO:
        # Run the Agumon demo first. The demo owns the buttons during its run
        # and short-circuits key_manipulation via the demo_active flag.
        # Await directly so any exception is caught here (a separate task
        # would silently die).
        try:
            print("Starting Agumon demo...")
            await agumon_demo()
            print("Agumon demo finished, returning to normal mode")
        except Exception as e:
            print("DEMO CRASHED:", e)
            # Best-effort UI restore so we don't end up with no UI
            for b in ALL_TAB_BUTTONS:
                try:
                    b.hidden = False
                except Exception:
                    pass
            for btn in ALL_EAT_BTNS:
                try:
                    btn.hidden = False
                except Exception:
                    pass
            try:
                view_layer.remove(_demo_label)
            except Exception:
                pass
            demo_active = False
            exit_demo = True

    print("Starting normal vPet mode")
    asyncio.create_task(move_main_screen())
    asyncio.create_task(light_blink())
    asyncio.create_task(training_animate())
    while True:
        await key_manipulation()

asyncio.run(main())
