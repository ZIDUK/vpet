"""
vPet UI v8 — bigger icons, cell highlight for cursor, labels under icons.

Layout (132 tall):
  Top bar:    30px (5 DM icons + 4-letter label under each, cursor = yellow cell bg)
  Stage:      60px (Agumon 60x60 centered at y=30..90) — reduced from 64 for safety
  Footer:     12px (just hearts + EN bar)
  Bottom bar: 30px (5 DM icons + labels)

Cursor: full cell filled with semi-transparent yellow overlay.
Selected action label shown in footer (right side, max 4 chars).

Animations: idle(5) walk(5) run(5) eat(4) attack(6) hurt(4)
            sleep(4) happy(4) poop(4) victory(4)
"""

import board
import busio
import displayio
from adafruit_st7735r import ST7735R
from digitalio import DigitalInOut, Direction, Pull
from adafruit_debouncer import Debouncer
from adafruit_display_shapes.rect import Rect
from adafruit_display_text.label import Label
import terminalio
import asyncio
import gc
import random

# --- Display & buttons ---
displayio.release_displays()
spi = busio.SPI(clock=board.GP10, MOSI=board.GP11)
bus = displayio.FourWire(spi, command=board.GP8, chip_select=board.GP9, reset=board.GP12)
display = ST7735R(bus, width=168, height=132, rotation=-90, bgr=False)

sw0 = DigitalInOut(board.GP15); sw0.direction = Direction.INPUT; sw0.pull = Pull.UP
sw1 = DigitalInOut(board.GP17); sw1.direction = Direction.INPUT; sw1.pull = Pull.UP
sw2 = DigitalInOut(board.GP2);  sw2.direction = Direction.INPUT; sw2.pull = Pull.UP
button0 = Debouncer(sw0)
button1 = Debouncer(sw1)
button2 = Debouncer(sw2)

# --- Layout ---
W, H = 168, 132
ICON_SIZE = 20
TOP_H = 30
BOT_H = 30
FOOTER_H = 12
SPRITE_SIZE = 60
STAGE_TOP = TOP_H
STAGE_BOT = H - BOT_H - FOOTER_H  # 90
SPRITE_X = (W - SPRITE_SIZE) // 2
SPRITE_Y = STAGE_TOP + (STAGE_BOT - STAGE_TOP - SPRITE_SIZE) // 2  # 30 + 0 = 30

# --- Menu ---
TOP_ITEMS = [
    ("/icons/dm_feed.bmp",     "FEED",   "oneshot", ("eat", 2)),
    ("/icons/dm_train.bmp",    "TRAIN",  "train",   None),
    ("/icons/dm_battle.bmp",   "BATTLE", "loop",    "attack"),
    ("/icons/dm_health.bmp",   "HEAL",   "oneshot", ("sleep", 3)),
    ("/icons/dm_scan.bmp",     "SCAN",   "loop",    "happy"),
]
BOT_ITEMS = [
    ("/icons/dm_digidex.bmp",  "DEX",    "cycle",   None),
    ("/icons/dm_digivolve.bmp","EVO",    "loop",    "victory"),
    ("/icons/dm_map.bmp",      "MAP",    "loop",    "walk"),
    ("/icons/dm_status.bmp",   "STAT",   "loop",    "hurt"),
    ("/icons/dm_options.bmp",  "OPT",    "loop",    "run"),
]

# --- Animations ---
ANIMS_MAP = {
    "idle":    ("/Agumon/agumon_idle.bmp",    5),
    "walk":    ("/Agumon/agumon_walk.bmp",    5),
    "run":     ("/Agumon/agumon_run.bmp",     5),
    "eat":     ("/Agumon/agumon_eat.bmp",     4),
    "attack":  ("/Agumon/agumon_attack.bmp",  6),
    "hurt":    ("/Agumon/agumon_hurt.bmp",    4),
    "sleep":   ("/Agumon/agumon_sleep.bmp",   4),
    "happy":   ("/Agumon/agumon_happy.bmp",   4),
    "poop":    ("/Agumon/agumon_poop.bmp",    4),
    "victory": ("/Agumon/agumon_victory.bmp", 4),
}
CYCLE_SEQ = ["idle", "walk", "run", "eat", "attack", "hurt", "sleep", "happy", "poop", "victory"]
HOME_CYCLE = ["idle", "walk", "run"]

