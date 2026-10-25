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

content::Action visualAction(const AppViewModel& model) {
    if (model.pet.species() == SpeciesId::Egg)
        return model.motion.state() == MotionState::Hatch ? content::Action::Hatch : content::Action::Idle;
    if (model.tired && (model.motion.state() == MotionState::Idle || model.motion.state() == MotionState::Walk))
        return content::Action::Tired;
    if (angryIdle(model)) return content::Action::Angry;
    return static_cast<content::Action>(model.motion.state());
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
    return model.motion.definition().clip(model.pet.species(), visualAction(model)).path;
}

void Renderer::rebuildStaticScene(bool night, SpeciesId species, const content::PetDefinition& definition) {
    assets_.drawFrame(
        staticScene_,
        night ? definition.nightBackground : definition.background,
        0,
        0,
        0
    );
    staticScene_.fillRect(0, 0, 240, 24, TFT_BLACK);
    for (uint8_t index = 0; index < menu_bar::count; ++index) {
        assets_.drawFrame(staticScene_, menu_bar::icons[index], 0, menu_bar::iconX(index), 2);
        menu_bar::dimLockedIcon(staticScene_,species,index);
    }
    staticSceneReady_ = true;
    staticSceneNight_ = night;
    staticSceneSpecies_ = species;
    staticDefinition_ = &definition;
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
    const auto value = cue::forPet(model.pet, model.tired);
    const auto detail = cue::restDetail(model.pet,model.tired,model.minuteOfDay);
    const char* path = detail.kind==cue::RestKind::Energy
        ? (value.angry ? "/ui/mood/energy_angry.vpa" : "/ui/mood/energy.vpa") : cue::bubblePath(value);
    if (path == nullptr) return;
    const auto position = cue::position(model.motion.x(), model.motion.y(), model.motion.direction());
    assets_.drawFrame(canvas_, path, 0, position.x, position.y, position.flip);
}

void Renderer::draw(const AppViewModel& model, int16_t statusSplitX, bool present) {
    const bool night = SleepRoutine::isNight(model.minuteOfDay);
    if (!staticSceneReady_ || staticSceneNight_ != night || staticSceneSpecies_ != model.pet.species() ||
        staticDefinition_ != &model.motion.definition()) {
        rebuildStaticScene(night,model.pet.species(),model.motion.definition());
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
    int16_t visiblePetTop = -1;
    assets_.drawFrame(
        canvas_,
        animationPath(model),
        emotion ? (model.nowMs / model.motion.definition().clip(model.pet.species(), visualAction(model)).intervalMs)
                    % model.motion.definition().clip(model.pet.species(), visualAction(model)).frames : model.motion.frame(),
        x,
        y,
        model.motion.direction() < 0 && !evolution,
        -1, 0,
        evolution ? 0 : 88,
        &visiblePetTop
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
        const auto state = model.motion.state();
        if (model.pet.species() != SpeciesId::Egg && !model.pet.cold() && !model.pet.exploration.away() &&
            (state == MotionState::Sleep || state == MotionState::Idle || state == MotionState::Walk)) {
            const int16_t bubbleX = std::max(0, std::min(208, model.motion.x() + 28));
            const int16_t bubbleY = std::max(25, std::min(107, (visiblePetTop < 0 ? y : visiblePetTop) - 30));
            // Keep the sleep indicator legible after dimming the world and pet.
            assets_.drawFrame(canvas_, model.motion.direction() < 0 ? "/ui/mood/asleep_left.vpa" : "/ui/mood/asleep.vpa",
                              0, bubbleX, bubbleY);
        }
    }
    if (present) {
        display_.startWrite();
        canvas_.pushSprite(0, 0);
        display_.endWrite();
    }
}

}  // namespace vpet
