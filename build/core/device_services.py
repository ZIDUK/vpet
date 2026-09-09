"""CircuitPython implementations used by the options controller."""

import json
import os
import time

from core.save import load_pet, save_pet


WIFI_CONFIG_PATH = "/wifi_config.json"


class DeviceServices:
    def save(self, pet):
        return save_pet(pet)

    def load(self, pet):
        return load_pet(pet)

    def scan_wifi(self):
        radio = None
        scanning = False
        try:
            import wifi

            radio = wifi.radio
            networks = []
            scanner = radio.start_scanning_networks()
            scanning = True
            for network in scanner:
                name = str(network.ssid)
                if name and name not in networks:
                    networks.append(name)
                if len(networks) >= 7:
                    break
            return networks
        except (ImportError, OSError, RuntimeError):
            return []
        finally:
            if radio is not None and scanning:
                try:
                    radio.stop_scanning_networks()
                except (OSError, RuntimeError):
                    pass

    def _save_wifi(self, ssid, password):
        try:
            with open(WIFI_CONFIG_PATH, "w") as config_file:
                json.dump({"ssid": ssid, "password": password}, config_file)
            return True
        except (OSError, ValueError):
            return False

    def _load_wifi(self):
        try:
            with open(WIFI_CONFIG_PATH, "r") as config_file:
                data = json.load(config_file)
            ssid = data.get("ssid", "")
            password = data.get("password", "")
            return (ssid, password) if ssid else (None, None)
        except (OSError, ValueError, AttributeError):
            configured_ssid = os.getenv("CIRCUITPY_WIFI_SSID")
            password = os.getenv("CIRCUITPY_WIFI_PASSWORD")
            return configured_ssid, password

    def _has_internet(self, radio):
        sock = None
        try:
            import socketpool

            pool = socketpool.SocketPool(radio)
            address = pool.getaddrinfo("example.com", 80)[0][-1]
            sock = pool.socket(pool.AF_INET, pool.SOCK_STREAM)
            sock.settimeout(4)
            sock.connect(address)
            sock.send(b"HEAD / HTTP/1.0\r\nHost: example.com\r\n\r\n")
            response = sock.recv(16)
            return response.startswith(b"HTTP/")
        except (ImportError, OSError, RuntimeError, ValueError):
            return False
        finally:
            if sock is not None:
                try:
                    sock.close()
                except (OSError, RuntimeError):
                    pass

    def connect_wifi(self, ssid, password):
        try:
            import wifi

            if wifi.radio.connected and str(wifi.radio.ap_info.ssid) != ssid:
                wifi.radio.stop_station()
            if not wifi.radio.connected:
                wifi.radio.connect(ssid, password)
            if not self._save_wifi(ssid, password):
                return "SAVE ERROR"
            return "ONLINE" if self._has_internet(wifi.radio) else "NO INTERNET"
        except (ImportError, OSError, RuntimeError):
            return "WIFI ERROR"

    def auto_connect(self):
        ssid, password = self._load_wifi()
        if not ssid or password is None:
            return "NO WIFI SAVED"
        return self.connect_wifi(ssid, password)

    def get_datetime(self):
        current = time.localtime()
        return current.tm_year, current.tm_mon, current.tm_mday, current.tm_hour, current.tm_min

    def set_date(self, year, month, day):
        import rtc

        current = time.localtime()
        rtc.RTC().datetime = time.struct_time(
            (year, month, day, current.tm_hour, current.tm_min, 0, -1, -1, -1)
        )

    def set_time(self, hour, minute):
        import rtc

        current = time.localtime()
        rtc.RTC().datetime = time.struct_time(
            (current.tm_year, current.tm_mon, current.tm_mday, hour, minute, 0, -1, -1, -1)
        )
