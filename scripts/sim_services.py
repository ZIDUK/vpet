"""Safe desktop services for the simulator options menu."""

import copy
import json
import math
import os
import socket
import subprocess
import tempfile
import time
from datetime import datetime
from pathlib import Path
from core.sleep import SleepRoutine
from core.profile import PetProfile

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
        self.storage_blocked = False

    def evolve_and_save(self, pet, evolution):
        if getattr(pet,'cold',False):
            return False
        if not evolution.check(pet)[0]:
            return False
        before = copy.deepcopy(pet.__dict__)
        if not evolution.evolve(pet):
            return False
        if self.save(pet):
            return True
        pet.__dict__.clear()
        pet.__dict__.update(before)
        return False

    def start(self, pet):
        """Load/migrate, or persist a first egg, before allowing gameplay."""
        if self.load(pet):
            return True
        return not self.storage_blocked and self.save(pet)

    def save(self, pet):
        if self.storage_blocked:
            return False
        temporary = None
        try:
            self.save_path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=self.save_path.parent,
                prefix=f".{self.save_path.name}.", suffix=".tmp", delete=False,
            ) as stream:
                temporary = Path(stream.name)
                data = pet.to_dict()
                profile = None
                if hasattr(pet, "profile") and not pet.profile.pet_id:
                    random = os.urandom(16)
                    profile = PetProfile.from_words(tuple(int.from_bytes(random[i:i+4], "big") for i in range(0,16,4)))
                    data["profile"] = profile.encode()
                if self._clock_offset:
                    data["_sim_clock_offset"] = self._clock_offset
                json.dump(data, stream, separators=(",", ":"))
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.save_path)
            if profile is not None:
                pet.profile = profile
            return True
        except (OSError, TypeError, ValueError):
            if temporary is not None:
                temporary.unlink(missing_ok=True)
            return False

    def toggle_sleep(self, pet):
        if pet.is_egg or pet.dead or getattr(pet,'cold',False) or pet.exploration.away:
            return False
        before = copy.deepcopy(pet.__dict__)
        if pet.sleep.asleep:
            pet.sleep.stop()
        else:
            pet.sleep.start(self.exploration_time(), pet.dna[3])
        pet.answer_lights()
        if self.save(pet):
            return True
        pet.__dict__.clear()
        pet.__dict__.update(before)
        return False

    def advance_sleep(self, pet, elapsed_ms):
        if not pet.sleep.asleep or getattr(pet,'cold',False) or pet.exploration.away:
            return False
        before = pet.sleep.to_dict()
        stats, ev, dp = dict(pet.stats), dict(pet.ev), pet.dp
        injured_ms, dead = pet.injured_ms, pet.dead
        if pet.injured:
            pet.injured_ms = min(21600000, pet.injured_ms + elapsed_ms)
            pet._check_death()
        if pet.dead:
            pet.sleep.stop()
            complete = True
        else:
            pet.stats['e'], complete, reward = pet.sleep.advance_ms(elapsed_ms, pet.stats['e'])
            if reward:
                pet.stats['hp'] = min(100, pet.stats['hp'] + 5)
                pet.restore_dp()
                pet.gain_ev('mp', 2)
                pet.gain_ev('def', 1)
        checkpoint = before['elapsed']//300 != pet.sleep.elapsed//300
        if (complete or checkpoint) and not self.save(pet):
            pet.sleep = SleepRoutine(before)
            pet.stats, pet.ev, pet.dp = stats, ev, dp
            pet.injured_ms, pet.dead = injured_ms, dead
            return False
        return complete

    def load(self, pet):
        before = copy.deepcopy(pet.__dict__)
        previous_offset = self._clock_offset
        try:
            with self.save_path.open(encoding="utf-8") as stream:
                data = json.load(stream)
            if not isinstance(data, dict):
                raise ValueError("Invalid save")
            offset = float(data.get("_sim_clock_offset", 0))
            if not math.isfinite(offset):
                raise ValueError("Invalid clock offset")
            pet.load_from_dict(data)
            self._clock_offset = offset
            self.storage_blocked = False
            if not pet.profile.pet_id and not self.save(pet):
                raise OSError("Profile migration was not saved")
            return True
        except FileNotFoundError:
            self.storage_blocked = False
            return False
        except (OSError, ValueError, TypeError, KeyError, OverflowError):
            pet.__dict__.clear()
            pet.__dict__.update(before)
            self._clock_offset = previous_offset
            self.storage_blocked = True
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
