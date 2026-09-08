# LILYGO T-Display PlatformIO Port Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `make sim` render the complete vPet at 240x135 and make `make deploy` safely build, back up, upload and verify the same game on the original 16 MB LILYGO T-Display.

**Architecture:** Keep Python as the asset/catalog source of truth and desktop simulator, then export a compact manifest plus native tables consumed by an Arduino firmware under `firmware/t-display`. Store indexed animation assets in LittleFS, persistent state in NVS, and enforce flash, filesystem, static-RAM and startup-heap budgets before declaring deployment successful.

**Tech Stack:** Python 3, Pillow, pygame, pytest, PlatformIO Core 6.2.0, `platformio/espressif32@7.0.1`, Arduino ESP32 2.0.17, `bodmer/TFT_eSPI@2.5.43`, LittleFS, Preferences/NVS, esptool.

## Global Constraints

- Target only the classic ESP32-D0WDQ6-V3 T-Display with 16 MB flash and no PSRAM.
- Use the ST7789V at 240x135 landscape: MOSI 19, SCLK 18, CS 5, DC 16, RST 23 and backlight 4.
- Map active-low GPIO35 to NEXT and active-low GPIO0 to ACTION; GPIO35 long press is BACK.
- Keep the menu at 240x24 and the content rectangle at `(0, 24, 240, 111)`.
- Normal pet sprites fit inside 88x88; overview portraits fit inside 36x36; menu icons fit inside 20x20.
- Use nearest-neighbor image scaling and transparent palette index zero.
- `make sim` must not require PlatformIO or alter the Mac network/clock.
- `make deploy` targets T-Display; `make deploy-pico` preserves the existing CircuitPython pipeline.
- Never erase the whole board during a normal deploy and never erase NVS.
- Require 10 percent free space in application and LittleFS partitions, 64 KiB startup free heap and 48 KiB minimum heap.
- Keep Flamemon-to-Dragfiremon gameplay requirements unassigned; simulator key `e` remains the development-only evolution trigger.

---

## File Map

| Path | Responsibility |
|---|---|
| `src/display_profiles.py` | Immutable Pico and T-Display dimensions used by Python tools |
| `src/config.py` | Select the active Python display profile and expose layout constants |
| `scripts/build.py` | Existing Pico builder plus shared source-art discovery |
| `scripts/build_tdisplay.py` | Generate indexed native assets, native catalog tables and manifest |
| `scripts/sim.py` | Run the default T-Display simulator and optional Pico profile |
| `scripts/sim_renderer.py` | Compose the profile-sized pygame/Pillow framebuffer |
| `scripts/deploy_tdisplay.py` | Detect, back up, budget, upload and verify the ESP32 |
| `scripts/deploy.py` | Preserved Pico manifest deployment implementation |
| `firmware/t-display/platformio.ini` | Pinned native toolchain, dependency and build flags |
| `firmware/t-display/partitions.csv` | Fixed 16 MB NVS/app/LittleFS/coredump map |
| `firmware/t-display/include/User_Setup.h` | Project-owned TFT_eSPI ST7789 pin setup |
| `firmware/t-display/lib/vpet_core/src/vpet/*` | Arduino-independent state, input, motion and navigation logic |
| `firmware/t-display/include/vpet/*.h` | ESP32 display, storage and network adapter interfaces |
| `firmware/t-display/src/*.cpp` | Arduino/TFT_eSPI/ESP32 adapter implementation |
| `firmware/t-display/data/` | Generated LittleFS payload |
| `firmware/t-display/test/test_native/` | PlatformIO native tests for portable logic |
| `tests/test_display_profiles.py` | Python profile and geometry tests |
| `tests/test_tdisplay_assets.py` | Native asset/manifest contract tests |
| `tests/test_tdisplay_deploy.py` | Deployment behavior and diagnostics tests |

---

### Task 1: Preserve Pico Targets And Add The 240x135 Profile

**Files:**
- Create: `src/display_profiles.py`
- Modify: `src/config.py`
- Modify: `Makefile`
- Modify: `scripts/sim.py`
- Create: `tests/test_display_profiles.py`
- Modify: `tests/test_pipeline.py`

**Interfaces:**
- Produces: `DisplayProfile` and `get_display_profile(name: str) -> DisplayProfile`.
- Produces: CLI `scripts/sim.py --profile {tdisplay,pico}` while the Makefile continues using Pico until Task 2 supplies the complete T-Display artifact.
- Produces: Make targets `deploy-pico` and `sim-pico` while reserving the final `deploy` switch for Task 8.

- [ ] **Step 1: Write failing profile and Makefile tests**

```python
from display_profiles import get_display_profile


def test_tdisplay_profile_is_default_landscape_geometry():
    profile = get_display_profile("tdisplay")
    assert (profile.width, profile.height) == (240, 135)
    assert (profile.menu_height, profile.cell_width) == (24, 30)
    assert profile.content_rect == (0, 24, 240, 111)
    assert profile.pet_size == 88


def test_pico_profile_remains_available():
    profile = get_display_profile("pico")
    assert (profile.width, profile.height) == (128, 128)
```

