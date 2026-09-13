#include "vpet/Renderer.h"

#include <cstring>

#include "vpet/Layout.h"
#include "vpet/Strings.h"

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
        case SpeciesId::Egg: return "egg";
        case SpeciesId::Baby: return "baby";
        case SpeciesId::Rookie: return "rookie";
        case SpeciesId::Champion: return "champion";
        case SpeciesId::Ultimate: return "ultimate";
    }
    return "rookie";
}

const char* petName(SpeciesId species) {
    switch (species) {
        case SpeciesId::Egg: return "egg";
        case SpeciesId::Baby: return "sparkmon";
        case SpeciesId::Rookie: return "firemon";
        case SpeciesId::Champion: return "flamemon";
        case SpeciesId::Ultimate: return "dragfiremon";
    }
    return "firemon";
}
}

Renderer::Renderer(
    TFT_eSPI& display,
    TFT_eSprite& canvas,
    TFT_eSprite& staticScene,
    AssetStore& assets
)
    : display_(display), canvas_(canvas), staticScene_(staticScene), assets_(assets) {}

const char* Renderer::animationPath(const AppViewModel& model) const {
    static char path[72];
    const MotionState state = model.motion.state();
    const char* action = "idle";
    if (model.pet.species() == SpeciesId::Egg) {
        snprintf(
            path,
            sizeof(path),
            model.motion.state() == MotionState::Hatch
                ? "/animations/egg/egg_hatch.vpa"
                : "/animations/egg/egg_idle.vpa"
        );
        return path;
    }
    if (state == MotionState::Evolution) {
        switch (model.pet.species()) {
            case SpeciesId::Rookie:
                return "/animations/baby/sparkmon_evolution.vpa";
            case SpeciesId::Champion:
                return "/animations/rookie/firemon_evolution.vpa";
            case SpeciesId::Ultimate:
                return "/animations/champion/flamemon_evolution.vpa";
            default:
                return "/animations/baby/sparkmon_evolution.vpa";
        }
    }
    switch (state) {
        case MotionState::Walk:
            action = model.pet.species() == SpeciesId::Ultimate ? "fly" : "walk";
            break;
        case MotionState::Eat: action = "eat"; break;
        case MotionState::Punch: action = "punch"; break;
        case MotionState::Cast: action = "cast"; break;
        case MotionState::Hit: action = "hit"; break;
        case MotionState::Hurt: action = "hurt"; break;
        case MotionState::Dodge: action = "dodge"; break;
        case MotionState::Block: action = "block"; break;
        case MotionState::Sleep: action = "sleep"; break;
        case MotionState::Evolution: break;
        case MotionState::Hatch: break;
        case MotionState::Idle: break;
    }
    if (model.pet.species() != SpeciesId::Rookie &&
        (strcmp(action, "hit") == 0 || strcmp(action, "hurt") == 0 ||
         strcmp(action, "dodge") == 0 || strcmp(action, "block") == 0)) {
        action = (strcmp(action, "hit") == 0 || strcmp(action, "hurt") == 0) ? "punch" : "cast";
    }
    if (model.pet.species() == SpeciesId::Baby &&
        strcmp(action, "idle") != 0 && strcmp(action, "walk") != 0 &&
        strcmp(action, "eat") != 0 && strcmp(action, "sleep") != 0) {
        action = "idle";
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

void Renderer::rebuildStaticScene(bool night) {
    assets_.drawFrame(
        staticScene_,
        night ? "/backgrounds/background_night.vpa" : "/backgrounds/background.vpa",
        0,
        0,
        0
    );
    staticScene_.fillRect(0, 0, 240, 24, TFT_BLACK);
    for (uint8_t index = 0; index < 8; ++index) {
        assets_.drawFrame(staticScene_, kMenuIcons[index], 0, index * 30 + 5, 2);
    }
    staticSceneReady_ = true;
    staticSceneNight_ = night;
}

void Renderer::drawSelector(uint8_t selected, bool calling) {
    const int16_t x = (selected % 8) * 30;
    canvas_.drawRect(x, 0, 30, 24, TFT_YELLOW);
    canvas_.drawRect(x + 1, 1, 28, 22, TFT_YELLOW);
    if (calling) {
        canvas_.setTextDatum(TR_DATUM);
        canvas_.setTextColor(TFT_YELLOW, TFT_BLACK);
        canvas_.drawString("*", x + 28, 1, 2);
        canvas_.setTextDatum(TL_DATUM);
    }
}

void Renderer::drawCallCue(const AppViewModel& model) {
    const CallReason reason = model.pet.callReason();
    if (reason == CallReason::None) return;
    const uint8_t cue = callMenuIndex(reason);
    if (cue < 8 && callBlinkOn(model.nowMs)) {
        const int16_t x = cue * 30;
        canvas_.drawRect(x, 0, 30, 24, TFT_RED);
        canvas_.drawRect(x + 1, 1, 28, 22, TFT_RED);
    }
    const char* label = copy::callHunger(model.spanish);
    if (reason == CallReason::Strength) label = copy::callStrength(model.spanish);
    if (reason == CallReason::Lights) label = copy::callLights(model.spanish);
    canvas_.fillRect(0, 117, 240, 18, TFT_YELLOW);
    canvas_.setTextDatum(MC_DATUM);
    canvas_.setTextColor(TFT_BLACK, TFT_YELLOW);
    canvas_.drawString(label, 120, 125, 2);
    canvas_.setTextDatum(TL_DATUM);
}

void Renderer::draw(const AppViewModel& model, int16_t statusSplitX, bool present) {
    const bool night = model.motion.state() == MotionState::Sleep;
    if (!staticSceneReady_ || staticSceneNight_ != night) {
        rebuildStaticScene(night);
    }
    memcpy(canvas_.getPointer(), staticScene_.getPointer(), 240 * 135 * 2);
    drawSelector(model.menuIndex, model.pet.callReason() != CallReason::None);
    if (statusSplitX <= 0) {
        drawCallCue(model);
    }
    if (model.pet.dead()) {
        assets_.drawFrame(canvas_, "/ui/fx/grave.vpa", 0, statusSplitX > 0 ? 6 : 76, 32);
        if (present) {
            display_.startWrite();
            canvas_.pushSprite(0, 0);
            display_.endWrite();
        }
        return;
    }
    const bool evolution = model.motion.state() == MotionState::Evolution;
    const int16_t spriteSize = evolution ? 111 : 88;
    int16_t x = evolution ? (240 - spriteSize) / 2 : model.motion.x();
    const int16_t y = evolution ? 24 : model.motion.y();
    if (!evolution && statusSplitX > 0) {
        x = statusPetX(spriteSize, statusSplitX);
    }
    if (model.motion.state() == MotionState::Punch) {
        const int16_t bagX = x + (model.motion.direction() < 0 ? -40 : 56);
        assets_.drawFrame(
            canvas_,
            "/ui/fx/bag.vpa",
            model.motion.frame(),
            bagX,
            bagDrawY(y, spriteSize, 135)
        );
    }
    assets_.drawFrame(
        canvas_,
        animationPath(model),
        model.motion.frame(),
        x,
        y,
        model.motion.direction() < 0 && !evolution
    );
    if (model.pet.injured()) {
        canvas_.setTextColor(TFT_YELLOW, TFT_BLACK);
        canvas_.drawString("*", x + spriteSize - 10, y + 4, 2);
    }
    if (present) {
        display_.startWrite();
        canvas_.pushSprite(0, 0);
        display_.endWrite();
    }
}

}  // namespace vpet
