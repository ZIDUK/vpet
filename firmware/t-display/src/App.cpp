#include "vpet/App.h"

namespace vpet {

App::App(Renderer& renderer, Panels& panels)
    : renderer_(renderer), panels_(panels), motion_(240, 135, 24, 88) {}

void App::begin(uint32_t nowMs) {
    lastTickMs_ = nowMs;
    lastRenderMs_ = nowMs - 50;
    motion_.setSpecies(pet_.species());
}

void App::activate(uint32_t nowMs) {
    Action action = Action::None;
    switch (navigation_.menuIndex()) {
        case 1: action = Action::Feed; break;
        case 2: action = Action::Training; break;
        case 3: action = Action::Battle; break;
        case 4: action = Action::Rest; break;
        default: return;
    }
    if (pet_.beginAction(action)) {
        motion_.startAction(action, nowMs);
    }
}

void App::tick(uint32_t nowMs, InputEvent event) {
    const uint32_t elapsed = nowMs - lastTickMs_;
    lastTickMs_ = nowMs;
    pet_.tick(elapsed);
    motion_.tick(nowMs);
    if (motion_.consumeActionCompleted()) {
        pet_.completeAction();
    }

    if (pet_.pendingAction() == Action::None && event != InputEvent::None) {
        if (navigation_.panel() == PanelId::Home && event == InputEvent::Action &&
            navigation_.menuIndex() >= 1 && navigation_.menuIndex() <= 4) {
            activate(nowMs);
        } else {
            navigation_.dispatch(event);
        }
    }

    navigation_.setDiscovered(
        pet_.species() != SpeciesId::Rookie,
        pet_.species() == SpeciesId::Ultimate
    );

    if (nowMs - lastRenderMs_ >= 50) {
        lastRenderMs_ = nowMs;
        if (navigation_.panel() == PanelId::Home) {
            renderer_.draw({pet_, motion_, navigation_.menuIndex()});
        } else {
            panels_.draw(navigation_, pet_);
        }
    }
}

}  // namespace vpet
