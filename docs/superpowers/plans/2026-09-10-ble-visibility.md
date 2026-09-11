# BLE Visibility Implementation Plan

> **Historico.** El producto ya no usa `OPTION_BLUETOOTH = 4` ni un DIS suelto:
> Bluetooth es la primera opcion y el anuncio es HID teclado + DIS. Consulta
> `docs/architecture.md` y `docs/connectivity.md`.
>
> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the T-Display discoverable through BLE with a persistent Bluetooth toggle and no active WiFi feature.

**Architecture:** A board-only `BleService` owns NimBLE advertising and connection callbacks. `Settings` persists the preference. `App` toggles it and `Panels` displays its status. The simulator mirrors the state visually without using the host Bluetooth radio.

**Tech Stack:** PlatformIO 6.2.0, Arduino ESP32 2.0.17, NimBLE-Arduino 2.5.1, TFT_eSPI, NVS, Unity, pytest.

## Global Constraints

- Use `h2zero/NimBLE-Arduino@2.5.1`, never Bluetooth Classic.
- WiFi scan, association, password entry, Internet checking, and active WiFi UI are removed.
- Preserve `vpet_wifi` NVS values without reading them.
- Persist the off-by-default Bluetooth preference as `bluetooth` in `vpet_state`.
- Advertise as `vPet-XXXX`, where `XXXX` is the final four hexadecimal digits of `ESP.getEfuseMac()`.
- Publish read-only Device Information model, firmware version, and serial identifier characteristics.

---

### Task 1: Persist and Render Bluetooth Preference

**Files:**
- Modify: `firmware/t-display/lib/vpet_core/src/vpet/SettingsStore.h`
- Modify: `firmware/t-display/lib/vpet_core/src/vpet/SettingsStore.cpp`
- Modify: `firmware/t-display/test/test_native/test_settings.cpp`
- Modify: `src/core/options.py`
- Modify: `tests/test_options.py`

**Produces:** `Settings::bluetoothEnabled`; `OPTION_BLUETOOTH = 4`; exactly eight choices: language, sound, save, load, Bluetooth, date, time, back.

- [ ] **Step 1: Add a failing persistence test**

```cpp
vpet::Settings before;
before.bluetoothEnabled = true;
TEST_ASSERT_TRUE(vpet::SettingsStore(store).save(saved, before));
vpet::Settings after;
TEST_ASSERT_EQUAL(vpet::LoadResult::Loaded,
                  vpet::SettingsStore(store).load(restored, after));
TEST_ASSERT_TRUE(after.bluetoothEnabled);
```

- [ ] **Step 2: Run `make native-test` and confirm compilation fails because `bluetoothEnabled` is absent.**

- [ ] **Step 3: Add the portable setting and NVS access**

```cpp
struct Settings {
    std::string language = "ES";
    bool soundEnabled = true;
    bool bluetoothEnabled = false;
    int64_t manualEpochOffset = 0;
};
settings.bluetoothEnabled = store_.getInt("bluetooth", 0) != 0;
ok = store_.putInt("bluetooth", settings.bluetoothEnabled ? 1 : 0) && ok;
```

- [ ] **Step 4: Replace all simulator WiFi/password branches with this state transition**

```python
OPTION_BLUETOOTH = 4
elif self.index == OPTION_BLUETOOTH:
    self.bluetooth_enabled = not self.bluetooth_enabled
    self.bluetooth_status = "ADVERTISING" if self.bluetooth_enabled else "OFF"
```

- [ ] **Step 5: Add and run the Python assertion**

```python
session.index = OPTION_BLUETOOTH
assert session.action(_pet(), FakeServices()) is True
assert session.bluetooth_status == "ADVERTISING"
```

Run: `make native-test && python3 -m pytest tests/test_options.py -v`

Expected: all tests pass.

### Task 2: Add the NimBLE Board Adapter

**Files:**
- Modify: `firmware/t-display/platformio.ini`
- Create: `firmware/t-display/include/vpet/BleService.h`
- Create: `firmware/t-display/src/BleService.cpp`
- Modify: `firmware/t-display/src/main.cpp`

**Produces:** `BleStatus { Off, Advertising, Connected, Error }`, and `BleService::begin()`, `setEnabled(bool)`, `status()`, `deviceName()`.

- [ ] **Step 1: Pin NimBLE and declare the adapter**

```ini
lib_deps =
    bodmer/TFT_eSPI@2.5.43
    h2zero/NimBLE-Arduino@2.5.1
```

```cpp
enum class BleStatus : uint8_t { Off, Advertising, Connected, Error };
class BleService {
public:
    void begin();
    bool setEnabled(bool enabled);
    BleStatus status() const { return status_; }
    const char* deviceName() const { return deviceName_.c_str(); }
};
```

- [ ] **Step 2: Create the advertising server and Device Information service**

```cpp
NimBLEDevice::init(deviceName_.c_str());
NimBLEServer* server = NimBLEDevice::createServer();
NimBLEService* info = server->createService("180A");
info->createCharacteristic("2A24", NIMBLE_PROPERTY::READ)->setValue("vPet T-Display");
info->createCharacteristic("2A26", NIMBLE_PROPERTY::READ)->setValue("0.1.0");
info->createCharacteristic("2A25", NIMBLE_PROPERTY::READ)->setValue(deviceName_);
info->start();
```

Implement connect/disconnect callbacks: connection sets `Connected`; disconnection restarts advertising; disable calls `NimBLEDevice::deinit(true)` and sets `Off`; startup errors set `Error`.

