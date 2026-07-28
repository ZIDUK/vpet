"""
vPet UI v7 — Agumon 64x64 atlas + functional FEED & TRAIN.

Layout (132 tall):
  Top bar:    24px (5 DM icons)
  Stage:      64px (Agumon 64x64 centered at y=24..88)
  Footer:     14px (hearts + EN + mood + name + stat)
  Bottom bar: 30px (5 DM icons + cursor area)

Animations: idle(5) walk(5) run(5) eat(4) attack(6) hurt(4)
            sleep(4) happy(4) poop(4) victory(4)

Actions:
  FEED   → play eat for 2 cycles (~1.4s), +25 hunger, return to idle
  TRAIN  → play walk; press KEY1 to push (max 8); ends at 8 presses or
           ~4s, then +N strength where N=presses
  BATTLE → loop attack until KEY2
  HEAL   → play sleep 3 cycles (~2.2s), +30 energy, return to idle
  SCAN   → loop happy until KEY2
  DEX    → cycle through all anims (auto-advance every 1.5s)
  EVO    → loop victory until KEY2
  MAP    → loop walk until KEY2
  STAT   → loop hurt until KEY2
  OPT    → loop run until KEY2

Default (no action): auto-cycle idle <-> walk every 3s.
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
ICON_SIZE = 18
TOP_H = 24
BOT_H = 30
FOOTER_H = 14
SPRITE_SIZE = 64
STAGE_TOP = TOP_H
STAGE_BOT = H - BOT_H - FOOTER_H  # 88
# 64x64 sprite centered in 64px stage = no vertical margin
SPRITE_X = (W - SPRITE_SIZE) // 2
SPRITE_Y = STAGE_TOP

# --- Menu ---
# (icon, label, kind, arg)
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
# Home cycle: alternates when no action is active
HOME_CYCLE = ["idle", "walk", "run"]

# --- Colors ---
NAVY = 0x0d1b3d
PANEL = 0x0f1e46
LINE = 0x2850a0
YELLOW = 0xf0b41e
GREEN = 0x32c850
ORANGE = 0xf0b41e
WHITE = 0xe0e0e0
GRAY = 0x606060
RED = 0xd03030

# --- Build UI ---
splash = displayio.Group()
display.root_group = splash

# Background
bg_bmp = displayio.OnDiskBitmap("/Background/digivice_night.bmp")
bg_pal = bg_bmp.pixel_shader
bg_pal.make_transparent(0)
splash.append(displayio.TileGrid(bg_bmp, pixel_shader=bg_pal))

# Outer frame
splash.append(Rect(1, 1, W-2, H-2, fill=None, outline=LINE, stroke=1))
splash.append(Rect(3, 3, W-6, H-6, fill=None, outline=0x143064, stroke=1))

# Top bar
splash.append(Rect(5, 4, W-10, TOP_H-5, fill=PANEL))
TOP_CELL_W = (W - 10) / len(TOP_ITEMS)
for i, (path, _, _, _) in enumerate(TOP_ITEMS):
    cx = int(5 + i * TOP_CELL_W + (TOP_CELL_W - ICON_SIZE) / 2)
    cy = 4 + (TOP_H - 5 - ICON_SIZE) // 2
    bmp = displayio.OnDiskBitmap(path)
    pal = bmp.pixel_shader
    pal.make_transparent(0)
    splash.append(displayio.TileGrid(bmp, pixel_shader=pal, x=cx, y=cy))

# Footer
footer_y = STAGE_BOT + 1  # 89
splash.append(Rect(5, footer_y, W-10, FOOTER_H-2, fill=PANEL))

# HP hearts (5)
hf_bmp = displayio.OnDiskBitmap("/icons/hp_full.bmp")
hf_pal = hf_bmp.pixel_shader; hf_pal.make_transparent(0)
he_bmp = displayio.OnDiskBitmap("/icons/hp_empty.bmp")
he_pal = he_bmp.pixel_shader; he_pal.make_transparent(0)
hp_hearts = []
energy = 60  # 3/5 hearts full
for i in range(5):
    full = i < (energy // 20)
    bmp = hf_bmp if full else he_bmp
    pal = hf_pal if full else he_pal
    tg = displayio.TileGrid(bmp, pixel_shader=pal, x=7 + i * 11, y=footer_y + 1)
    hp_hearts.append(tg)
    splash.append(tg)

# EN bar
en_lbl = Label(terminalio.FONT, text="EN", color=WHITE)
en_lbl.x, en_lbl.y = 65, footer_y + 2
splash.append(en_lbl)
splash.append(Rect(76, footer_y + 3, 28, 4, fill=GRAY))
splash.append(Rect(76, footer_y + 3, 17, 4, fill=ORANGE))

# Mood
mood_bmp = displayio.OnDiskBitmap("/icons/mood_small.bmp")
mood_pal = mood_bmp.pixel_shader; mood_pal.make_transparent(0)
splash.append(displayio.TileGrid(mood_bmp, pixel_shader=mood_pal, x=109, y=footer_y + 1))

# Selected name
sel_name_lbl = Label(terminalio.FONT, text="FEED", color=YELLOW)
sel_name_lbl.x, sel_name_lbl.y = 122, footer_y + 2
splash.append(sel_name_lbl)

# Stat feedback (overlaid in footer area)
stat_lbl = Label(terminalio.FONT, text="", color=GREEN)
stat_lbl.x, stat_lbl.y = 7, footer_y - 11
splash.append(stat_lbl)

# Bottom bar
bot_y = H - BOT_H + 2
splash.append(Rect(5, bot_y, W-10, BOT_H-5, fill=PANEL))
BOT_CELL_W = (W - 10) / len(BOT_ITEMS)
for i, (path, _, _, _) in enumerate(BOT_ITEMS):
    cx = int(5 + i * BOT_CELL_W + (BOT_CELL_W - ICON_SIZE) / 2)
    cy = bot_y + (BOT_H - 5 - ICON_SIZE) // 2
    bmp = displayio.OnDiskBitmap(path)
    pal = bmp.pixel_shader
    pal.make_transparent(0)
    splash.append(displayio.TileGrid(bmp, pixel_shader=pal, x=cx, y=cy))

# Cursor brackets
CURSOR_SIZE = 3
brk = [Rect(0, 0, CURSOR_SIZE, CURSOR_SIZE, fill=YELLOW) for _ in range(4)]
for b in brk:
    splash.append(b)

# Agumon sprite (centered, 64x64)
bmp = displayio.OnDiskBitmap("/Agumon/agumon_idle.bmp")
bpal = bmp.pixel_shader
bpal.make_transparent(0)
grid = displayio.TileGrid(bmp, pixel_shader=bpal, x=SPRITE_X, y=SPRITE_Y,
                          tile_width=SPRITE_SIZE, tile_height=SPRITE_SIZE, default_tile=0)
splash.append(grid)

gc.collect()
print("UI v7 built. mem free:", gc.mem_free())

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
home_idx = 0  # index into HOME_CYCLE
train_presses = 0
train_max = 8
train_window = 200  # ~4s @ 20ms
stat_message_ticks = 0
hunger = 0
strength = 0


def move_cursor(row, col):
    if row == 0:
        x0 = int(5 + col * TOP_CELL_W)
        y0 = 4
        x1 = int(x0 + TOP_CELL_W)
        y1 = TOP_H - 1
    else:
        x0 = int(5 + col * BOT_CELL_W)
        y0 = bot_y
        x1 = int(x0 + BOT_CELL_W)
        y1 = H - 5
    s = CURSOR_SIZE
    brk[0].x, brk[0].y = x0, y0
    brk[1].x, brk[1].y = x1 - s, y0
    brk[2].x, brk[2].y = x0, y1 - s
    brk[3].x, brk[3].y = x1 - s, y1 - s


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
    global mode, action_anim, default_cycle, home_idx
    mode = "idle"
    action_anim = None
    default_cycle = 0
    home_idx = 0
    play_anim(HOME_CYCLE[0])


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
    global train_presses, stat_message_ticks, hunger, strength, energy, home_idx

    tick = 0
    while True:
        tick += 1
        # Frame advance every 9 ticks (~180ms = 5.5fps)
        if tick % 9 == 0:
            frame = (frame + 1) % current_n
            grid[0] = frame

        # Stat message fade
        if stat_message_ticks > 0:
            stat_message_ticks -= 1
            if stat_message_ticks == 0:
                stat_lbl.text = ""

        # Mode logic
        if mode == "idle":
            default_cycle += 1
            if default_cycle >= 100:  # 2s per state
                default_cycle = 0
                home_idx = (home_idx + 1) % len(HOME_CYCLE)
                play_anim(HOME_CYCLE[home_idx])
        elif mode == "oneshot":
            action_ticks += 1
            # One cycle = N frames * 9 ticks each
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
            if tick % 75 == 0:  # 1.5s
                idx = CYCLE_SEQ.index(current_anim) if current_anim in CYCLE_SEQ else 0
                play_anim(CYCLE_SEQ[(idx + 1) % len(CYCLE_SEQ)])

        # Buttons
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
                home_idx = 0
                default_cycle = 0
                play_anim(HOME_CYCLE[0])

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
