#pragma once
#define Panels ProgressBasePanels
#include "../../app_stubs/vpet/Panels.h"
#undef Panels
#include <utility>

namespace vpet {
struct Panels : ProgressBasePanels {
    bool errorVisible=false;
    void drawStorageError(const char* language) {
        ProgressBasePanels::drawStorageError(language); errorVisible=true;
    }
    template<class... T> void draw(T&&... args) {
        ProgressBasePanels::draw(std::forward<T>(args)...); errorVisible=false;
    }
    void drawPractice(const PracticeSession& s,const PetState& p,uint32_t ms,const char* language) {
        ProgressBasePanels::drawPractice(s,p,ms,language); errorVisible=false;
    }
    void drawTraining(const TrainingSession& s,const PetState& p,uint32_t ms,const char* language) {
        ProgressBasePanels::drawTraining(s,p,ms,language); errorVisible=false;
    }
    void drawExploration(const ExplorationSession& s,const PetState& p,uint64_t now,uint32_t ms,
                         const char* language,bool home=false,uint8_t menu=3) {
        ProgressBasePanels::drawExploration(s,p,now,ms,language,home,menu); errorVisible=false;
    }
};
}
