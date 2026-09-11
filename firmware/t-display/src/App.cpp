#include "vpet/App.h"

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
    editingDate_ = date;
    dateField_ = 0;
    const time_t now = time(nullptr);
    struct tm value {};
    localtime_r(&now, &value);
    if (value.tm_year + 1900 >= 2024) {
        dateTime_[0] = value.tm_year + 1900;
        dateTime_[1] = value.tm_mon + 1;
        dateTime_[2] = value.tm_mday;
        dateTime_[3] = value.tm_hour;
        dateTime_[4] = value.tm_min;
    }
    navigation_.setPanel(PanelId::DateTime);
}

void App::applyDateTime() {
    struct tm value {};
    value.tm_year = dateTime_[0] - 1900;
    value.tm_mon = dateTime_[1] - 1;
    value.tm_mday = dateTime_[2];
    value.tm_hour = dateTime_[3];
    value.tm_min = dateTime_[4];
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
    if (panel == PanelId::DateTime) {
        if (event == InputEvent::Back) {
            navigation_.setPanel(PanelId::Options, editingDate_ ? 5 : 6);
        } else if (event == InputEvent::Next) {
            const uint8_t index = editingDate_ ? dateField_ : dateField_ + 3;
            const int maxima[] = {2099, 12, 31, 23, 59};
            const int minima[] = {2024, 1, 1, 0, 0};
            dateTime_[index] = dateTime_[index] >= maxima[index] ? minima[index] : dateTime_[index] + 1;
        } else if (event == InputEvent::Action) {
            const uint8_t fields = editingDate_ ? 3 : 2;
            if (++dateField_ >= fields) {
                applyDateTime();
                navigation_.setPanel(PanelId::Options, editingDate_ ? 5 : 6);
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

    if (event != InputEvent::None || nowMs - lastRenderMs_ >= 33) {
        lastRenderMs_ = nowMs;
        if (navigation_.panel() == PanelId::Home) {
            renderer_.draw({pet_, motion_, navigation_.menuIndex()});
        } else {
            panels_.draw(
                navigation_, pet_, bluetooth_.status(),
                dateTime_, editingDate_, dateField_
            );
        }
    }
}

}  // namespace vpet
