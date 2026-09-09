#pragma once

#include <stdint.h>

#include "vpet/Input.h"
#include "vpet/Motion.h"
#include "vpet/Navigation.h"
#include "vpet/Panels.h"
#include "vpet/PasswordEditor.h"
#include "vpet/PetState.h"
#include "vpet/Renderer.h"

namespace vpet {

class App {
public:
    App(Renderer& renderer, Panels& panels, SettingsStore& settingsStore, NetworkService& network);
    void begin(uint32_t nowMs);
    void tick(uint32_t nowMs, InputEvent event);

private:
    void activate(uint32_t nowMs);
    void handlePanelInput(uint32_t nowMs, InputEvent event);
    void beginDateTime(bool date);
    void applyDateTime();

    Renderer& renderer_;
    Panels& panels_;
    SettingsStore& settingsStore_;
    NetworkService& network_;
    Settings settings_;
    PasswordEditor password_;
    std::string selectedSsid_;
    int dateTime_[5] = {2026, 1, 1, 0, 0};
    bool editingDate_ = true;
    uint8_t dateField_ = 0;
    PetState pet_;
    Motion motion_;
    Navigation navigation_;
    uint32_t lastTickMs_ = 0;
    uint32_t lastRenderMs_ = 0;
    uint32_t eggStartedMs_ = 0;
};

}  // namespace vpet
