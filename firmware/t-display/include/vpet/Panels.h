#pragma once

#include <TFT_eSPI.h>

#include "vpet/AssetStore.h"
#include "vpet/BleService.h"
#include "vpet/DateTimeMenu.h"
#include "vpet/Navigation.h"
#include "vpet/PetState.h"

namespace vpet {

class Panels {
public:
    Panels(TFT_eSPI& display, TFT_eSprite& canvas, AssetStore& assets);
    void draw(
        const Navigation& navigation,
        const PetState& pet,
        BleStatus bluetoothStatus,
        const DateTimeMenu& dateMenu,
        const char* language,
        bool soundEnabled
    );
    void invalidate();

private:
    void drawChrome(uint8_t selected, const char* title);
    void beginPanel(bool panelChanged, uint8_t selected, const char* title);
    void drawStatus(const PetState& pet, bool spanish, uint8_t page);
    void drawInventory(uint8_t selected, bool spanish, const PetState& pet);
    void drawBar(const char* label, int value, int16_t y);
    void drawEvolution(const Navigation& navigation, bool detail, bool spanish);
    void drawOptions(uint8_t selected, BleStatus bluetoothStatus, bool spanish, const char* language, bool soundEnabled);
    void drawDateTime(const DateTimeMenu& dateMenu);
    void drawStat(const char* icon, const char* label, const char* value, int16_t x, int16_t y);
    void drawLabel(const char* text, int16_t x, int16_t y, int16_t width, uint8_t font = 1);

    TFT_eSPI& output_;
    TFT_eSprite& display_;
    AssetStore& assets_;
    PanelId lastPanel_ = PanelId::Home;
    bool lastSpanish_ = true;
};

}  // namespace vpet
