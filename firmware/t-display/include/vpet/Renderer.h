#pragma once

#include <Arduino.h>
#include <TFT_eSPI.h>

#include "vpet/AssetStore.h"
#include "vpet/Motion.h"
#include "vpet/PetState.h"

namespace vpet {

struct AppViewModel {
    const PetState& pet;
    const Motion& motion;
    uint8_t menuIndex;
};

class Renderer {
public:
    Renderer(TFT_eSPI& display, TFT_eSprite& canvas, AssetStore& assets);
    void draw(const AppViewModel& model);

private:
    const char* animationPath(const AppViewModel& model) const;
    void drawMenu(uint8_t selected);

    TFT_eSPI& display_;
    TFT_eSprite& canvas_;
    AssetStore& assets_;
};

}  // namespace vpet
