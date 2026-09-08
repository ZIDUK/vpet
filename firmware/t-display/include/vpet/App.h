#pragma once

#include <stdint.h>

#include "vpet/Input.h"
#include "vpet/Motion.h"
#include "vpet/Navigation.h"
#include "vpet/Panels.h"
#include "vpet/PetState.h"
#include "vpet/Renderer.h"

namespace vpet {

class App {
public:
    App(Renderer& renderer, Panels& panels);
    void begin(uint32_t nowMs);
    void tick(uint32_t nowMs, InputEvent event);

private:
    void activate(uint32_t nowMs);

    Renderer& renderer_;
    Panels& panels_;
    PetState pet_;
    Motion motion_;
    Navigation navigation_;
    uint32_t lastTickMs_ = 0;
    uint32_t lastRenderMs_ = 0;
};

}  // namespace vpet
