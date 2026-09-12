# Inventory Spend And Status Pages Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** On the T-Display, ACTION spends inventory items without leaving the menu, and Status shows HP/HAM/ENE as bars with a second page for the rest.

**Architecture:** `PetState::useItem` owns stock and stat changes. `SettingsStore` persists four NVS keys on schema 1. `App` intercepts Inventory ACTION and autosaves. `Navigation` pages Status with NEXT. `Panels` paints live `xN` and the two Status pages.

**Tech Stack:** PlatformIO, `vpet_core`, Unity native tests, TFT_eSPI, NVS. Firmware first; Python sim is out of this plan.

## Global Constraints

- Placa primero. El sim no se toca en este plan.
- Catálogo: Carne +20 HAM (stock 3), Energía +25 ENE (stock 2), EXP +8 ESF (stock 1), Anillo +15 mood (stock 1), ATRÁS cierra.
- ACTION en item se queda en Inventario. Stock 0 = no-op. Huevo no gasta. Feed del header no gasta Carne.
- NVS schema 1, claves `invMeat`, `invEner`, `invExp`, `invRing`. Save viejo → 3/2/1/1. Autosave al gastar.
- Status página 1: barras HP/HAM/ENE. Página 2: AGE, ESF, BAT, mood, reloj. NEXT cicla 0↔1. ACTION/BACK → Home.
- Árbol / Call / CM / DP fuera. No `uploadfs`. No commit a menos que el usuario lo pida.
- Tests: `.venv-platformio/bin/pio test -d firmware/t-display -e native --filter test_native`
- Upload: `.venv-platformio/bin/pio run -d firmware/t-display -e tdisplay --upload-port /dev/cu.usbserial-57040013171 -t upload`

---

### Task 1: `PetState::useItem`

**Files:**
- Modify: `firmware/t-display/lib/vpet_core/src/vpet/PetState.h`
- Modify: `firmware/t-display/lib/vpet_core/src/vpet/PetState.cpp`
- Modify: `firmware/t-display/test/test_native/test_pet_state.cpp`
- Modify: `firmware/t-display/test/test_native/test_input.cpp`

**Produces:**
- `enum class ItemUseResult : uint8_t { Used, Empty, Blocked, Back };`
- `ItemUseResult useItem(uint8_t index);`
- `uint8_t itemCount(uint8_t index) const;`
- `void restoreItems(uint8_t meat, uint8_t energyItem, uint8_t expItem, uint8_t ring);`
- Defaults: meat 3, energyItem 2, expItem 1, ring 1. Counts clamp 0–99.

- [x] **Step 1: Write the failing tests**

```cpp
void test_use_item_spends_stock_and_applies_stat() {
    vpet::PetState pet;
    pet.evolveTo(vpet::SpeciesId::Rookie);
    TEST_ASSERT_EQUAL(3, pet.itemCount(0));
    TEST_ASSERT_EQUAL(vpet::ItemUseResult::Used, pet.useItem(0));
    TEST_ASSERT_EQUAL(2, pet.itemCount(0));
    TEST_ASSERT_EQUAL(100, pet.hunger());
    TEST_ASSERT_EQUAL(vpet::ItemUseResult::Used, pet.useItem(1));
    TEST_ASSERT_EQUAL(1, pet.itemCount(1));
    TEST_ASSERT_EQUAL(100, pet.energy());
    TEST_ASSERT_EQUAL(vpet::ItemUseResult::Used, pet.useItem(2));
    TEST_ASSERT_EQUAL(0, pet.itemCount(2));
    TEST_ASSERT_EQUAL(8, pet.effort());
    TEST_ASSERT_EQUAL(vpet::ItemUseResult::Used, pet.useItem(3));
    TEST_ASSERT_EQUAL(0, pet.itemCount(3));
    TEST_ASSERT_EQUAL(95, pet.happiness());
}

void test_use_item_empty_and_egg_do_not_change_stats() {
    vpet::PetState pet;
    TEST_ASSERT_EQUAL(vpet::ItemUseResult::Blocked, pet.useItem(0));
    TEST_ASSERT_EQUAL(3, pet.itemCount(0));
    TEST_ASSERT_EQUAL(vpet::ItemUseResult::Back, pet.useItem(4));
    pet.evolveTo(vpet::SpeciesId::Rookie);
    pet.restoreItems(0, 0, 0, 0);
    const int hunger = pet.hunger();
    TEST_ASSERT_EQUAL(vpet::ItemUseResult::Empty, pet.useItem(0));
    TEST_ASSERT_EQUAL(hunger, pet.hunger());
    TEST_ASSERT_EQUAL(vpet::ItemUseResult::Empty, pet.useItem(9));
}
```

