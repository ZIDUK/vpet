"""vPet boot: prevent the REPL/terminal from taking over the display.

Without this, opening a serial monitor (mpremote, VSCode, screen) auto-attaches
the CIRCUITPYTHON_TERMINAL group to the display, showing the REPL prompt on
the 128x128 screen instead of the vPet.

Strategy: autoreload stays on (so file changes still restart code.py), but we
never let the auto-attached REPL claim the display. Our app.py will overwrite
display.root_group every loop iteration anyway, but boot.py is the first line
of defense.
"""
import supervisor

# Make sure autoreload is enabled (in case the REPL paused it).
supervisor.runtime.autoreload = True

# Don't let the auto-attached REPL take over the display.
# Setting display = None tells the supervisor to NOT create a CIRCUITPYTHON_TERMINAL
# TileGrid on the display. This is supported in CP 10.x.
try:
    supervisor.runtime.display = None
except Exception:
    pass