# --- Colors ---
NAVY = 0x0d1b3d
PANEL = 0x0f1e46
PANEL_DARK = 0x081632
LINE = 0x2850a0
YELLOW = 0xf0b41e
YELLOW_DIM = 0x704a08  # darker yellow for label text
GREEN = 0x32c850
ORANGE = 0xf0b41e
WHITE = 0xe0e0e0
GRAY = 0x606060
RED = 0xd03030

# --- Build UI ---
splash = displayio.Group()
display.root_group = splash

# Background
bg_bmp = displayio.OnDiskBitmap("/Background/registerjungle.bmp")
bg_pal = bg_bmp.pixel_shader
bg_pal.make_transparent(0)
splash.append(displayio.TileGrid(bg_bmp, pixel_shader=bg_pal))

# Outer frame
splash.append(Rect(1, 1, W-2, H-2, fill=None, outline=LINE, stroke=1))
splash.append(Rect(3, 3, W-6, H-6, fill=None, outline=0x143064, stroke=1))

# Bar builder
def cell_x(i, cell_w):
    """X position of icon inside cell i (centered)."""
    return int(5 + i * cell_w + (cell_w - ICON_SIZE) / 2)

def cell_origin(i, cell_w, bar_y, cell_h):
    """Top-left (x, y) of cell i."""
    return (int(5 + i * cell_w), bar_y)

def add_bar(bar_y, cell_h, items):
    # Background panel
    splash.append(Rect(5, bar_y, W-10, cell_h-2, fill=PANEL))
    cell_w = (W - 10) / len(items)
    for i, (path, label, _, _) in enumerate(items):
        cx = cell_x(i, cell_w)
        cy = bar_y + 2
        bmp = displayio.OnDiskBitmap(path)
        pal = bmp.pixel_shader
        pal.make_transparent(0)
        splash.append(displayio.TileGrid(bmp, pixel_shader=pal, x=cx, y=cy))
        # Label under icon (3-letter abbreviation to fit)
        abbrev = label[:4]
        lbl = Label(terminalio.FONT, text=abbrev, color=WHITE)
        lbl.x = cx + (ICON_SIZE - len(abbrev) * 6) // 2
        lbl.y = bar_y + cell_h - 9
        splash.append(lbl)
    return cell_w

TOP_CELL_W = add_bar(4, TOP_H, TOP_ITEMS)
bot_y = H - BOT_H + 1
BOT_CELL_W = add_bar(bot_y, BOT_H, BOT_ITEMS)

# Cursor highlight: fixed size, only x/y changes (Rect.width/height not settable in 8.2.9)
CURSOR_W = 28
CURSOR_H_PIX = 26
CURSOR_HL = Rect(0, 0, CURSOR_W, CURSOR_H_PIX, fill=None, outline=YELLOW, stroke=2)
splash.append(CURSOR_HL)

# Footer
footer_y = STAGE_BOT + 1
splash.append(Rect(5, footer_y, W-10, FOOTER_H-2, fill=PANEL_DARK))

