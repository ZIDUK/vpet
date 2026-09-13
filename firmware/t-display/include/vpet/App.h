#pragma once

#include <stdint.h>

#include "vpet/Input.h"
#include "vpet/BleService.h"
#include "vpet/DateTimeMenu.h"
#include "vpet/Evolution.h"
#include "vpet/Motion.h"
#include "vpet/Navigation.h"
#include "vpet/Panels.h"
#include "vpet/PetState.h"
#include "vpet/Renderer.h"
#include "vpet/SettingsStore.h"

namespace vpet {

class App {
public:
    App(Renderer& renderer, Panels& panels, SettingsStore& settingsStore, BleService& bluetooth);
    void begin(uint32_t nowMs);
    void tick(uint32_t nowMs, InputEvent event);

private:
    void activate(uint32_t nowMs);
    void handlePanelInput(uint32_t nowMs, InputEvent event);
    void beginDateTime(bool date);
    void applyDateTime();
    uint8_t clockHour() const;

    Renderer& renderer_;
    Panels& panels_;
    SettingsStore& settingsStore_;
    BleService& bluetooth_;
    static constexpr uint32_t kCareTimeScale = 1;

    Settings settings_;
    DateTimeMenu dateMenu_;
    PetState pet_;
    Evolution evolution_;
    Motion motion_;
    Navigation navigation_;
    uint32_t lastTickMs_ = 0;
    uint32_t lastRenderMs_ = 0;
    uint32_t eggStartedMs_ = 0;
};

}  // namespace vpet
