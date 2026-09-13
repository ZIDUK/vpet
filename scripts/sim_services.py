"""Safe desktop services for the simulator options menu."""

import json
import socket
import subprocess
from datetime import datetime
from pathlib import Path

from core.save import load_pet, save_pet


def clock_hour(clock, default=12):
    """Read hour from the shared get_datetime() 5-tuple."""
    if clock is None:
        return default
    return clock[3]


def format_clock(clock, empty="--"):
    """Format get_datetime() as YYYY/MM/DD HH:MM."""
    if not clock:
        return empty
    year, month, day, hour, minute = clock
    return "%04d/%02d/%02d %02d:%02d" % (year, month, day, hour, minute)


class SimulatorServices:
    def __init__(self, root):
        self.save_path = Path(root) / "out" / "sim_pet_save.json"
        self.wifi_path = Path(root) / "out" / "sim_wifi_config.json"
        self.clock = datetime.now().replace(second=0, microsecond=0)
        self.connected_ssid = None
        self.wifi_status = "OFF"

    def save(self, pet):
        self.save_path.parent.mkdir(parents=True, exist_ok=True)
        return save_pet(pet, self.save_path)

    def load(self, pet):
        return load_pet(pet, self.save_path)

    def scan_wifi(self):
        try:
            result = subprocess.run(
                ["networksetup", "-listpreferredwirelessnetworks", "en0"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return ["SIMULATED WIFI"]
        networks = [line.strip() for line in result.stdout.splitlines()[1:] if line.strip()]
        return networks[:7] or ["SIMULATED WIFI"]

    def _has_internet(self):
        connection = None
        try:
            connection = socket.create_connection(("example.com", 80), timeout=3)
            connection.sendall(b"HEAD / HTTP/1.0\r\nHost: example.com\r\n\r\n")
            return connection.recv(16).startswith(b"HTTP/")
        except OSError:
            return False
        finally:
            if connection is not None:
                connection.close()

    def connect_wifi(self, ssid, password):
        self.connected_ssid = ssid
        if not self._has_internet():
            self.wifi_status = "NO INTERNET"
            return self.wifi_status
        self.wifi_path.parent.mkdir(parents=True, exist_ok=True)
        self.wifi_path.write_text(json.dumps({"ssid": ssid, "password": password}))
        self.wifi_status = "ONLINE"
        return "SIM ONLINE"

    def auto_connect(self):
        try:
            data = json.loads(self.wifi_path.read_text())
            return self.connect_wifi(data["ssid"], data["password"])
        except (OSError, ValueError, KeyError, TypeError):
            self.wifi_status = "OFF"
            return "NO WIFI SAVED"

    def get_datetime(self):
        value = self.clock
        return value.year, value.month, value.day, value.hour, value.minute

    def set_date(self, year, month, day):
        self.clock = self.clock.replace(year=year, month=month, day=day)

    def set_time(self, hour, minute):
        self.clock = self.clock.replace(hour=hour, minute=minute)