Add a Makefile assertion to `tests/test_pipeline.py`:

```python
def test_makefile_keeps_explicit_pico_compatibility_targets():
    makefile = (ROOT / "Makefile").read_text()
    assert "deploy-pico:" in makefile
    assert "sim-pico:" in makefile
    assert "scripts/deploy.py" in makefile
```

- [ ] **Step 2: Run focused tests and confirm the missing module/targets fail**

Run: `python3 -m pytest tests/test_display_profiles.py tests/test_pipeline.py::test_makefile_keeps_explicit_pico_compatibility_targets -v`

Expected: FAIL because `display_profiles` and the two compatibility targets do not exist.

- [ ] **Step 3: Add immutable profiles and CLI selection**

Create `src/display_profiles.py` with this public contract:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class DisplayProfile:
    name: str
    width: int
    height: int
    menu_height: int
    cell_width: int
    icon_size: int
    pet_size: int
    portrait_size: int

    @property
    def content_rect(self):
        return (0, self.menu_height, self.width, self.height - self.menu_height)


PROFILES = {
    "tdisplay": DisplayProfile("tdisplay", 240, 135, 24, 30, 20, 88, 36),
    "pico": DisplayProfile("pico", 128, 128, 16, 16, 14, 64, 32),
}


def get_display_profile(name="tdisplay"):
    try:
        return PROFILES[name]
    except KeyError as error:
        raise ValueError(f"Unknown display profile: {name}") from error
```

Add `--profile` to `scripts/sim.py`, pass the selected profile to build/render
calls, and make T-Display the default. Refactor `src/config.py` to derive width,
height, menu, pet bounds and portrait size from `VPET_DISPLAY_PROFILE`, keeping
existing path and frame constants unchanged.

Update the Makefile target bodies without changing the current default `sim`
target yet:

```make
sim-pico: build
	$(SIM_PY) scripts/sim.py --profile pico

deploy-pico: build test
	$(PY) scripts/deploy.py
```

- [ ] **Step 4: Run profile and legacy tests**

Run: `python3 -m pytest tests/test_display_profiles.py tests/test_pipeline.py -v`

Expected: PASS, including proof that Pico deployment still calls `scripts/deploy.py`.

- [ ] **Step 5: Commit the profile boundary**

```bash
git add Makefile src/display_profiles.py src/config.py scripts/sim.py tests/test_display_profiles.py tests/test_pipeline.py
git commit -m "feat: add T-Display screen profile"
```

---

### Task 2: Render The Existing Game At 240x135

**Files:**
- Modify: `scripts/build.py`
- Modify: `scripts/sim_renderer.py`
- Modify: `src/ui/status.py`
- Modify: `tests/test_sim_renderer.py`
- Modify: `tests/test_pipeline.py`

**Interfaces:**
- Consumes: `DisplayProfile` from Task 1.
- Produces: `render_frame(..., profile: DisplayProfile)` returning a profile-sized Pillow image.
- Produces: `scripts/build.py --profile tdisplay --output build-tdisplay` with day/night backgrounds, icons, portraits and sprite atlases sized for the selected profile.

- [ ] **Step 1: Add failing 240x135 pixel-contract tests**

Add assertions that build and render T-Display assets:

```python
def test_tdisplay_renderer_uses_approved_geometry(built_tdisplay):
    frame = render_frame(built_tdisplay, _rookie(), 7, 0, profile=get_display_profile("tdisplay"))
    assert frame.size == (240, 135)
    assert frame.getpixel((0, 23)) != frame.getpixel((0, 24))
    assert selector_bounds(frame) == (210, 0, 239, 23)


def test_every_visible_pixel_stays_inside_content_bounds(built_tdisplay):
    for species in ("rookie", "champion", "ultimate"):
        frame = render_species_at_motion_extremes(built_tdisplay, species)
        assert non_background_bounds(frame.crop((0, 24, 240, 135))) <= (0, 0, 240, 111)
```

- [ ] **Step 2: Run the renderer tests and confirm 128x128 assumptions fail**

Run: `python3 -m pytest tests/test_sim_renderer.py tests/test_pipeline.py -v`

Expected: FAIL on framebuffer size, fixed 16-pixel cells and fixed status panel width.

- [ ] **Step 3: Make builders and renderers profile-aware**

Change build helpers to receive output sizes explicitly:

```python
def collect_background(profile, output_root): ...
def collect_pet_images(profile, output_root): ...
def collect_ui(profile, output_root): ...
def collect_evolution_thumbnails(profile, output_root): ...
```

For T-Display, resize source art directly to 88x88, transitions to at most
120x111, portraits to 36x36 and icons to 20x20. Preserve `_quantize_rgba_with_transparency`
and ensure palette index zero is transparent. Replace every fixed menu and panel
coordinate in `scripts/sim_renderer.py` and `src/ui/status.py` with values from
the profile. Make panel drawing accept `(width, height)` and clip all writes.

Add the first complete T-Display targets:

```make
build-pico:
	$(PY) scripts/build.py --profile pico --output build

