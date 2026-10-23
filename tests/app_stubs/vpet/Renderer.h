#pragma once
#include "vpet/PetState.h"
#include "vpet/Motion.h"
namespace vpet {
struct AppViewModel {
    const PetState& pet; const Motion& motion; uint8_t menuIndex; uint32_t nowMs; bool spanish;
    int minuteOfDay; bool tired;
    AppViewModel(const PetState& p,const Motion& m,uint8_t menu,uint32_t ms,bool es,int minute=720,bool sleepy=false)
        : pet(p),motion(m),menuIndex(menu),nowMs(ms),spanish(es),minuteOfDay(minute),tired(sleepy) {}
};
struct Renderer {
    int invalidations=0, minute=720; uint8_t menuIndex=0; bool sleeping=false, tired=false;
    void invalidate() { ++invalidations; }
    void draw(const AppViewModel& m) { menuIndex=m.menuIndex; minute=m.minuteOfDay; sleeping=m.pet.sleep.asleep; tired=m.tired; }
};
}
