#include "vpet/Renderer.h"

namespace vpet {
namespace {
constexpr const char* kMenuIcons[] = {
    "/ui/icons/status.vpa",
    "/ui/icons/feed.vpa",
    "/ui/icons/training.vpa",
    "/ui/icons/battle.vpa",
    "/ui/icons/rest.vpa",
    "/ui/icons/items.vpa",
    "/ui/icons/pedia.vpa",
    "/ui/icons/options.vpa",
};

const char* speciesName(SpeciesId species) {
    switch (species) {
        case SpeciesId::Rookie: return "rookie";
        case SpeciesId::Champion: return "champion";
        case SpeciesId::Ultimate: return "ultimate";
    }
    return "rookie";
}

const char* petName(SpeciesId species) {
    switch (species) {
        case SpeciesId::Rookie: return "firemon";
        case SpeciesId::Champion: return "flamemon";
        case SpeciesId::Ultimate: return "dragfiremon";
    }
    return "firemon";
}
}

Renderer::Renderer(TFT_eSPI& display, AssetStore& assets)
    : display_(display), assets_(assets) {}

const char* Renderer::animationPath(const AppViewModel& model) const {
    static char path[72];
    const MotionState state = model.motion.state();
    const char* action = "idle";
    switch (state) {
        case MotionState::Walk:
            action = model.pet.species() == SpeciesId::Ultimate ? "fly" : "walk";
            break;
        case MotionState::Eat: action = "eat"; break;
        case MotionState::Punch: action = "punch"; break;
        case MotionState::Cast: action = "cast"; break;
        case MotionState::Sleep: action = "sleep"; break;
        case MotionState::Evolution: action = "evolution"; break;
        case MotionState::Idle: break;
    }
    snprintf(
        path,
        sizeof(path),
        "/animations/%s/%s_%s.vpa",
        speciesName(model.pet.species()),
        petName(model.pet.species()),
        action
    );
    return path;
}

void Renderer::drawMenu(uint8_t selected) {
    display_.fillRect(0, 0, 240, 24, TFT_BLACK);
    for (uint8_t index = 0; index < 8; ++index) {
        assets_.drawFrame(display_, kMenuIcons[index], 0, index * 30 + 5, 2);
    }
    display_.drawRect((selected % 8) * 30, 0, 30, 24, TFT_YELLOW);
}

void Renderer::draw(const AppViewModel& model) {
    display_.startWrite();
    const char* background = model.motion.state() == MotionState::Sleep
        ? "/backgrounds/background_night.vpa"
        : "/backgrounds/background.vpa";
    assets_.drawFrame(display_, background, 0, 0, 0);
    drawMenu(model.menuIndex);
    const bool evolution = model.motion.state() == MotionState::Evolution;
    const int16_t spriteSize = evolution ? 111 : 88;
    const int16_t x = evolution ? (240 - spriteSize) / 2 : model.motion.x();
    const int16_t y = evolution ? 24 : model.motion.y();
    assets_.drawFrame(
        display_,
        animationPath(model),
        model.motion.frame(),
        x,
        y,
        model.motion.direction() < 0 && !evolution
    );
    display_.endWrite();
}

}  // namespace vpet
