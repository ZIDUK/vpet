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
    Renderer(
        TFT_eSPI& display,
        TFT_eSprite& canvas,
        TFT_eSprite& staticScene,
        AssetStore& assets
    );
    void draw(const AppViewModel& model);

private:
    const char* animationPath(const AppViewModel& model) const;
    void rebuildStaticScene(bool night);
    void drawSelector(uint8_t selected);

    TFT_eSPI& display_;
    TFT_eSprite& canvas_;
    TFT_eSprite& staticScene_;
    AssetStore& assets_;
    bool staticSceneReady_ = false;
    bool staticSceneNight_ = false;
};

}  // namespace vpet