- [ ] **Step 3: Replace active network construction in `main.cpp`**

```cpp
vpet::BleService bluetooth;
vpet::App app(renderer, panels, settingsStore, bluetooth);
// In setup(), after buttons.begin():
bluetooth.begin();
```

- [ ] **Step 4: Run `make firmware`**

Expected: `SUCCESS`, NimBLE appears in dependencies, while `WiFi` and `HTTPClient` do not.

### Task 3: Integrate BLE into App and Options UI

**Files:**
- Modify: `firmware/t-display/include/vpet/App.h`
- Modify: `firmware/t-display/src/App.cpp`
- Modify: `firmware/t-display/include/vpet/Panels.h`
- Modify: `firmware/t-display/src/Panels.cpp`
- Modify: `firmware/t-display/lib/vpet_core/src/vpet/Navigation.h`
- Modify: `firmware/t-display/lib/vpet_core/src/vpet/Navigation.cpp`
- Delete: `firmware/t-display/include/vpet/Esp32NetworkAdapter.h`
- Delete: `firmware/t-display/src/Esp32NetworkAdapter.cpp`
- Delete: `firmware/t-display/lib/vpet_core/src/vpet/NetworkService.h`
- Delete: `firmware/t-display/lib/vpet_core/src/vpet/NetworkService.cpp`
- Delete: `firmware/t-display/lib/vpet_core/src/vpet/PasswordEditor.h`
- Delete: `firmware/t-display/lib/vpet_core/src/vpet/PasswordEditor.cpp`
- Modify: `tests/test_tdisplay_deploy.py`

**Produces:** index 4 toggles BLE and saves it. `Panels` displays `BLUETOOTH: OFF`, `ADVERTISING`, `CONNECTED`, or `ERROR`.

- [ ] **Step 1: Restore persisted BLE in `App::begin`**

```cpp
settingsStore_.load(pet_, settings_);
bluetooth_.setEnabled(settings_.bluetoothEnabled);
```

- [ ] **Step 2: Replace the old index 4 flow**

```cpp
case 4:
    settings_.bluetoothEnabled = !settings_.bluetoothEnabled;
    if (!bluetooth_.setEnabled(settings_.bluetoothEnabled)) settings_.bluetoothEnabled = false;
    settingsStore_.save(pet_, settings_);
    break;
case 5: beginDateTime(true); break;
case 6: beginDateTime(false); break;
case 7: navigation_.setPanel(PanelId::Home); break;
```

Delete `WifiList` and `Password` panel IDs, panel input branches, `network_.poll()`, and WiFi/password render functions.

- [ ] **Step 3: Render exact status text**

```cpp
case BleStatus::Advertising: return "BLUETOOTH: ADVERTISING";
case BleStatus::Connected: return "BLUETOOTH: CONNECTED";
case BleStatus::Error: return "BLUETOOTH: ERROR";
case BleStatus::Off: return "BLUETOOTH: OFF";
```

- [ ] **Step 4: Replace the firmware source-contract test**

```python
assert '"BLUETOOTH: ADVERTISING"' in source
assert '"BLUETOOTH: CONNECTED"' in source
assert '"WIFI: ONLINE"' not in source
```

- [ ] **Step 5: Run `make test && make native-test && make firmware`**

Expected: all pass.

### Task 4: Simulator, Documentation, Deploy, and Phone Validation

**Files:**
- Modify: `scripts/sim.py`
- Modify: `scripts/sim_renderer.py`
- Modify: `tests/test_sim_renderer.py`
- Modify: `README.md`
- Modify: `docs/connectivity.md`
- Modify: `docs/architecture.md`
- Modify: `docs/hardware.md`
- Modify: `docs/hardware-notes.md`

**Produces:** simulator parity and an operator guide for a generic BLE scanner.

- [ ] **Step 1: Add a rendering test**

```python
session.index = OPTION_BLUETOOTH
session.action(_rookie(), FakeOptionsServices())
frame = render_frame(build_dir, _rookie(), menu_index=7, panel_mode="options", options_session=session, profile=get_display_profile("tdisplay"))
assert frame.size == (240, 135)
```

- [ ] **Step 2: Remove `services.auto_connect()`, WiFi labels, and password render modes; render Bluetooth at index 4.**

- [ ] **Step 3: Add this exact discovery flow to README and connectivity docs**

```text
1. Abre el engrane con ACTION.
2. Selecciona BLUETOOTH con NEXT.
3. Pulsa ACTION hasta ver BLUETOOTH: ADVERTISING.
4. En el telefono, abre nRF Connect o LightBlue y busca vPet-XXXX.
5. Al conectar, la tarjeta muestra BLUETOOTH: CONNECTED.
```

- [ ] **Step 4: Run and deploy**

Run: `make test && make native-test && make sim-record && make deploy PORT=/dev/cu.usbserial-57040013171`

Expected: all tests pass and deploy prints `Deploy OK`.

- [ ] **Step 5: Accept on a phone**

Enable Bluetooth, verify `ADVERTISING`, discover `vPet-XXXX` in nRF Connect or LightBlue, connect and verify `CONNECTED`, disconnect and verify it returns to `ADVERTISING`, then toggle off and confirm it disappears after a refreshed scan.

## Self-Review

- Spec coverage: preference, disabled WiFi, NimBLE advertising, unique name, Device Information, visible status, simulator parity, deployment, and phone verification are covered.
- Placeholder scan: no unresolved requirement remains.
- Type consistency: `bluetoothEnabled`, `BleStatus`, `BleService`, and option index 4 are defined before downstream use.
