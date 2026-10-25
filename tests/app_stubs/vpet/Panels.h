#pragma once
#include "vpet/ExplorationSession.h"
#include "vpet/Navigation.h"
#include "vpet/PracticeSession.h"
namespace vpet {
struct Panels {
    int errors = 0;
    int explorationFrames = 0;
    ExplorationSession::Page explorePage = ExplorationSession::Page::Routes;
    bool exploreHome = false;
    bool away = false;
    uint8_t selectedMenu = 3;
    PanelId lastPanel = PanelId::Home;
    uint8_t panelIndex = 0, detailPage = 0;
    int arenaResult = 0;
    void invalidate() {}
    void drawStorageError(const char*) { ++errors; }
    template<class... T> void draw(const Navigation& n,T&&...) {
        lastPanel=n.panel(); panelIndex=n.panelIndex(); detailPage=n.evolutionDetailPage();
    }
    void drawPractice(const PracticeSession& s,const PetState&,uint32_t,const char*) {
        arenaResult=s.battle.result;
    }
    template<class... T> void drawTraining(T&&...) {}
    void drawExploration(const ExplorationSession& s,const PetState& p,uint64_t,uint32_t,const char*,bool home=false,uint8_t menu=3) {
        ++explorationFrames; explorePage=s.page; away=p.exploration.away(); exploreHome=home; selectedMenu=menu;
    }
};
}