Hunger starts at 80, +20 = 100. Energy 80+25=105 → 100. Happiness 80+15=95.

- [x] **Step 2: Run native tests. Expected RED:** `useItem` / `ItemUseResult` not declared.

- [x] **Step 3: Implement `useItem` / `itemCount` / `restoreItems` in `PetState`.** Index 4 → `Back` even as egg. Egg + item index → `Blocked`. Apply +20/+25/+8/+15 with `clampStat`. Decrement only on `Used`.

- [x] **Step 4: Run native tests. Expected GREEN for the new cases.**

- [x] **Step 5: Do not commit.**

---

### Task 2: Status NEXT pages

**Files:**
- Modify: `firmware/t-display/lib/vpet_core/src/vpet/Navigation.cpp`
- Modify: `firmware/t-display/test/test_native/test_navigation.cpp`
- Modify: `firmware/t-display/test/test_native/test_input.cpp`

**Produces:** Opening Status sets `panelIndex_ = 0`. NEXT on Status does `(panelIndex_ + 1) % 2`. ACTION/BACK still Home.

- [x] **Step 1: Write the failing test**

```cpp
void test_status_next_cycles_two_pages() {
    vpet::Navigation navigation;
    navigation.setMenuIndex(0);
    navigation.dispatch(vpet::InputEvent::Action);
    TEST_ASSERT_EQUAL(vpet::PanelId::Status, navigation.panel());
    TEST_ASSERT_EQUAL(0, navigation.panelIndex());
    navigation.dispatch(vpet::InputEvent::Next);
    TEST_ASSERT_EQUAL(vpet::PanelId::Status, navigation.panel());
    TEST_ASSERT_EQUAL(1, navigation.panelIndex());
    navigation.dispatch(vpet::InputEvent::Next);
    TEST_ASSERT_EQUAL(0, navigation.panelIndex());
    navigation.dispatch(vpet::InputEvent::Action);
    TEST_ASSERT_EQUAL(vpet::PanelId::Home, navigation.panel());
}
```

- [x] **Step 2: Run native tests. Expected:** page stays 0 or wraps `% 8` (not 1 then 0).

- [x] **Step 3: In `openSelectedMenu` case 0 set `panelIndex_ = 0`. In NEXT, `else if (panel_ == PanelId::Status) panelIndex_ = (panelIndex_ + 1) % 2`.**

- [x] **Step 4: Run native tests. Expected GREEN.**

- [x] **Step 5: Do not commit.**

---

### Task 3: Persist inventory in NVS

**Files:**
- Modify: `firmware/t-display/lib/vpet_core/src/vpet/SettingsStore.cpp`
- Modify: `firmware/t-display/test/test_native/test_settings.cpp`
- Modify: `firmware/t-display/test/test_native/test_input.cpp`

**Produces:** save/load `invMeat`, `invEner`, `invExp`, `invRing`. Missing keys use 3/2/1/1.

- [x] **Step 1: Write the failing test**

