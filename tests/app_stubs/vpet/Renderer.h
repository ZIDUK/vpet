#pragma once
#include "vpet/PetState.h"
#include "vpet/Motion.h"
namespace vpet {
struct AppViewModel { const PetState& pet; const Motion& motion; uint8_t menuIndex; uint32_t nowMs; bool spanish; };
struct Renderer { int invalidations=0; void invalidate() { ++invalidations; } void draw(const AppViewModel&) {} };
}
