#pragma once
#include "vpet/ExplorationSession.h"
#include "vpet/Navigation.h"
namespace vpet {
struct Panels {
    int errors = 0;
    int explorationFrames = 0;
    ExplorationSession::Page explorePage = ExplorationSession::Page::Routes;
    bool exploreHome = false;
    bool away = false;
    uint8_t selectedMenu = 3;
    PanelId lastPanel = PanelId::Home;
    void invalidate() {}
    void drawStorageError(const char*) { ++errors; }
    template<class... T> void draw(const Navigation& n,T&&...) { lastPanel=n.panel(); }
    template<class... T> void drawPractice(T&&...) {}
    template<class... T> void drawTraining(T&&...) {}
    void drawExploration(const ExplorationSession& s,const PetState& p,uint64_t,uint32_t,const char*,bool home=false,uint8_t menu=3) {
        ++explorationFrames; explorePage=s.page; away=p.exploration.away(); exploreHome=home; selectedMenu=menu;
    }
};
}