# HP hearts (5)
hf_bmp = displayio.OnDiskBitmap("/icons/hp_full.bmp")
hf_pal = hf_bmp.pixel_shader; hf_pal.make_transparent(0)
he_bmp = displayio.OnDiskBitmap("/icons/hp_empty.bmp")
he_pal = he_bmp.pixel_shader; he_pal.make_transparent(0)
hp_hearts = []
energy = 60
for i in range(5):
    full = i < (energy // 20)
    bmp = hf_bmp if full else he_bmp
    pal = hf_pal if full else he_pal
    tg = displayio.TileGrid(bmp, pixel_shader=pal, x=7 + i * 11, y=footer_y)
    hp_hearts.append(tg)
    splash.append(tg)

# EN bar
en_lbl = Label(terminalio.FONT, text="EN", color=WHITE)
en_lbl.x, en_lbl.y = 65, footer_y + 1
splash.append(en_lbl)
splash.append(Rect(76, footer_y + 2, 28, 4, fill=GRAY))
splash.append(Rect(76, footer_y + 2, 17, 4, fill=ORANGE))

# Mood icon
mood_bmp = displayio.OnDiskBitmap("/icons/mood_small.bmp")
mood_pal = mood_bmp.pixel_shader; mood_pal.make_transparent(0)
splash.append(displayio.TileGrid(mood_bmp, pixel_shader=mood_pal, x=109, y=footer_y))

# Selected name
sel_name_lbl = Label(terminalio.FONT, text="FEED", color=YELLOW)
sel_name_lbl.x, sel_name_lbl.y = 122, footer_y + 1
splash.append(sel_name_lbl)

# Stat feedback
stat_lbl = Label(terminalio.FONT, text="", color=GREEN)
stat_lbl.x, stat_lbl.y = 7, footer_y - 11
splash.append(stat_lbl)

# Agumon sprite (60x60)
bmp = displayio.OnDiskBitmap("/Agumon/agumon_idle.bmp")
bpal = bmp.pixel_shader
bpal.make_transparent(0)
grid = displayio.TileGrid(bmp, pixel_shader=bpal, x=SPRITE_X, y=SPRITE_Y,
                          tile_width=SPRITE_SIZE, tile_height=SPRITE_SIZE, default_tile=0)
splash.append(grid)

gc.collect()
print("UI v8 built. mem free:", gc.mem_free())

# --- State ---
current_anim = "idle"
current_n = ANIMS_MAP["idle"][1]
frame = 0

mode = "idle"
action_anim = None
action_cycles_target = 0
action_cycles_done = 0
action_ticks = 0
default_cycle = 0
last_home = None
train_presses = 0
train_max = 8
train_window = 200
stat_message_ticks = 0
hunger = 0
strength = 0


def move_cursor(row, col):
    if row == 0:
        cell_w = TOP_CELL_W
        bar_y = 4
    else:
        cell_w = BOT_CELL_W
        bar_y = bot_y
    x0 = int(5 + col * cell_w)
    # Center the fixed-size cursor within the cell
    CURSOR_HL.x = x0 + (int(cell_w) - CURSOR_W) // 2
    CURSOR_HL.y = bar_y + 1


cursor_row, cursor_col = 0, 0
move_cursor(cursor_row, cursor_col)


def update_sel_label():
    items = TOP_ITEMS if cursor_row == 0 else BOT_ITEMS
    sel_name_lbl.text = items[cursor_col][1]


def update_hp():
    full_count = max(0, min(5, energy // 20))
    for i in range(5):
        full = i < full_count
        hp_hearts[i].bitmap = hf_bmp if full else he_bmp
        hp_hearts[i].pixel_shader = hf_pal if full else he_pal


def show_stat(msg, color=GREEN, ticks=60):
    global stat_message_ticks
    stat_lbl.text = msg
    stat_lbl.color = color
    stat_message_ticks = ticks


def play_anim(name):
    global current_anim, current_n, frame
    if name is None or name == current_anim:
        return
    path, n = ANIMS_MAP[name]
    try:
        new_bmp = displayio.OnDiskBitmap(path)
        new_pal = new_bmp.pixel_shader
        new_pal.make_transparent(0)
        grid.bitmap = new_bmp
        grid.pixel_shader = new_pal
        current_n = n
        current_anim = name
        frame = 0
    except Exception as e:
        print("anim fail:", e)


def end_action():
    global mode, action_anim, default_cycle, last_home
    mode = "idle"
    action_anim = None
    default_cycle = 0
    last_home = None
    play_anim(pick_home())


def start_oneshot(anim_name, cycles):
    global mode, action_anim, action_cycles_target, action_cycles_done, action_ticks
    mode = "oneshot"
    action_anim = anim_name
    action_cycles_target = cycles
    action_cycles_done = 0
    action_ticks = 0
    play_anim(anim_name)


def start_loop(anim_name):
    global mode, action_anim
    mode = "loop"
    action_anim = anim_name
    play_anim(anim_name)


def start_train():
    global mode, train_presses, action_ticks
    mode = "train"
    train_presses = 0
    action_ticks = 0
    show_stat("TRAIN! press K1", YELLOW, ticks=40)
    play_anim("walk")


def start_cycle():
    global mode
    mode = "cycle"
    show_stat("CYCLE", YELLOW, ticks=40)
    idx = CYCLE_SEQ.index(current_anim) if current_anim in CYCLE_SEQ else 0
    play_anim(CYCLE_SEQ[(idx + 1) % len(CYCLE_SEQ)])


def pick_home():
    global last_home
    choices = [a for a in HOME_CYCLE if a != last_home]
    if not choices:
        choices = HOME_CYCLE
    last_home = random.choice(choices)
    return last_home


def handle_action(kind, arg):
    if kind == "oneshot":
        anim, cycles = arg
        start_oneshot(anim, cycles)
    elif kind == "loop":
        start_loop(arg)
    elif kind == "cycle":
        start_cycle()
    elif kind == "train":
        start_train()
    else:
        end_action()


update_sel_label()


async def main():
    global cursor_row, cursor_col, current_anim, current_n, frame, default_cycle
    global mode, action_anim, action_cycles_target, action_cycles_done, action_ticks
    global train_presses, stat_message_ticks, hunger, strength, energy, last_home

    tick = 0
    while True:
        tick += 1
        if tick % 9 == 0:
            frame = (frame + 1) % current_n
            grid[0] = frame

        if stat_message_ticks > 0:
            stat_message_ticks -= 1
            if stat_message_ticks == 0:
                stat_lbl.text = ""

        if mode == "idle":
            default_cycle += 1
            if default_cycle >= 100:
                default_cycle = 0
                play_anim(pick_home())
        elif mode == "oneshot":
            action_ticks += 1
            cycle_ticks = ANIMS_MAP[action_anim][1] * 9
            if action_ticks > 0 and action_ticks % cycle_ticks == 0:
                action_cycles_done += 1
                if action_cycles_done >= action_cycles_target:
                    if action_anim == "eat":
                        hunger = min(99, hunger + 25)
                        show_stat("+%d HUNGER" % 25, GREEN)
                    elif action_anim == "sleep":
                        energy = min(100, energy + 30)
                        update_hp()
                        show_stat("+%d EN" % 30, GREEN)
                    end_action()
        elif mode == "train":
            action_ticks += 1
            if action_ticks > train_window:
                strength = min(99, strength + train_presses)
                show_stat("+%d STR!" % train_presses, YELLOW)
                end_action()
        elif mode == "cycle":
            if tick % 75 == 0:
                idx = CYCLE_SEQ.index(current_anim) if current_anim in CYCLE_SEQ else 0
                play_anim(CYCLE_SEQ[(idx + 1) % len(CYCLE_SEQ)])

        button0.update()
        button1.update()
        button2.update()

        if button0.fell:
            items = TOP_ITEMS if cursor_row == 0 else BOT_ITEMS
            if cursor_col < len(items) - 1:
                cursor_col += 1
            else:
                cursor_row = 1 - cursor_row
                cursor_col = 0
            move_cursor(cursor_row, cursor_col)
            update_sel_label()

        if button2.fell:
            if mode != "idle":
                end_action()
            else:
                default_cycle = 0
                last_home = None
                play_anim(pick_home())

        if button1.fell:
            if mode == "train":
                train_presses += 1
                show_stat("PUSH! %d/%d" % (train_presses, train_max), YELLOW, ticks=20)
                if train_presses >= train_max:
                    strength = min(99, strength + train_presses)
                    show_stat("MAX! +%d STR" % train_presses, YELLOW, ticks=80)
                    end_action()
            else:
                items = TOP_ITEMS if cursor_row == 0 else BOT_ITEMS
                kind, arg = items[cursor_col][2], items[cursor_col][3]
                handle_action(kind, arg)

        await asyncio.sleep_ms(20)


asyncio.run(main())