build-tdisplay:
	$(PY) scripts/build.py --profile tdisplay --output build-tdisplay

sim: build-tdisplay
	$(SIM_PY) scripts/sim.py --profile tdisplay --build-dir build-tdisplay
```

- [ ] **Step 4: Verify both profile renders and inspect a recorded frame**

Run: `python3 -m pytest tests/test_sim_renderer.py tests/test_pipeline.py -v`

Run: `SDL_VIDEODRIVER=dummy python3 scripts/sim.py --profile tdisplay --build-dir build-tdisplay --max-frames 3 --record out/tdisplay-smoke`

Expected: PASS and `out/tdisplay-smoke/frame_0002.png` is exactly 240x135.

- [ ] **Step 5: Commit the wide simulator**

```bash
git add scripts/build.py scripts/sim_renderer.py src/ui/status.py tests/test_sim_renderer.py tests/test_pipeline.py
git commit -m "feat: render vPet at 240x135"
```

---

### Task 3: Generate Compact LittleFS Assets And Native Catalogs

**Files:**
- Create: `scripts/tdisplay_assets.py`
- Create: `scripts/build_tdisplay.py`
- Create: `tests/test_tdisplay_assets.py`
- Create: `firmware/t-display/data/.gitkeep`
- Create: `firmware/t-display/include/generated/.gitkeep`
- Modify: `Makefile`
- Modify: `.gitignore`

**Interfaces:**
- Produces: `build_tdisplay.build(root: Path) -> dict` while retaining the simulator BMPs under `build-tdisplay`.
- Produces: one `.vpa` indexed asset per animation/background under `firmware/t-display/data`.
- Produces: `firmware/t-display/data/manifest.json` and `firmware/t-display/include/generated/catalog.h`.
- `.vpa` header: magic `VPA1`, uint16 width/height/frame_count/palette_count, uint8 transparent_index, RGB565 palette, then uint32 frame offsets and indexed pixels.

- [ ] **Step 1: Write failing binary-format and manifest tests**

```python
def test_vpa_round_trip_preserves_transparency_and_dimensions(tmp_path):
    source = rgba_test_frames()
    payload = encode_vpa(source, width=88, height=88)
    decoded = decode_vpa(payload)
    assert decoded.size == (88, 88)
    assert decoded.frame_count == len(source)
    assert decoded.transparent_index == 0


def test_native_manifest_covers_every_registered_animation(tdisplay_build):
    manifest = json.loads((tdisplay_build / "manifest.json").read_text())
    assert manifest["display"] == {"width": 240, "height": 135, "menu_height": 24}
    assert set(manifest["species"]) == {"rookie", "champion", "ultimate"}
    assert all(item["sha256"] and item["bytes"] > 0 for item in manifest["assets"])
```

- [ ] **Step 2: Run tests and confirm encoder/build entrypoint are absent**

Run: `python3 -m pytest tests/test_tdisplay_assets.py -v`

Expected: FAIL importing `scripts.tdisplay_assets`.

- [ ] **Step 3: Implement deterministic indexed assets and generated header**

Implement these exact Python functions:

```python
def encode_vpa(frames: list[Image.Image], width: int, height: int) -> bytes: ...
def decode_vpa(payload: bytes) -> DecodedAsset: ...
def write_asset(path: Path, frames: list[Image.Image], size: tuple[int, int]) -> dict: ...
def write_manifest(data_dir: Path, records: list[dict], catalog: dict) -> Path: ...
def write_catalog_header(include_dir: Path, catalog: dict) -> Path: ...
```

Quantize a complete animation against one shared palette, reserve index zero
for transparency, serialize little-endian fields with `struct.pack`, and sort
all manifest entries by POSIX path before hashing. Export species IDs, animation
paths/counts, menu actions and evolution edges as `constexpr` arrays in
`generated/catalog.h`.

Replace the Task 2 native-build target so it first creates the simulator BMPs
and then the native package:

```make
build-tdisplay:
	$(PY) scripts/build.py --profile tdisplay --output build-tdisplay
	$(PY) scripts/build_tdisplay.py --sim-build build-tdisplay

