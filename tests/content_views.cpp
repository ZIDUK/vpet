#include <cassert>
#include <cstdio>
#include <LittleFS.h>
#include "vpet/Panels.h"
#include "vpet/Renderer.h"
#include "OtherPet.h"

int main(int argc, char** argv) {
    assert(argc == 4);
    using namespace vpet;
    assetRoot = argv[1];
    const auto& definition = content::otherDefinition();
    const std::string view = argv[2];
    const auto role = SpeciesId::Rookie;
    PetState pet;
    pet.restore(role, 80, 80, 80, 0, 90, 0);
    const auto before = pet.snapshot();
    TFT_eSPI output;
    TFT_eSprite canvas, scene;
    canvas.setSwapBytes(true); scene.setSwapBytes(true);
    AssetStore assets;
    assert(assets.begin().mounted);
    Panels panels(output, canvas, assets, &scene, definition);
    Renderer renderer(output, canvas, scene, assets);
    Motion motion(240,135,24,88,definition);
    motion.setSpecies(role);
    Navigation nav;
    nav.setCurrentSpecies(role);
    DateTimeMenu clock;
    if (view == "home") renderer.draw({pet,motion,0,0,true});
    else if (view == "training") {
        TrainingSession session;
        panels.drawTraining(session,pet,0,"ES");
    } else if (view == "arena") {
        PracticeSession session;
        session.page = PracticeSession::Page::Arena;
        panels.drawPractice(session,pet,0,"ES");
    } else if (view == "exploration") {
        ExplorationSession session;
        session.page = ExplorationSession::Page::Clock;
        panels.drawExploration(session,pet,1791979200,0,"ES");
    } else {
        nav.setPanel(view == "status" ? PanelId::Status :
            view == "tree" ? PanelId::EvolutionTree : PanelId::EvolutionDetail, 2);
        panels.draw(nav,pet,BleStatus::Off,clock,"ES",false);
    }
    assert(assetPathOpens[argv[3]] > 0);
    for (const auto& pair : assetPathOpens) {
        assert(pair.first.find("firemon") == std::string::npos);
        assert(pair.first.rfind("/battle/rookie_",0) != 0);
    }
    const auto after = pet.snapshot();
    assert(memcmp(&before,&after,sizeof(before)) == 0);
    printf("P6\n240 135\n255\n");
    for (int y=0;y<135;++y) for (int x=0;x<240;++x) {
        const uint16_t p=canvas.readPixel(x,y);
        const unsigned char rgb[]={static_cast<unsigned char>(((p>>11)&31)*255/31),
            static_cast<unsigned char>(((p>>5)&63)*255/63),static_cast<unsigned char>((p&31)*255/31)};
        fwrite(rgb,1,3,stdout);
    }
}
