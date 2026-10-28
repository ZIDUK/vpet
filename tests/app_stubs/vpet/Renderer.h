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
    int invalidations=0, draws=0, minute=720; uint8_t menuIndex=0; bool sleeping=false, tired=false;
    int frameChanges=0, lastFrame=-1;
    int hunger=0, energy=0;
    uint32_t ageSeconds=0;
    SpeciesId species=SpeciesId::Egg;
    MotionState motionState=MotionState::Idle;
    void invalidate() { ++invalidations; }
    void draw(const AppViewModel& m) {
        ++draws;
        menuIndex=m.menuIndex; minute=m.minuteOfDay; sleeping=m.pet.sleep.asleep; tired=m.tired;
        if(lastFrame!=m.motion.frame()) ++frameChanges;
        lastFrame=m.motion.frame(); species=m.pet.species();
        motionState=m.motion.state();
        hunger=m.pet.hunger(); energy=m.pet.energy(); ageSeconds=m.pet.ageSeconds();
    }
};
}
