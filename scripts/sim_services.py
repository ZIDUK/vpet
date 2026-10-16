"""Safe desktop services for the simulator options menu."""

import json
import math
import os
import socket
import subprocess
import tempfile
import time
from datetime import datetime
from pathlib import Path

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
        self._clock_offset = 0
        self.connected_ssid = None
        self.wifi_status = "OFF"

    def save(self, pet):
        temporary = None
        try:
            self.save_path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=self.save_path.parent,
                prefix=f".{self.save_path.name}.", suffix=".tmp", delete=False,
            ) as stream:
                temporary = Path(stream.name)
                data = pet.to_dict()
                if self._clock_offset:
                    data["_sim_clock_offset"] = self._clock_offset
                json.dump(data, stream, separators=(",", ":"))
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.save_path)
            return True
        except (OSError, TypeError, ValueError):
            if temporary is not None:
                temporary.unlink(missing_ok=True)
            return False

    def load(self, pet):
        try:
            with self.save_path.open(encoding="utf-8") as stream:
                data = json.load(stream)
            if not isinstance(data, dict):
                return False
            offset = float(data.get("_sim_clock_offset", 0))
            if not math.isfinite(offset):
                return False
            snapshot = pet.to_dict()
            try:
                pet.load_from_dict(data)
            except (TypeError, ValueError, KeyError, OverflowError):
                pet.load_from_dict(snapshot)
                return False
            self._clock_offset = offset
            return True
        except (OSError, ValueError, TypeError, OverflowError):
            return False

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

    @property
    def clock(self):
        return datetime.fromtimestamp(time.time() + self._clock_offset)

    @clock.setter
    def clock(self, value):
        self._clock_offset = value.timestamp() - time.time()

    def exploration_time(self):
        # Encode local civil time so Monday caps follow the displayed calendar.
        return int((self.clock - datetime(1970, 1, 1)).total_seconds())

    def set_date(self, year, month, day):
        self.clock = self.clock.replace(year=year, month=month, day=day)

    def set_time(self, hour, minute):
        self.clock = self.clock.replace(hour=hour, minute=minute)
