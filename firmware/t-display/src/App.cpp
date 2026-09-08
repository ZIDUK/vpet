#include "vpet/App.h"

#include <sys/time.h>
#include <time.h>

namespace vpet {

App::App(Renderer& renderer, Panels& panels, SettingsStore& settingsStore, NetworkService& network)
    : renderer_(renderer),
      panels_(panels),
      settingsStore_(settingsStore),
      network_(network),
      motion_(240, 135, 24, 88) {}

void App::begin(uint32_t nowMs) {
    lastTickMs_ = nowMs;
    lastRenderMs_ = nowMs - 50;
    settingsStore_.load(pet_, settings_);
    network_.autoConnect();
    motion_.setSpecies(pet_.species());
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
    (void)nowMs;
    const PanelId panel = navigation_.panel();
    if (panel == PanelId::Options) {
        if (event == InputEvent::Next || event == InputEvent::Back) {
            navigation_.dispatch(event);
            return;
        }
        if (event != InputEvent::Action) return;
        switch (navigation_.panelIndex()) {
            case 0:
                settings_.language = settings_.language == "ES" ? "EN" : "ES";
                break;
            case 1:
                settings_.soundEnabled = !settings_.soundEnabled;
                break;
            case 2:
                settingsStore_.save(pet_, settings_);
                break;
            case 3:
                settingsStore_.load(pet_, settings_);
                motion_.setSpecies(pet_.species());
                break;
            case 4:
                network_.startScan();
                navigation_.setPanel(PanelId::WifiList);
                break;
            case 5: beginDateTime(true); break;
            case 6: beginDateTime(false); break;
            case 7: navigation_.setPanel(PanelId::Home); break;
        }
        return;
    }
    if (panel == PanelId::WifiList) {
        if (event == InputEvent::Back) {
            navigation_.setPanel(PanelId::Options, 4);
            return;
        }
        if (!network_.scanComplete()) return;
        const size_t count = network_.networkCount();
        if (event == InputEvent::Next) {
            navigation_.setPanelIndex((navigation_.panelIndex() + 1) % (count + 1));
        } else if (event == InputEvent::Action) {
            if (navigation_.panelIndex() >= count) {
                navigation_.setPanel(PanelId::Options, 4);
            } else {
                selectedSsid_ = network_.networkName(navigation_.panelIndex());
                password_.clear();
                navigation_.setPanel(PanelId::Password);
            }
        }
        return;
    }
    if (panel == PanelId::Password) {
        if (event == InputEvent::Back) {
            password_.clear();
            navigation_.setPanel(PanelId::WifiList);
        } else if (event == InputEvent::Next) {
            password_.next();
        } else if (event == InputEvent::Action) {
            if (password_.select()) {
                network_.connect(selectedSsid_, password_.password());
                navigation_.setPanel(PanelId::Options, 4);
            } else if (password_.consumeCancelled()) {
                navigation_.setPanel(PanelId::WifiList);
            }
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
    network_.poll();
    motion_.tick(nowMs);
    if (motion_.consumeActionCompleted()) {
        pet_.completeAction();
    }

    if (pet_.pendingAction() == Action::None && event != InputEvent::None) {
        if (navigation_.panel() == PanelId::Home && event == InputEvent::Action &&
            navigation_.menuIndex() >= 1 && navigation_.menuIndex() <= 4) {
            activate(nowMs);
        } else if (navigation_.panel() == PanelId::Home) {
            navigation_.dispatch(event);
        } else {
            handlePanelInput(nowMs, event);
        }
    }

    navigation_.setDiscovered(
        pet_.species() != SpeciesId::Rookie,
        pet_.species() == SpeciesId::Ultimate
    );

    if (nowMs - lastRenderMs_ >= 33) {
        lastRenderMs_ = nowMs;
        if (navigation_.panel() == PanelId::Home) {
            renderer_.draw({pet_, motion_, navigation_.menuIndex()});
        } else {
            panels_.draw(
                navigation_, pet_, network_, password_, selectedSsid_.c_str(),
                dateTime_, editingDate_, dateField_
            );
        }
    }
}

}  // namespace vpet
