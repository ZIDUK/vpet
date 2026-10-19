#include "vpet/Renderer.h"

#include <cstring>

#include "vpet/Layout.h"
#include "vpet/Strings.h"
#include "vpet/MenuBar.h"
#include "vpet/UiCue.h"

namespace vpet {
namespace {

bool angryIdle(const AppViewModel& model) {
    if (model.tired || (model.motion.state() != MotionState::Idle && model.motion.state() != MotionState::Walk))
        return false;
    const auto value = cue::forPet(model.pet);
    return value.need != cue::Need::None && value.face == cue::Face::Angry;
}

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
                return "/animations/rookie/firemon_evolution.vpa";
            case SpeciesId::Champion:
                return "/animations/champion/flamemon_evolution.vpa";
            case SpeciesId::Ultimate:
                return "/animations/ultimate/dragfiremon_evolution.vpa";
            default: return "/animations/baby/sparkmon_evolution.vpa";
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
    if ((model.pet.species() == SpeciesId::Champion || model.pet.species() == SpeciesId::Ultimate) &&
        strcmp(action, "hit") == 0)
        action = "punch";
    if (model.pet.species() == SpeciesId::Ultimate && strcmp(action, "dodge") == 0)
        action = "cast";
    if (model.pet.species() != SpeciesId::Rookie && model.pet.species() != SpeciesId::Champion &&
        model.pet.species() != SpeciesId::Ultimate &&
        (strcmp(action, "hit") == 0 || strcmp(action, "hurt") == 0 ||
         strcmp(action, "dodge") == 0 || strcmp(action, "block") == 0)) {
        action = (strcmp(action, "hit") == 0 || strcmp(action, "hurt") == 0) ? "punch" : "cast";
    }
    if (model.tired && (state == MotionState::Idle || state == MotionState::Walk)) action = "tired";
    else if (angryIdle(model)) action = "angry";
    if (model.pet.species() == SpeciesId::Baby && strcmp(action, "tired") != 0 && strcmp(action, "angry") != 0 &&
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
    for (uint8_t index = 0; index < menu_bar::count; ++index) {
        assets_.drawFrame(staticScene_, menu_bar::icons[index], 0, menu_bar::iconX(index), 2);
    }
    staticSceneReady_ = true;
    staticSceneNight_ = night;
}

void Renderer::drawSelector(uint8_t selected, bool calling) {
    const int16_t x = menu_bar::left(selected), width = menu_bar::width(selected);
    canvas_.drawRect(x, 0, width, 24, TFT_YELLOW);
    canvas_.drawRect(x + 1, 1, width - 2, 22, TFT_YELLOW);
    if (calling) {
        canvas_.setTextDatum(TR_DATUM);
        canvas_.setTextColor(TFT_YELLOW, TFT_BLACK);
        canvas_.drawString("*", x + width - 2, 1, 2);
        canvas_.setTextDatum(TL_DATUM);
    }
}

void Renderer::drawCallCue(const AppViewModel& model) {
    const CallReason reason = model.pet.callReason();
    if (reason == CallReason::None) return;
    const uint8_t cue = callMenuIndex(reason);
    if (cue < menu_bar::count && callBlinkOn(model.nowMs)) {
        const int16_t x = menu_bar::left(cue), width = menu_bar::width(cue);
        canvas_.drawRect(x, 0, width, 24, TFT_RED);
        canvas_.drawRect(x + 1, 1, width - 2, 22, TFT_RED);
    }
}

void Renderer::drawNeedBubble(const AppViewModel& model) {
    if (model.motion.state() != MotionState::Idle && model.motion.state() != MotionState::Walk) return;
    const char* path = cue::bubblePath(cue::forPet(model.pet, model.tired));
    if (path == nullptr) return;
    const auto position = cue::position(model.motion.x(), model.motion.y(), model.motion.direction());
    assets_.drawFrame(canvas_, path, 0, position.x, position.y, position.flip);
}

void Renderer::draw(const AppViewModel& model, int16_t statusSplitX, bool present) {
    const bool night = SleepRoutine::isNight(model.minuteOfDay);
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
    const bool emotion = angryIdle(model) || (model.tired &&
        (model.motion.state() == MotionState::Idle || model.motion.state() == MotionState::Walk));
    assets_.drawFrame(
        canvas_,
        animationPath(model),
        emotion ? (model.nowMs / 90) % 25 : model.motion.frame(),
        x,
        y,
        model.motion.direction() < 0 && !evolution,
        -1, 0,
        evolution ? 0 : 88
    );
    if (model.pet.injured()) {
        canvas_.setTextColor(TFT_YELLOW, TFT_BLACK);
        canvas_.drawString("*", x + spriteSize - 10, y + 4, 2);
    }
    if (statusSplitX <= 0) drawNeedBubble(model);
    if (statusSplitX <= 0 && (model.pet.sleep.asleep || model.motion.state() == MotionState::Sleep)) {
        // Quarter each RGB565 channel without changing byte order or navigation.
        for (int16_t py = 24; py < 135; ++py) {
            for (int16_t px = 0; px < 240; ++px) {
                const uint16_t color = canvas_.readPixel(px, py);
                canvas_.drawPixel(px, py, ((color >> 2) & 0x39E7));
            }
        }
    }
    if (present) {
        display_.startWrite();
        canvas_.pushSprite(0, 0);
        display_.endWrite();
    }
}

}  // namespace vpet
