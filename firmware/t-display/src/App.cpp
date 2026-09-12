#include "vpet/App.h"
#include "vpet/Strings.h"

#include <sys/time.h>
#include <time.h>

namespace vpet {

App::App(Renderer& renderer, Panels& panels, SettingsStore& settingsStore, BleService& bluetooth)
    : renderer_(renderer),
      panels_(panels),
      settingsStore_(settingsStore),
      bluetooth_(bluetooth),
      motion_(240, 135, 24, 88) {}

void App::begin(uint32_t nowMs) {
    lastTickMs_ = nowMs;
    lastRenderMs_ = nowMs - 50;
    settingsStore_.load(pet_, settings_);
    bluetooth_.setEnabled(settings_.bluetoothEnabled);
    motion_.setSpecies(pet_.species());
    eggStartedMs_ = nowMs;
}

void App::beginDateTime(bool date) {
    int values[5] = {2026, 1, 1, 0, 0};
    const time_t now = time(nullptr);
    struct tm value {};
    localtime_r(&now, &value);
    if (value.tm_year + 1900 >= 2024) {
        values[0] = value.tm_year + 1900;
        values[1] = value.tm_mon + 1;
        values[2] = value.tm_mday;
        values[3] = value.tm_hour;
        values[4] = value.tm_min;
    }
    dateMenu_.begin(date, values, languageIsSpanish(settings_.language.c_str()));
    navigation_.setPanel(PanelId::DateTime);
}

void App::applyDateTime() {
    const int* values = dateMenu_.values();
    struct tm value {};
    value.tm_year = values[0] - 1900;
    value.tm_mon = values[1] - 1;
    value.tm_mday = values[2];
    value.tm_hour = values[3];
    value.tm_min = values[4];
    const time_t epoch = mktime(&value);
    const timeval clock = {epoch, 0};
    settimeofday(&clock, nullptr);
}

void App::handlePanelInput(uint32_t nowMs, InputEvent event) {
    const PanelId panel = navigation_.panel();
    if (panel == PanelId::Options) {
        if (event == InputEvent::Next || event == InputEvent::Back) {
            navigation_.dispatch(event);
            return;
        }
        if (event != InputEvent::Action) return;
        switch (navigation_.panelIndex()) {
            case 0:
                settings_.bluetoothEnabled = !settings_.bluetoothEnabled;
                if (!bluetooth_.setEnabled(settings_.bluetoothEnabled)) {
                    settings_.bluetoothEnabled = false;
                }
                settingsStore_.save(pet_, settings_);
                break;
            case 1:
                settings_.language = settings_.language == "ES" ? "EN" : "ES";
                break;
            case 2:
                settings_.soundEnabled = !settings_.soundEnabled;
                break;
            case 3:
                settingsStore_.save(pet_, settings_);
                break;
            case 4:
                settingsStore_.load(pet_, settings_);
                motion_.setSpecies(pet_.species());
                bluetooth_.setEnabled(settings_.bluetoothEnabled);
                break;
            case 5: beginDateTime(true); break;
            case 6: beginDateTime(false); break;
            case 7:
                if (pet_.forceNextForm()) {
                    motion_.setSpecies(pet_.species());
                    motion_.startEvolution(nowMs);
                    settingsStore_.save(pet_, settings_);
                    navigation_.setPanel(PanelId::Home);
                }
                break;
            case 8: navigation_.setPanel(PanelId::Home); break;
        }
        return;
    }
    if (panel == PanelId::Inventory) {
        navigation_.setPanelIndex(pet_.clampVisibleInventoryIndex(navigation_.panelIndex()));
        if (event == InputEvent::Back) {
            navigation_.dispatch(event);
            return;
        }
        if (event == InputEvent::Next) {
            navigation_.setPanelIndex(pet_.nextVisibleInventoryIndex(navigation_.panelIndex()));
            return;
        }
        if (event != InputEvent::Action) return;
        const ItemUseResult result = pet_.useItem(navigation_.panelIndex());
        if (result == ItemUseResult::Used) {
            settingsStore_.save(pet_, settings_);
            navigation_.setPanelIndex(pet_.clampVisibleInventoryIndex(navigation_.panelIndex()));
        }
        if (result == ItemUseResult::Back) navigation_.setPanel(PanelId::Home);
        return;
    }
    if (panel == PanelId::DateTime) {
        if (event == InputEvent::Next) {
            dateMenu_.next();
        } else if (event == InputEvent::Action) {
            const DateTimeAction result = dateMenu_.activate();
            if (result == DateTimeAction::Saved) applyDateTime();
            if (result != DateTimeAction::None) {
                navigation_.setPanel(PanelId::Options, dateMenu_.editingDate() ? 5 : 6);
            }
        }
        return;
    }
    navigation_.dispatch(event);
}

void App::activate(uint32_t nowMs) {
    if (motion_.state() == MotionState::Sleep) {
        if (navigation_.menuIndex() == 4) motion_.wake(nowMs);
        return;
    }
    Action action = Action::None;
    switch (navigation_.menuIndex()) {
        case 1: action = Action::Feed; break;
        case 2: action = Action::Training; break;
        case 3: action = Action::Battle; break;
        case 4: action = Action::Rest; break;
        default: return;
    }
    if (pet_.beginAction(action)) {
        motion_.startAction(action, nowMs);
    }
}

void App::tick(uint32_t nowMs, InputEvent event) {
    const uint32_t elapsed = nowMs - lastTickMs_;
    lastTickMs_ = nowMs;
    pet_.tick(elapsed);
    if (pet_.species() == SpeciesId::Egg && nowMs - eggStartedMs_ >= 8000) {
        pet_.evolveTo(SpeciesId::Baby);
        motion_.setSpecies(SpeciesId::Baby);
        settingsStore_.save(pet_, settings_);
    }
    motion_.tick(nowMs);
    if (motion_.consumeActionCompleted()) {
        pet_.completeAction();
    }

    const bool acceptsInput =
        navigation_.panel() != PanelId::Home ||
        pet_.pendingAction() == Action::None ||
        motion_.state() == MotionState::Sleep;
    if (acceptsInput && event != InputEvent::None) {
        if (navigation_.panel() == PanelId::Home && event == InputEvent::Action &&
            navigation_.menuIndex() >= 1 && navigation_.menuIndex() <= 4) {
            activate(nowMs);
        } else if (navigation_.panel() == PanelId::Home) {
            navigation_.dispatch(event);
        } else {
            handlePanelInput(nowMs, event);
        }
    }

    navigation_.setCurrentSpecies(pet_.species());

    const PanelId panel = navigation_.panel();
    uint32_t intervalMs = 33;
    if (panel == PanelId::Status || panel == PanelId::Inventory ||
        panel == PanelId::EvolutionTree || panel == PanelId::EvolutionDetail) {
        intervalMs = 1000;
    }
    if (event != InputEvent::None || nowMs - lastRenderMs_ >= intervalMs) {
        lastRenderMs_ = nowMs;
        if (navigation_.panel() == PanelId::Home) {
            panels_.invalidate();
            renderer_.draw({pet_, motion_, navigation_.menuIndex()});
        } else {
            panels_.draw(
                navigation_,
                pet_,
                bluetooth_.status(),
                dateMenu_,
                settings_.language.c_str(),
                settings_.soundEnabled
            );
        }
    }
}

}  // namespace vpet