build: build-pico build-tdisplay
```

Ignore `.pio/`, `.venv-platformio/` and generated `firmware/t-display/data/*`
and `firmware/t-display/include/generated/*`, while retaining each `.gitkeep`.

- [ ] **Step 4: Run deterministic build twice and compare hashes**

Run: `python3 -m pytest tests/test_tdisplay_assets.py -v`

Run: `python3 scripts/build_tdisplay.py && shasum -a 256 firmware/t-display/data/manifest.json > /tmp/vpet-manifest-1 && python3 scripts/build_tdisplay.py && shasum -a 256 -c /tmp/vpet-manifest-1`

Expected: tests PASS and checksum reports `OK`.

- [ ] **Step 5: Commit the native asset pipeline**

```bash
git add Makefile .gitignore scripts/tdisplay_assets.py scripts/build_tdisplay.py tests/test_tdisplay_assets.py firmware/t-display/data/.gitkeep firmware/t-display/include/generated/.gitkeep
git commit -m "feat: generate compact T-Display assets"
```

---

### Task 4: Bootstrap PlatformIO, TFT And Physical Buttons

**Files:**
- Create: `scripts/bootstrap_platformio.sh`
- Create: `firmware/t-display/platformio.ini`
- Create: `firmware/t-display/partitions.csv`
- Create: `firmware/t-display/include/User_Setup.h`
- Create: `firmware/t-display/lib/vpet_core/src/vpet/Input.h`
- Create: `firmware/t-display/lib/vpet_core/src/vpet/Input.cpp`
- Create: `firmware/t-display/include/vpet/BoardInput.h`
- Create: `firmware/t-display/src/BoardInput.cpp`
- Create: `firmware/t-display/include/vpet/AssetStore.h`
- Create: `firmware/t-display/src/AssetStore.cpp`
- Create: `firmware/t-display/src/main.cpp`
- Create: `firmware/t-display/test/test_native/test_input.cpp`
- Modify: `Makefile`

**Interfaces:**
- Produces: local executable `.venv-platformio/bin/pio`.
- Produces: `InputEvent { None, Next, Action, Back }` and `Input::poll(uint32_t nowMs)`.
- Produces: boot-time display, LittleFS mount, manifest check and `VPET_READY` telemetry.

- [ ] **Step 1: Write native input tests**

```cpp
void test_short_next_press() {
    FakePins pins;
    Input input(pins, 25, 700);
    pins.press(35, 100); pins.release(35, 180);
    TEST_ASSERT_EQUAL(InputEvent::Next, input.poll(200));
}

void test_long_next_press_becomes_back() {
    FakePins pins;
    Input input(pins, 25, 700);
    pins.press(35, 100); pins.release(35, 900);
    TEST_ASSERT_EQUAL(InputEvent::Back, input.poll(910));
}
```

- [ ] **Step 2: Add pinned PlatformIO configuration and confirm native tests fail**

Create `scripts/bootstrap_platformio.sh` as an idempotent bootstrap:

```bash
#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$ROOT/.venv-platformio"
test -x "$VENV/bin/python" || python3 -m venv "$VENV"
"$VENV/bin/python" -m pip install --disable-pip-version-check "platformio==6.2.0"
"$VENV/bin/pio" --version
```

Use this core configuration:

```ini
[platformio]
default_envs = tdisplay
data_dir = data

[env:tdisplay]
platform = platformio/espressif32@7.0.1
board = esp32dev
framework = arduino
board_build.flash_size = 16MB
board_build.partitions = partitions.csv
board_build.filesystem = littlefs
monitor_speed = 115200
upload_speed = 921600
lib_deps = bodmer/TFT_eSPI@2.5.43
build_flags = -DUSER_SETUP_LOADED -include include/User_Setup.h

[env:native]
platform = platformio/native@1.2.1
test_framework = unity
test_build_src = no
```

Use this exact partition table:

```csv
# Name,     Type, SubType, Offset,   Size,     Flags
nvs,        data, nvs,     0x9000,   0x5000,
app0,       app,  factory, 0x10000,  0x400000,
littlefs,   data, spiffs,  0x410000, 0xBE0000,
coredump,   data, coredump,0xFF0000, 0x10000,
```

The project-owned TFT setup contains:

```cpp
#pragma once
#define ST7789_DRIVER
#define TFT_WIDTH 135
#define TFT_HEIGHT 240
#define CGRAM_OFFSET
#define TFT_MOSI 19
#define TFT_SCLK 18
#define TFT_CS 5
#define TFT_DC 16
#define TFT_RST 23
#define TFT_BL 4
#define TFT_BACKLIGHT_ON HIGH
#define LOAD_GLCD
#define LOAD_FONT2
#define SPI_FREQUENCY 40000000
#define SPI_READ_FREQUENCY 20000000
```

Run: `scripts/bootstrap_platformio.sh && .venv-platformio/bin/pio test -d firmware/t-display -e native`

Expected: FAIL because `Input` is not implemented.

- [ ] **Step 3: Implement display setup, debounce and readiness telemetry**

Configure `User_Setup.h` with `ST7789_DRIVER`, `TFT_WIDTH 135`, `TFT_HEIGHT 240`,
the confirmed pins, `SPI_FREQUENCY 40000000` and loaded fonts 1 and 2. In
`setup()`, enable GPIO4, initialize TFT rotation 1, mount LittleFS, validate
`/manifest.json`, initialize GPIO35/GPIO0 as inputs, and render a bounded boot
screen. Emit one machine-readable line:

```cpp
Serial.printf(
  "VPET_READY heap_free=%u heap_min=%u flash=%u fs_used=%u fs_total=%u manifest=%s\n",
  ESP.getFreeHeap(), ESP.getMinFreeHeap(), ESP.getFlashChipSize(),
  LittleFS.usedBytes(), LittleFS.totalBytes(), manifest.version.c_str());
```

Keep `Input` portable by accepting `ButtonSample { bool nextDown; bool
actionDown; }` from its caller. Implement 25 ms debounce and a 700 ms GPIO35
long press. `BoardInput` performs only `digitalRead` and passes samples into the
portable state machine. Never block in `loop()` and never assign a long-press
action to GPIO0.

- [ ] **Step 4: Run native tests and compile firmware**

Run: `.venv-platformio/bin/pio test -d firmware/t-display -e native`

Run: `.venv-platformio/bin/pio run -d firmware/t-display -e tdisplay`

Expected: native tests PASS and firmware reports program/RAM usage without overflow.

- [ ] **Step 5: Commit the hardware bootstrap**

```bash
git add Makefile scripts/bootstrap_platformio.sh firmware/t-display
git commit -m "feat: boot T-Display firmware"
```

---

### Task 5: Port Pet State, Motion And Action Animations

**Files:**
- Create: `firmware/t-display/lib/vpet_core/src/vpet/PetState.h`
- Create: `firmware/t-display/lib/vpet_core/src/vpet/PetState.cpp`
- Create: `firmware/t-display/lib/vpet_core/src/vpet/Motion.h`
- Create: `firmware/t-display/lib/vpet_core/src/vpet/Motion.cpp`
- Create: `firmware/t-display/include/vpet/Renderer.h`
- Create: `firmware/t-display/src/Renderer.cpp`
- Create: `firmware/t-display/include/vpet/App.h`
- Create: `firmware/t-display/src/App.cpp`
- Modify: `firmware/t-display/src/main.cpp`
- Create: `firmware/t-display/test/test_native/test_motion.cpp`
- Create: `firmware/t-display/test/test_native/test_pet_state.cpp`

**Interfaces:**
- Produces: `PetState::apply(Action)`, `PetState::tick(uint32_t elapsedMs)` and `PetState::evolveTo(SpeciesId)`.
- Produces: `Motion::tick(nowMs, frameWidth)` with x constrained to `0..(240-frameWidth)` and y constrained to `24..(135-frameHeight)`.
- Produces: `Renderer::draw(const AppViewModel&)` using indexed `.vpa` frames and bounded RGB565 scan lines.

- [ ] **Step 1: Add parity tests for state and movement**

```cpp
void test_dragfiremon_moves_with_fly_state() {
    Motion motion(240, 135, 24, 88);
    motion.setSpecies(SpeciesId::Ultimate);
    motion.startWalking(1000);
    TEST_ASSERT_EQUAL(AnimationId::DragfiremonFly, motion.animation());
    for (uint32_t now = 1000; now < 20000; now += 16) motion.tick(now);
    TEST_ASSERT_TRUE(motion.x() >= 0 && motion.x() <= 152);
}

void test_feed_updates_stats_once_when_animation_completes() {
    PetState pet;
    pet.beginAction(Action::Feed);
    pet.completeAction();
    TEST_ASSERT_EQUAL(100, pet.hunger());
    TEST_ASSERT_EQUAL(1, pet.meals());
}
```

- [ ] **Step 2: Run native tests and confirm portable classes are missing**

Run: `.venv-platformio/bin/pio test -d firmware/t-display -e native`

Expected: FAIL compiling missing `PetState`, `Motion`, `Renderer` and `App` headers.

- [ ] **Step 3: Implement the non-blocking gameplay loop**

Mirror Python's menu order and route Feed to eat, Training to punch, Rest to
sleep/night, and Battle to cast. Implement autonomous random idle/movement
durations using the same ranges and frame intervals as `src/config.py`. Load one
frame at a time through `AssetStore`; decode palette indices into a fixed
`uint16_t line[240]` buffer and call TFT_eSPI `pushImage` for visible runs.
Clear the previous sprite rectangle from the cached background before drawing
the next frame. Horizontal flips happen during scan-line conversion and allocate
no second frame buffer.

- [ ] **Step 4: Verify portable logic and embedded compile**

Run: `.venv-platformio/bin/pio test -d firmware/t-display -e native`

Run: `.venv-platformio/bin/pio run -d firmware/t-display -e tdisplay`

Expected: all native tests PASS and the embedded binary remains below 90 percent of the 4 MB app partition.

- [ ] **Step 5: Commit native gameplay**

```bash
git add firmware/t-display/lib/vpet_core firmware/t-display/include/vpet firmware/t-display/src firmware/t-display/test/test_native
git commit -m "feat: port vPet gameplay to ESP32"
```

---

### Task 6: Port Status, Inventory, Evolution And Options Panels

**Files:**
- Create: `firmware/t-display/include/vpet/Panels.h`
- Create: `firmware/t-display/src/Panels.cpp`
- Create: `firmware/t-display/lib/vpet_core/src/vpet/Navigation.h`
- Create: `firmware/t-display/lib/vpet_core/src/vpet/Navigation.cpp`
- Modify: `firmware/t-display/include/vpet/App.h`
- Modify: `firmware/t-display/src/App.cpp`
- Create: `firmware/t-display/test/test_native/test_navigation.cpp`
- Modify: `tests/test_sim_renderer.py`
- Modify: `scripts/sim.py`
- Create: `scripts/render_panel_tour.py`

**Interfaces:**
- Produces: `PanelId { Home, Status, Inventory, EvolutionTree, EvolutionDetail, Options, WifiList, Password, DateTime }`.
- Produces: `Navigation::dispatch(InputEvent)` with identical simulator/board transitions.
- Consumes: generated species/evolution catalog and `PetState.discoveredSpecies()`.
- Produces: deterministic `scripts/render_panel_tour.py --output PATH` screenshots for visual regression review.

- [ ] **Step 1: Write navigation and evolution-discovery tests**

```cpp
void test_hidden_branch_does_not_reveal_identity() {
    Navigation navigation(catalogWithSiblingUltimate());
    navigation.openEvolutionTree(discovered({SpeciesId::Firemon, SpeciesId::Flamemon}));
    navigation.select(SpeciesId::UnknownUltimate);
    auto node = navigation.selectedEvolutionNode();
    TEST_ASSERT_TRUE(node.hidden);
    TEST_ASSERT_EQUAL_STRING("???", node.label);
}

void test_back_returns_from_detail_to_same_tree_node() {
    Navigation navigation(defaultCatalog());
    navigation.select(SpeciesId::Dragfiremon);
    navigation.dispatch(InputEvent::Action);
    navigation.dispatch(InputEvent::Back);
    TEST_ASSERT_EQUAL(PanelId::EvolutionTree, navigation.panel());
    TEST_ASSERT_EQUAL(SpeciesId::Dragfiremon, navigation.selectedSpecies());
}
```

- [ ] **Step 2: Run native and Python panel tests and confirm failures**

Run: `.venv-platformio/bin/pio test -d firmware/t-display -e native`

Run: `python3 -m pytest tests/test_sim_renderer.py -v`

Expected: FAIL until native panel navigation and wide Python panel layouts exist.

- [ ] **Step 3: Implement bounded panel renderers and shared navigation rules**

Draw directly in the 240x111 content rectangle. Use the generated pixel font,
36x36 evolution portraits, an 88x88 detail portrait, yellow selected borders
and black `???` silhouettes. Implement left-to-right/top-to-bottom branch
traversal and explicit BACK nodes. Status reads current values; inventory uses
persisted quantities; options exposes language, sound preference, save, load,
WiFi and date/time. All labels pass through a width-aware clipping helper:

```cpp
void Panels::drawLabel(const char* text, Rect bounds, TextAlign align) {
    const String fitted = font_.ellipsize(text, bounds.w);
    renderer_.drawText(fitted.c_str(), bounds, align);
}
```

- [ ] **Step 4: Run panel tests and produce simulator snapshots**

Run: `.venv-platformio/bin/pio test -d firmware/t-display -e native`

Run: `python3 -m pytest tests/test_sim_renderer.py -v`

Run: `python3 scripts/render_panel_tour.py --build-dir build-tdisplay --output out/tdisplay-panels`

Expected: PASS; recorded status, evolution and options frames are 240x135 with no non-background pixels outside their panel bounds.

- [ ] **Step 5: Commit native panels**

```bash
git add firmware/t-display/lib/vpet_core firmware/t-display/include/vpet firmware/t-display/src firmware/t-display/test/test_native scripts/sim.py scripts/render_panel_tour.py tests/test_sim_renderer.py
git commit -m "feat: add T-Display vPet panels"
```

---

### Task 7: Add NVS Saves, WiFi, Internet Check And Clock

**Files:**
- Create: `firmware/t-display/lib/vpet_core/src/vpet/SettingsStore.h`
- Create: `firmware/t-display/lib/vpet_core/src/vpet/SettingsStore.cpp`
- Create: `firmware/t-display/lib/vpet_core/src/vpet/NetworkService.h`
- Create: `firmware/t-display/lib/vpet_core/src/vpet/NetworkService.cpp`
- Create: `firmware/t-display/include/vpet/NvsKeyValueStore.h`
- Create: `firmware/t-display/src/NvsKeyValueStore.cpp`
- Create: `firmware/t-display/include/vpet/Esp32NetworkAdapter.h`
- Create: `firmware/t-display/src/Esp32NetworkAdapter.cpp`
- Modify: `firmware/t-display/include/vpet/App.h`
- Modify: `firmware/t-display/src/App.cpp`
- Create: `firmware/t-display/test/test_native/test_settings.cpp`
- Create: `firmware/t-display/test/test_native/test_password_editor.cpp`

**Interfaces:**
- Produces: `SettingsStore::load(PetState&, Settings&) -> LoadResult` and `save(...) -> bool`.
- Produces: NVS schema version 1 in namespaces `vpet_state`, `vpet_config`, `vpet_wifi`.
- Produces: asynchronous `NetworkService::startScan`, `connect`, `poll` and `syncClock`.

- [ ] **Step 1: Write serialization and password-editor tests**

```cpp
void test_old_or_missing_save_seeds_current_species_discovery() {
    FakePreferences nvs;
    nvs.putString("species", "champion");
    PetState pet;
    Settings settings;
    SettingsStore(nvs).load(pet, settings);
    TEST_ASSERT_TRUE(pet.hasDiscovered(SpeciesId::Flamemon));
}

void test_credentials_are_saved_only_after_internet_capable_connection() {
    FakePreferences nvs;
    FakeWifi wifi;
    wifi.result = ConnectResult::InternetAvailable;
    NetworkService service(wifi, nvs);
    service.connect("Home", "secret");
    service.poll();
    TEST_ASSERT_EQUAL_STRING("Home", nvs.getString("ssid").c_str());
}
```

- [ ] **Step 2: Run native tests and confirm persistence/network classes are absent**

Run: `.venv-platformio/bin/pio test -d firmware/t-display -e native`

Expected: FAIL compiling the missing classes.

- [ ] **Step 3: Implement versioned NVS and bounded asynchronous networking**

Keep `SettingsStore` portable behind a `KeyValueStore` interface and keep
`NetworkService` portable behind a `NetworkAdapter` interface; the two ESP32
adapters own Preferences, WiFi, DNS, HTTP and NTP calls. Serialize stats,
inventory and discovered IDs as versioned values. Save WiFi
credentials only after association plus DNS and HTTP success. Distinguish
`NoAssociation`, `LocalOnly` and `InternetAvailable` on screen. Use
`WiFi.scanNetworks(true)` and poll completion, a five-second connection timeout,
DNS lookup, and an HTTP request with a five-second timeout. Use `configTzTime`
for NTP and persist a manual epoch offset when offline. Reuse uppercase,
lowercase, number and symbol modes plus `DEL`, `CONNECT` and `CANCEL` from the
Python editor.

- [ ] **Step 4: Run all native and Python options tests**

Run: `.venv-platformio/bin/pio test -d firmware/t-display -e native`

Run: `python3 -m pytest tests/test_options.py tests/test_sim_renderer.py -v`

Expected: PASS, including no credential write after failed connectivity.

- [ ] **Step 5: Commit persistence and connectivity**

```bash
git add firmware/t-display/lib/vpet_core firmware/t-display/include/vpet firmware/t-display/src firmware/t-display/test/test_native
git commit -m "feat: persist and connect T-Display vPet"
```

---

### Task 8: Implement Safe T-Display Deployment And Memory Diagnostics

**Files:**
- Create: `scripts/tdisplay_device.py`
- Create: `scripts/deploy_tdisplay.py`
- Create: `tests/test_tdisplay_deploy.py`
- Modify: `Makefile`
- Modify: `.gitignore`

**Interfaces:**
- Produces: `detect_board(port: str | None) -> BoardInfo`.
- Produces: `ensure_backup(board: BoardInfo, output: Path) -> Path`.
- Produces: `classify_memory(report: BuildReport, telemetry: ReadyTelemetry) -> list[Diagnostic]`.
- Produces: `deploy(port=None, upload_speed=921600) -> ReadyTelemetry`.

- [ ] **Step 1: Write deployment tests with mocked subprocess and serial data**

```python
def test_first_deploy_reads_full_16mb_flash_before_upload(fake_runner, tmp_path):
    board = classic_esp32_board(flash_size=16 * 1024 * 1024)
    deploy(board=board, output=tmp_path, runner=fake_runner)
    assert fake_runner.calls.index(call_containing("read_flash", "0x1000000")) < fake_runner.calls.index(call_containing("upload"))


@pytest.mark.parametrize((report, code), [
    (build_report(app_free_ratio=.09), "FLASH_OVERFLOW"),
    (build_report(fs_free_ratio=.09), "ASSET_STORAGE_OVERFLOW"),
    (build_report(static_ram_over=True), "STATIC_RAM_OVERFLOW"),
    (build_report(heap_free=65535), "HEAP_STARTUP_LOW"),
])
def test_memory_failures_are_specific(report, code):
    assert classify_memory(report.build, report.ready)[0].code == code
```

- [ ] **Step 2: Run deployment tests and confirm missing implementation fails**

Run: `python3 -m pytest tests/test_tdisplay_deploy.py -v`

Expected: FAIL importing `scripts.deploy_tdisplay`.

- [ ] **Step 3: Implement guarded backup, build, upload and serial verification**

Detect `/dev/cu.usbserial-*` and `/dev/cu.SLAB_USBtoUART*`, require exactly one
unless `PORT` is provided, and query esptool chip/flash identity. Create
`out/board-backups/<chip-id>-<timestamp>-16mb.bin` plus `.sha256` only when no
valid backup exists for that chip ID. Run pytest, native asset build, PlatformIO
firmware build and `buildfs`. Parse sizes before any write. Upload firmware,
partitions and LittleFS through PlatformIO without `erase_flash`, reset, then
read serial for 15 seconds and require one valid `VPET_READY` line.

Use these hard failures:

```python
APP_FREE_RATIO_MIN = 0.10
FS_FREE_RATIO_MIN = 0.10
STARTUP_HEAP_MIN = 64 * 1024
MIN_HEAP_MIN = 48 * 1024
READY_TIMEOUT_SECONDS = 15
```

Wire the Makefile:

```make
deploy: test build-tdisplay firmware
	$(PY) scripts/deploy_tdisplay.py --port "$(PORT)" --upload-speed "$(UPLOAD_SPEED)"

firmware: build-tdisplay
	./scripts/bootstrap_platformio.sh
	.venv-platformio/bin/pio run -d firmware/t-display -e tdisplay
```

- [ ] **Step 4: Run deployment tests and a read-only board preflight**

Run: `python3 -m pytest tests/test_tdisplay_deploy.py tests/test_pipeline.py -v`

Run: `python3 scripts/deploy_tdisplay.py --preflight --port /dev/cu.usbserial-57040013171`

Expected: tests PASS; preflight identifies classic ESP32 and 16 MB flash, prints budgets, and performs no upload.

- [ ] **Step 5: Commit the deployment pipeline**

```bash
git add Makefile .gitignore scripts/tdisplay_device.py scripts/deploy_tdisplay.py tests/test_tdisplay_deploy.py
git commit -m "feat: safely deploy vPet to T-Display"
```

---

### Task 9: Document, Back Up And Deploy To The Connected Board

**Files:**
- Modify: `README.md`
- Modify: `docs/architecture.md`
- Modify: `docs/development-workflow.md`
- Create: `docs/tdisplay-recovery.md`

**Interfaces:**
- Consumes: all previous Make targets and telemetry contracts.
- Produces: end-to-end operator documentation and a verified physical deployment.

- [ ] **Step 1: Update documentation with exact daily and recovery commands**

Document `make sim`, `make deploy`, `make deploy-pico`, `PORT`, `UPLOAD_SPEED`,
button mapping, not holding ACTION during reset, memory diagnostic meanings,
NVS preservation, first backup path, and the restore command:

```bash
BACKUP="$(find out/board-backups -name '*-16mb.bin' -type f -print | sort | tail -1)"
test -n "$BACKUP"
shasum -a 256 -c "$BACKUP.sha256"
/Library/Frameworks/Python.framework/Versions/3.12/bin/esptool.py \
  --chip esp32 --port /dev/cu.usbserial-57040013171 \
  write_flash 0x0 "$BACKUP"
```

State clearly that restore replaces the entire board and must use the backup
whose adjacent SHA-256 file verifies successfully.

- [ ] **Step 2: Run the complete automated suite**

Run: `make test`

Expected: all Python and native tests PASS.

- [ ] **Step 3: Validate the final simulator visually**

Run: `SDL_VIDEODRIVER=dummy /usr/local/bin/python3 scripts/sim.py --profile tdisplay --build-dir build-tdisplay --max-frames 60 --record out/tdisplay-final`

Expected: recorded 240x135 frames show menu, motion, actions, night sleep,
status, inventory, evolution and options without overflow or black chroma boxes.

- [ ] **Step 4: Back up and deploy the connected T-Display**

Run: `make deploy PORT=/dev/cu.usbserial-57040013171`

Expected: a verified 16 MB backup exists, firmware and LittleFS upload succeed,
and serial returns `VPET_READY` above every configured memory threshold.

- [ ] **Step 5: Exercise both hardware buttons**

Verify on the physical screen:

1. GPIO35 short press moves the yellow selector exactly one item.
2. GPIO0 short press opens or activates the selected item.
3. GPIO35 long press returns one level.
4. Feed, Training, Rest and Battle use the correct current-species animation.
5. Dragfiremon moves using fly.
6. Rest switches to the night background and returns to day afterward.
7. WiFi scan, password entry and Internet status remain responsive.

- [ ] **Step 6: Commit documentation and record acceptance evidence**

```bash
git add README.md docs/architecture.md docs/development-workflow.md docs/tdisplay-recovery.md
git commit -m "docs: document T-Display workflow and recovery"
```

Record the final build sizes, backup path and `VPET_READY` line in the task
completion response; do not commit device credentials, NVS contents or the
full-flash backup.
