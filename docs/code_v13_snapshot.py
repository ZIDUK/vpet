"""vPet Pico v13.0 - Agumon animated + jungle + 4 colored action squares w/ selector
Waveshare Pico-LCD-1.44 (ST7735S 128x128, rotation=180)"""
import board, busio, displayio, digitalio, time
from fourwire import FourWire
from adafruit_st7735r import ST7735R
from digitalio import DigitalInOut, Direction, Pull
from adafruit_debouncer import Debouncer

# Backlight
bl = DigitalInOut(board.GP13); bl.direction = Direction.OUTPUT; bl.value = True

displayio.release_displays()
spi = busio.SPI(clock=board.GP10, MOSI=board.GP11)
display_bus = FourWire(spi, command=board.GP8, chip_select=board.GP9, reset=board.GP12)
display = ST7735R(display_bus, width=128, height=128, colstart=2, rowstart=2, rotation=180)

W, H = 128, 128
g = displayio.Group()
display.root_group = g

# Background - jungle
bg_bmp = displayio.OnDiskBitmap("/Background/registerjungle.bmp")
g.append(displayio.TileGrid(bg_bmp, pixel_shader=bg_bmp.pixel_shader, x=-16, y=0))

# Agumon sprite
idle_bmp = displayio.OnDiskBitmap("/Agumon/agumon_idle.bmp")
idle_bmp.pixel_shader.make_transparent(0)
sp_tg = displayio.TileGrid(
    idle_bmp, pixel_shader=idle_bmp.pixel_shader,
    x=32, y=4, tile_width=64, tile_height=64
)
g.append(sp_tg)
n_idle = idle_bmp.width // 64
print("sprite", n_idle)

# 4 stat bars at y=80
bar_colors = [0xf0b41e, 0x2850a0, 0x32c850, 0xd03030]
bar_fg_tiles = []
for i, c in enumerate(bar_colors):
    b_fg = displayio.Bitmap(26, 4, 1)
    p_fg = displayio.Palette(1); p_fg[0] = c
    fg = displayio.TileGrid(b_fg, pixel_shader=p_fg, x=6 + i*29, y=80)
    g.append(fg)
    bar_fg_tiles.append((b_fg, fg))

# 4 action buttons as numbered colored squares (no BMP, no transparency issues)
ACT_BG = [0xf0b41e, 0xd03030, 0x32c850, 0x2850a0]  # yellow red green blue
ACT_LABELS = ["F", "H", "P", "E"]  # F=Feed, H=Heal, P=Play, E=Evo

# Pre-draw all 4 buttons as filled squares
btn_bmps = []
for i, bg_c in enumerate(ACT_BG):
    # Square 24x24
    b = displayio.Bitmap(24, 24, 1)
    p = displayio.Palette(2); p[0] = bg_c; p[1] = 0xffffff
    # Fill with bg color
    for x in range(24):
        for y in range(24):
            b[x, y] = 0
    # Add letter as 5x7 pixel font (simple bitmap)
    label = ACT_LABELS[i]
    label_bmp = {
        "F": [(0,0),(0,1),(0,2),(0,3),(0,4),(0,5),(0,6),  # |
              (1,0),(2,0),(3,0),  # top
              (1,3),(2,3),(3,3),  # mid
              (1,4),(2,5)],       # legs
        "H": [(0,0),(0,1),(0,2),(0,3),(0,4),(0,5),(0,6),
              (3,0),(3,1),(3,2),(3,3),(3,4),(3,5),(3,6),
              (1,3),(2,3)],
        "P": [(0,0),(0,1),(0,2),(0,3),(0,4),(0,5),(0,6),
              (1,0),(2,0),(3,0),
              (1,3),(2,3),(3,3),
              (1,1),(1,2),(2,1),(2,2)],
        "E": [(0,0),(0,1),(0,2),(0,3),(0,4),(0,5),(0,6),
              (1,0),(2,0),(3,0),
              (1,3),(2,3),
              (1,6),(2,6),(3,6)],
    }
    for x, y in label_bmp[label]:
        if 0 <= x+8 < 24 and 0 <= y+8 < 24:
            b[x+8, y+8] = 1
    t = displayio.TileGrid(b, pixel_shader=p, x=8 + i*29, y=92)
    g.append(t)
    btn_bmps.append((b, t, p))

# Selection ring (white hollow square that moves)
sel_b = displayio.Bitmap(24, 24, 1)
sel_p = displayio.Palette(1); sel_p[0] = 0xffffff
for x in range(24):
    sel_b[x, 0] = 1; sel_b[x, 23] = 1
for y in range(24):
    sel_b[0, y] = 1; sel_b[23, y] = 1
sel_tg = displayio.TileGrid(sel_b, pixel_shader=sel_p, x=8, y=92)
g.append(sel_tg)

# Buttons
sw0 = DigitalInOut(board.GP15); sw0.direction = Direction.INPUT; sw0.pull = Pull.UP
sw1 = DigitalInOut(board.GP17); sw1.direction = Direction.INPUT; sw1.pull = Pull.UP
b0 = Debouncer(sw0); b1 = Debouncer(sw1)

# State
pet = {"h": 70, "e": 70, "p": 70, "hp": 70}
menu_idx = 0

def draw_bars():
    stats = [pet["h"], pet["e"], pet["p"], pet["hp"]]
    for i, val in enumerate(stats):
        b_fg, _ = bar_fg_tiles[i]
        fill = int(26 * val / 100)
        for x in range(26):
            on = (x < fill)
            b_fg[x, 0] = 1 if on else 0
            b_fg[x, 1] = 1 if on else 0
            b_fg[x, 2] = 1 if on else 0
            b_fg[x, 3] = 1 if on else 0

def do_action():
    if menu_idx == 0: pet["h"] = min(100, pet["h"] + 25)
    elif menu_idx == 1: pet["hp"] = min(100, pet["hp"] + 30)
    elif menu_idx == 2: pet["p"] = min(100, pet["p"] + 15)
    elif menu_idx == 3:
        pet["h"] = min(100, pet["h"] + 10)
        pet["hp"] = min(100, pet["hp"] + 10)

def decay():
    pet["h"] = max(0, pet["h"] - 1)
    pet["e"] = max(0, pet["e"] - 1)
    pet["p"] = max(0, pet["p"] - 1)
    pet["hp"] = max(0, pet["hp"] - 1)

def draw_menu():
    sel_tg.x = 8 + menu_idx * 29

draw_bars()
draw_menu()
print("vPet v13.0 ready")

frame = 0
last_frame = time.monotonic()
last_decay = time.monotonic()
while True:
    b0.update(); b1.update()
    if b0.fell:
        menu_idx = (menu_idx + 1) % 4
        draw_menu()
    if b1.fell:
        do_action()
        draw_bars()
    now = time.monotonic()
    if now - last_frame > 0.12:
        frame = (frame + 1) % n_idle
        sp_tg[0] = frame
        last_frame = now
    if now - last_decay > 3:
        decay()
        draw_bars()
        last_decay = now
    time.sleep(0.05)
