#include "vpet/App.h"

namespace vpet {

App::App(Renderer& renderer)
    : renderer_(renderer), motion_(240, 135, 24, 88) {}

void App::begin(uint32_t nowMs) {
    lastTickMs_ = nowMs;
    lastRenderMs_ = nowMs - 50;
    motion_.setSpecies(pet_.species());
}

void App::activate(uint32_t nowMs) {
    Action action = Action::None;
    switch (menuIndex_) {
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

    if (pet_.pendingAction() == Action::None) {
        if (event == InputEvent::Next) {
            menuIndex_ = (menuIndex_ + 1) % 8;
        } else if (event == InputEvent::Action) {
            activate(nowMs);
        } else if (event == InputEvent::Back) {
            menuIndex_ = 0;
        }
    }

    if (nowMs - lastRenderMs_ >= 50) {
        lastRenderMs_ = nowMs;
        renderer_.draw({pet_, motion_, menuIndex_});
    }
}

}  // namespace vpet
