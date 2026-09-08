#pragma once

#include <TFT_eSPI.h>

#include "vpet/AssetStore.h"
#include "vpet/Navigation.h"
#include "vpet/PetState.h"

namespace vpet {

class Panels {
public:
    Panels(TFT_eSPI& display, AssetStore& assets);
    void draw(const Navigation& navigation, const PetState& pet);

private:
    void drawChrome(uint8_t selected, const char* title);
    void drawStatus(const PetState& pet);
    void drawInventory(uint8_t selected);
    void drawEvolution(const Navigation& navigation, bool detail);
    void drawOptions(uint8_t selected);
    void drawLabel(const char* text, int16_t x, int16_t y, int16_t width, uint8_t font = 1);

    TFT_eSPI& display_;
    AssetStore& assets_;
};

}  // namespace vpet
