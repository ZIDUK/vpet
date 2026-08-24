# Hardware Reference

This document gives a complete technical reference for the hardware that vPet runs on.
It is written so an AI agent (or a new human dev) can read it and immediately understand
what the board is, how it's wired, and what the constraints are.

> **Source**: [Waveshare Pico-LCD-1.44 wiki](https://www.waveshare.com/wiki/Pico-LCD-1.44)
> plus empirical notes from this project.

## At a glance

| Property | Value |
|---|---|
| Board | Waveshare Pico-LCD-1.44 |
| Form factor | Raspberry Pi Pico HAT (plugs into Pico pin headers) |
| Display | 1.44" TFT, 128×128 px, 65K RGB colors |
| Display driver | ST7735S (Sitronix, 132×162 controller, this panel uses 128×128) |
| Interface | 4-wire SPI (no MISO — display only, no readback) |
| Operating voltage | 3.3V (signals) / 5V tolerant (VSYS input) |
| Dimensions | 52.0 × 30.0 mm |
| Display area | 25.5 × 26.5 mm |
| Pixel pitch | 0.20 × 0.20 mm |
| Weight | ~10 g |
| Operating temp | -20°C to +70°C |
| Buttons | 4× tactile switches (KEY0–KEY3) — we use only KEY0 and KEY1 |
| Price | ~$13 USD |

## Host MCU

The board is designed to plug directly onto a **Raspberry Pi Pico** or **Pico W** header.
The W variant is what we use (the user has a Pico W).

| Property | Value |
|---|---|
| MCU | RP2040 (dual-core ARM Cortex-M0+, 133 MHz) |
| RAM | 264 KB SRAM |
| Flash | 2 MB QSPI |
| Wireless | 2.4 GHz 802.11n (CYW43439) on Pico W |
| USB | USB 1.1 host/device, micro-USB or USB-C depending on board revision |
| GPIO | 26 multi-function GPIO (3.3V logic) |
| ADC | 3× 12-bit SAR ADC |
| Other | 2× UART, 2× I2C, 2× SPI, 16× PWM, 8× PIO state machines |
| Operating voltage | 1.8V – 5.5V input (VBUS or VSYS) |
| Logic level | 3.3V |

**Firmware we run**: CircuitPython 10.2.1 (port: `adafruit-circuitpython-raspberry_pi_pico_w-en_US-10.2.1.uf2`)

## Display panel

### ST7735S controller

The ST7735S is a single-chip controller for 132×162 TFT panels. Our panel is 128×128,
so the controller's 132-wide RAM has 2 pixels of horizontal offset that are unused
(exactly what `colstart=2` in our init code is for — see `src/hal.py`).

**Color formats supported**:
- 4-bit RGB444 (4096 colors)
- **16-bit RGB565 (65K colors)** — what we use
- 18-bit RGB666 (262K colors)

**Memory**: the ST7735S has built-in 132×162×18-bit = 39.6 KB of GRAM. We don't use
all of it (only 128×128 = 32.7 KB worth of pixels).

**Refresh rate**: partial-frame updates supported. We redraw only changed regions
where possible (the dirty-rect of a stat bar, the selected button ring) and full-frame
once per 0.12s for sprite frame advance.

### SPI protocol (4-wire)

This is **NOT a standard SPI** — it's a write-only variant optimized for displays:

| Signal | Pin on Pico W | Direction | Description |
|---|---|---|---|
| MOSI (SDA) | GP11 | Pico → display | Serial data (RGB pixel or command byte) |
| SCLK (SCL) | GP10 | Pico → display | Serial clock |
| CS (CSX)   | GP9  | Pico → display | Chip select, **active low** |
| DC (D/CX)  | GP8  | Pico → display | Data/Command select: **0 = command, 1 = data** |
| RST (RESX) | GP12 | Pico → display | Hardware reset, **active low** |
| BL         | GP13 | Pico → display | Backlight enable, **active high** (set HIGH for ON) |

There is **no MISO** — the display never sends data back to the host. The SPI bus on
the Pico is configured as 3-wire (MOSI-only) by the `fourwire.FourWire` driver.

**SPI mode**: Mode 0 (CPOL=0, CPHA=0). MSB first. Max clock 32 MHz on RP2040.
We use the default busio.SPI() speed which is determined by the display driver
(typically 12 MHz on ST7735S, plenty fast for 128×128 @ 30 fps).

**Frame transmission**:
1. Pull CS low.
2. Drive DC low (command), clock out the command byte on MOSI.
3. For each parameter of that command, drive DC high (data) and clock out the parameter.
4. Pull CS high.

**Sending one pixel** (16-bit RGB565 color):
- Command: `0x2C` (RAMWR — memory write)
- Data: 2 bytes (high 5 bits red, middle 6 bits green, low 5 bits blue)
- After the data, the ST7735S auto-increments its write pointer. The next
  pixel data byte sent will go to the next pixel position (left-to-right,
  then top-to-bottom).

**Init sequence** (handled by `adafruit_st7735r.mpy`):
1. Software reset (or hardware via RST pin)
2. Sleep out (`0x11`)
3. Color mode set to 16-bit (`0x3A`, param 0x05)
4. Display on (`0x29`)
5. Many other configuration commands (gamma, inversion, etc.)

We don't need to write this — the Adafruit library handles it. We only need to pass
the right constructor params for our panel variant:
- `colstart=2` — skips the unused left 2 pixels
- `rowstart=2` — skips the unused top 2 pixels (or maybe 1, varies by panel lot)
- `rotation=180` — flips the display 180° so the USB connector is at the top

## Buttons

| Button | Pin | Function in vPet |
|---|---|---|
| KEY0 | GP15 | Navigate menu (NEXT) |
| KEY1 | GP17 | Apply selected action (ACTION) |
| KEY2 | GP2  | (unused — reserved for future "back" / "menu" button) |
| KEY3 | GP3  | (unused — reserved for future "select" / "info" button) |

**Wiring**: each button shorts its GPIO pin to GND when pressed.
**Logic**: active LOW. We configure the pin as `INPUT` with `Pull.UP` so the pin
reads HIGH when idle, LOW when pressed.

**Debouncing**: handled in software by `adafruit_debouncer.Debouncer`.
Default debounce interval is 10ms. Each main loop iteration calls `b.update()` which
samples the pin and updates `b.fell` (True for one frame when transitioning from
HIGH to LOW).

## Power

- **VBUS** (5V from USB) feeds the Pico's onboard 3.3V LDO (RT6150 on Pico W).
- **VSYS** (1.8V–5.5V) is the alternative power input — same as VBUS when USB is plugged.
- **3V3_OUT** (3.3V output from the LDO) is what powers the display logic and the LEDs.
- **GND** is common.

The display's backlight is wired to GP13, NOT to 3V3. This means the backlight is
software-controllable (we set GP13 HIGH to turn it on, LOW to turn it off). If you
don't drive GP13, the screen stays dark — this is a common gotcha for new users.

**No battery support** on this board. The Pico can run from a LiPo via VSYS with
an extra Schottky diode, but the Pico-LCD-1.44 has no battery connector. For portable
use, you'd need to add one externally or move to a different board.

## Physical layout

```
        ┌──────────────────────┐
   USB ─┤  Raspberry Pi Pico W │ (board sticking out the back)
        │  (underneath)        │
        │                      │  ┌──────────────────┐
        │  ┌────────────────┐  │  │  1.44" TFT LCD   │
        │  │   buttons on   │  │  │   (front side)   │
        │  │   the PCB      │  │  │                  │
        │  └────────────────┘  │  └──────────────────┘
        └──────────────────────┘
```

The buttons are on the back of the LCD board, accessible from the sides. KEY0 is on
the left, KEY1 on the right (when looking at the screen with USB at the top).

## Constraints and gotchas

These are the things that will bite you if you don't know:

1. **Display needs `displayio.release_displays()` before re-init.** If you don't,
   the second `ST7735R(...)` call raises `ValueError: Too many displays`.

2. **`from fourwire import FourWire` not `displayio.FourWire`.** The class moved
   from `displayio.FourWire` (CP 8.x) to a separate top-level `fourwire.FourWire` in
   CP 9.x and 10.x. The 8.x name was removed.

3. **`.mpy` files must be compiled for the right CircuitPython version.** The CP 10.x
   `.mpy` files have a `0x4306` magic; CP 8.x had `0x4305`. Mixing them produces
   `ImportError: incompatible .mpy` and (worse) silent signature mismatches that
   show as `TypeError: function takes N positional arguments but M given`.

4. **macOS leaks AppleDouble metadata (`._*` files) into the FAT filesystem.** This
   wastes 4 KB per file on a Pico with only 491 KB free. Run `find /Volumes/CIRCUITPY
   -name "._*" -delete` after every copy. The `deploy.py` script does this automatically.

5. **All assets that vPet reads must be referenced from the file as a path
   starting with `/`** (e.g. `displayio.OnDiskBitmap("/Agumon/idle.bmp")`). The root
   of the CIRCUITPY drive is `/` from CircuitPython's perspective.

6. **`adafruit_imageload` is a PACKAGE, not a single file.** If you copy any BMPs,
   you also need `lib/adafruit_imageload/__init__.mpy` AND `lib/adafruit_imageload/
   bmp/__init__.mpy` (the latter is easy to forget because it's a sub-package).

7. **Backlight must be driven manually** on GP13. `ST7735R` does not control it
   because the BL pin is not part of the display's SPI interface.

8. **The RP2040 has limited RAM (264 KB).** A full CircuitPython 10.2.1 runtime +
   displayio + framebuffer (~32 KB) + our code (~5 KB) leaves ~150 KB for heap.
   Don't try to load 64×64 sprites > 10 of them at once.

9. **`displayio.Rect.width/height` are READ-ONLY in 8.2.9** (the version we started
   on) and even setting them in newer versions can cause `IndexError` if the
   resulting bounding rect goes negative. We use 4 separate 1-pixel-wide brackets
   to draw a selection ring instead of one rect with stroke.

## References

- [Waveshare Pico-LCD-1.44 wiki](https://www.waveshare.com/wiki/Pico-LCD-1.44)
- [ST7735S datasheet (PDF link on Waveshare wiki)](https://www.waveshare.com/wiki/Pico-LCD-1.44#Documents)
- [CircuitPython displayio docs](https://docs.circuitpython.org/en/latest/shared-bindings/displayio/)
- [Raspberry Pi Pico W pinout](https://datasheets.raspberrypi.com/picow/PicoW-A4-Pinout.pdf)
- [Adafruit ST7735R library source](https://github.com/adafruit/Adafruit_CircuitPython_ST7735R)
