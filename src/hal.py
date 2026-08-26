"""Hardware abstraction layer for vPet on Pico W + Waveshare Pico-LCD-1.44.

Hides all the CircuitPython / displayio / debouncer / SPI setup so app.py stays clean.

Pins (Waveshare Pico-LCD-1.44):
  SPI:  GP10=SCK, GP11=MOSI
  LCD:  GP8=DC, GP9=CS, GP12=RST, GP13=Backlight (active HIGH)
  BTN:  GP15=KEY0 (next), GP17=KEY1 (action)
"""
import board
import busio
import displayio
import digitalio
from digitalio import DigitalInOut, Direction, Pull
from fourwire import FourWire
from adafruit_st7735r import ST7735R
from adafruit_debouncer import Debouncer


# ---------- Display ----------

def init_display():
    """Initialize the ST7735R display, return the display object."""
    # Backlight ON (active HIGH)
    bl = DigitalInOut(board.GP13)
    bl.direction = Direction.OUTPUT
    bl.value = True

    displayio.release_displays()
    spi = busio.SPI(clock=board.GP10, MOSI=board.GP11)
    display_bus = FourWire(
        spi,
        command=board.GP8,
        chip_select=board.GP9,
        reset=board.GP12,
    )
    return ST7735R(
        display_bus,
        width=128,
        height=128,
        colstart=2,
        rowstart=3,
        rotation=0,
    )


# ---------- Buttons ----------

def init_buttons():
    """Return (next_button, action_button) Debouncer instances.
    Both buttons are active LOW (Pull.UP)."""
    sw0 = DigitalInOut(board.GP15)
    sw0.direction = Direction.INPUT
    sw0.pull = Pull.UP
    sw1 = DigitalInOut(board.GP17)
    sw1.direction = Direction.INPUT
    sw1.pull = Pull.UP
    return Debouncer(sw0), Debouncer(sw1)
