"""Prevent CircuitPython's serial terminal from taking over the LCD."""
import supervisor

supervisor.runtime.autoreload = True

try:
    supervisor.runtime.display = None
except Exception:
    pass
