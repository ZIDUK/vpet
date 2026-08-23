# Hardware notes

## Waveshare Pico-LCD-1.44

| Pin | Function |
|---|---|
| GP10 | LCD_CLK (SPI clock) |
| GP11 | LCD_DIN (SPI data / MOSI) |
| GP8 | LCD_DC (data/command) |
| GP9 | LCD_CS (chip select, active low) |
| GP12 | LCD_RST (reset, active low) |
| GP13 | LCD_BL (backlight, set HIGH to enable) |
| GP15 | KEY0 (user button 1) |
| GP17 | KEY1 (user button 2) |
| GP2 | KEY2 (user button 3, unused in v13.0) |
| GP3 | KEY3 (user button 4, unused in v13.0) |

## CircuitPython 10.2.1 init pattern

```python
import board, busio, displayio, digitalio
from fourwire import FourWire  # NOT displayio.FourWire — moved in CP 10
from adafruit_st7735r import ST7735R

# Backlight MUST be enabled manually
bl = digitalio.DigitalInOut(board.GP13)
bl.direction = digitalio.Direction.OUTPUT
bl.value = True

displayio.release_displays()
spi = busio.SPI(clock=board.GP10, MOSI=board.GP11)
display_bus = FourWire(spi, command=board.GP8, chip_select=board.GP9, reset=board.GP12)
display = ST7735R(display_bus, width=128, height=128, colstart=2, rowstart=2, rotation=180)
```

## Common gotchas

- **`from fourwire import FourWire`**, not `from displayio import FourWire`. In CircuitPython 10,
  FourWire moved to its own module. The old import silently makes the display show nothing.

- **Backlight is OFF by default**. You MUST set GP13 HIGH or the screen will look completely
  white/blank even though the code is running.

- **Old .mpy libraries from CP 8.x don't work on CP 10.x**. The bytecode format changed
  (0x4305 → 0x4306). If you see "incompatible .mpy" errors, grab the CP 10 version from
  https://github.com/adafruit/Adafruit_CircuitPython_Bundle/releases (look for `*10.x-mpy*.zip`).

- **`displayio.OnDiskBitmap` + `make_transparent(0)`** can fail silently in some combinations
  on CP 10.2.1. Test it explicitly with a debug print before assuming it works.

- **`adafruit_imageload` package layout changed in CP 10**. The `__init__.mpy` files for the
  package AND its sub-packages (`bmp/`, etc) are all required. If you copy only some files
  you'll get cryptic import errors.

- **`displayio.Palette` has no `.depth` attribute** in CP 10. Use `len(palette)` instead.

- **`Rect.width` and `Rect.height` are READ-ONLY** in CP 8.2.9 (not settable). To draw a border,
  draw 4 separate small Rects or use a `Line` from `adafruit_display_shapes`.

## File transfer

The Pico W appears as a USB mass storage device (`/Volumes/CIRCUITPY`). Just copy files.

For other boards (T-Display, ESP32), use `mpremote fs cp`:

```bash
mpremote connect /dev/cu.usbserial-XXXXX fs cp local_file.py :/remote_file.py
```

## Power and heat

- The Pico-LCD-1.44 is well-behaved. Runs cool, no issues.
- The T-Display v1.1 (ESP32) is NOTORIOUS for overheating. The AMS1117 regulator can die
  if WiFi is on at full power with the display active. Avoid or attach a heatsink.

## Resource limits

- Pico W: 264KB RAM, 2MB flash
- After CP 10.2.1 runtime: ~140KB RAM free for code
- v13.0 with 5 sprite sheets loaded, 4 stat bars, 4 action tiles, 1 background, 1 selector:
  ~140KB free still. Plenty of headroom for M1.
