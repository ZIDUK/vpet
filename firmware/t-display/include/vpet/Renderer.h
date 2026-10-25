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
    uint32_t nowMs;
    bool spanish;
    int minuteOfDay;
    bool tired;
    AppViewModel(const PetState& p, const Motion& m, uint8_t menu, uint32_t ms,
                 bool es, int minute = 720, bool sleepy = false)
        : pet(p), motion(m), menuIndex(menu), nowMs(ms), spanish(es),
          minuteOfDay(minute), tired(sleepy) {}
};

class Renderer {
public:
    Renderer(
        TFT_eSPI& display,
        TFT_eSprite& canvas,
        TFT_eSprite& staticScene,
        AssetStore& assets
    );
    void draw(const AppViewModel& model, int16_t statusSplitX = 0, bool present = true);
    void invalidate() { staticSceneReady_ = false; }

private:
    const char* animationPath(const AppViewModel& model) const;
    void rebuildStaticScene(bool night, SpeciesId species, const content::PetDefinition& definition);
    void drawSelector(uint8_t selected, bool calling);
    void drawCallCue(const AppViewModel& model);
    void drawNeedBubble(const AppViewModel& model);

    TFT_eSPI& display_;
    TFT_eSprite& canvas_;
    TFT_eSprite& staticScene_;
    AssetStore& assets_;
    bool staticSceneReady_ = false;
    bool staticSceneNight_ = false;
    SpeciesId staticSceneSpecies_ = SpeciesId::Egg;
    const content::PetDefinition* staticDefinition_ = nullptr;
};

}  // namespace vpet