```cpp
void test_settings_persist_inventory_counts() {
    FakeStore store;
    vpet::PetState saved;
    saved.evolveTo(vpet::SpeciesId::Rookie);
    saved.useItem(0);
    vpet::Settings settings;
    TEST_ASSERT_TRUE(vpet::SettingsStore(store).save(saved, settings));
    vpet::PetState restored;
    vpet::Settings after;
    TEST_ASSERT_EQUAL(vpet::LoadResult::Loaded, vpet::SettingsStore(store).load(restored, after));
    TEST_ASSERT_EQUAL(2, restored.itemCount(0));
    TEST_ASSERT_EQUAL(2, restored.itemCount(1));
}

void test_missing_inventory_keys_use_defaults() {
    FakeStore store;
    store.ints["schema"] = 1;
    store.ints["species"] = 0;
    vpet::PetState pet;
    vpet::Settings settings;
    TEST_ASSERT_EQUAL(vpet::LoadResult::Loaded, vpet::SettingsStore(store).load(pet, settings));
    TEST_ASSERT_EQUAL(3, pet.itemCount(0));
    TEST_ASSERT_EQUAL(2, pet.itemCount(1));
    TEST_ASSERT_EQUAL(1, pet.itemCount(2));
    TEST_ASSERT_EQUAL(1, pet.itemCount(3));
}
```

- [x] **Step 2: Run native tests. Expected:** counts reset to defaults after load.

- [x] **Step 3: After `pet.restore(...)`, call `pet.restoreItems(store_.getInt("invMeat", 3), ...)` with 3/2/1/1 fallbacks. In save, `putInt` the four keys from `itemCount`.**

- [x] **Step 4: Run native tests. Expected GREEN.**

- [x] **Step 5: Do not commit.**

---

### Task 4: App spends items and Status/Inventory paint

**Files:**
- Modify: `firmware/t-display/src/App.cpp`
- Modify: `firmware/t-display/include/vpet/Panels.h`
- Modify: `firmware/t-display/src/Panels.cpp`
- Modify: `firmware/t-display/lib/vpet_core/src/vpet/Strings.h`

**Produces:** Inventory ACTION → `useItem`; `Used` autosaves; `Back` → Home. Inventory labels use `itemCount`. Status page 0 = bars; page 1 = AGE/ESF/BAT/mood/clock.

- [x] **Step 1: No Unity test for TFT paint. Native coverage is Tasks 1–3.**

- [x] **Step 2: In `handlePanelInput`, before the final `dispatch`, handle Inventory like Options:**

```cpp
if (panel == PanelId::Inventory) {
    if (event == InputEvent::Next || event == InputEvent::Back) {
        navigation_.dispatch(event);
        return;
    }
    if (event != InputEvent::Action) return;
    const ItemUseResult result = pet_.useItem(navigation_.panelIndex());
    if (result == ItemUseResult::Used) settingsStore_.save(pet_, settings_);
    if (result == ItemUseResult::Back) navigation_.setPanel(PanelId::Home);
    return;
}
```

- [x] **Step 3: `copy::mood` → `"MOOD"` / `"ANIMO"`. `drawInventory(selected, spanish, pet)` formats `"%s x%u"`. `drawStatus(pet, spanish, page)`: page 0 draws three 200×8 bars under `HP`/`HAM`/`ENE` + value; page 1 reuses `drawStat` for AGE, ESF, BAT, mood and the clock row.**

- [x] **Step 4: Build firmware and upload. No `uploadfs`.**

```bash
.venv-platformio/bin/pio test -d firmware/t-display -e native --filter test_native
.venv-platformio/bin/pio run -d firmware/t-display -e tdisplay --upload-port /dev/cu.usbserial-57040013171 -t upload
```

- [x] **Step 5: Do not commit.**

---

## Spec coverage

| Spec | Task |
|---|---|
| useItem Used/Empty/Blocked/Back | 1 |
| Stats +20/+25/+8/+15, clamp 100 | 1 |
| Defaults 3/2/1/1 | 1, 3 |
| Status NEXT 0↔1, ACTION Home | 2 |
| NVS inv* + old save defaults | 3 |
| Stay in menu, autosave, live xN | 4 |
| Status bars + page 2 + mood | 4 |
| Sim / árbol | Fuera |
