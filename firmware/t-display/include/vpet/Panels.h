#pragma once

#include <TFT_eSPI.h>

#include "vpet/AssetStore.h"
#include "vpet/BleService.h"
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
        const int* dateTime,
        bool editingDate,
        uint8_t dateField
    );

private:
    void drawChrome(uint8_t selected, const char* title);
    void drawStatus(const PetState& pet);
    void drawInventory(uint8_t selected);
    void drawEvolution(const Navigation& navigation, bool detail);
    void drawOptions(uint8_t selected, BleStatus bluetoothStatus);
    void drawDateTime(const int* values, bool editingDate, uint8_t field);
    void drawLabel(const char* text, int16_t x, int16_t y, int16_t width, uint8_t font = 1);

    TFT_eSPI& output_;
    TFT_eSprite& display_;
    AssetStore& assets_;
    PanelId lastPanel_ = PanelId::Home;
};

}  // namespace vpet
