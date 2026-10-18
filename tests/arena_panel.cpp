#include <cassert>
#include <iostream>
#include <LittleFS.h>
#include "vpet/Panels.h"
#include "vpet/MenuBar.h"

int main(int argc,char** argv) {
    assert(argc==5);
    assetRoot=argv[1];
    const int result=std::stoi(argv[2]), species=std::stoi(argv[3]);
    const bool spanish=std::string(argv[4])=="ES";
    vpet::PetState pet;
    pet.evolveTo(static_cast<vpet::SpeciesId>(species));
    vpet::PracticeSession session;
    session.page=vpet::PracticeSession::Page::Arena;
    session.battle.round=2;
    session.battle.result=result;
    session.awarded=true;
    session.updatedAt=1000;
    session.battle.actions[0]=1; session.battle.actions[1]=2;
    session.battle.damage[0]=8; session.battle.damage[1]=0;
    session.battle.player.equipped=3;
    if (species>0) {
        pet.practice.training=6;
        pet.practice.equipped=species==1 ? 11 : 27;
        session.battle.player.equipped=pet.practice.equipped;
        session.battle.actions[0]=species==1 ? 3 : 4;
    }
    TFT_eSPI output;
    TFT_eSprite canvas;
    canvas.setSwapBytes(true);
    TFT_eSprite scene;
    scene.setSwapBytes(true);
    vpet::AssetStore assets;
    assert(assets.begin().mounted);
    vpet::Panels panels(output,canvas,assets,&scene);
    TFT_eSprite reference;
    reference.setSwapBytes(true);
    vpet::Panels uncached(output,reference,assets);
    panels.drawPractice(session,pet,1000,spanish ? "ES" : "EN");
    uncached.drawPractice(session,pet,1000,spanish ? "ES" : "EN");
    assert(canvas.pixels==reference.pixels);
    const auto initial=canvas.pixels;
    auto labels=canvas.labels;
    for(const auto& label:labels)
        assert(label.find("ORDER")==std::string::npos && label.find("WHY:")==std::string::npos &&
               label.find("PEDISTE")==std::string::npos && label.find("MOTIVO:")==std::string::npos);
    if(result==1 || result==2) {
        const char* expected=result==1 ? (spanish ? "VICTORIA" : "VICTORY") :
                                          (spanish ? "DERROTA" : "DEFEAT");
        assert(std::find(labels.begin(),labels.end(),expected)!=labels.end());
        unsigned opaque=0;
        for(int y=57;y<105;++y) for(int x=174;x<222;++x)
            if(canvas.readPixel(x,y)!=TFT_DARKGREY) ++opaque;
        assert(opaque>150); // Catches the old 20px source crop: blank result portrait.
        panels.drawPractice(session,pet,1500,spanish ? "ES" : "EN");
        assert(canvas.pixels!=initial); // Reaction animates, including the feet.
    }
    if(!result) {
        assert(canvas.readPixel(120,100)!=TFT_BLACK); // Former feedback band is now arena.
        unsigned visible=0;
        for(int y=38;y<114;++y) for(int x=4;x<100;++x)
            if(canvas.readPixel(x,y)!=canvas.readPixel(120,y)) ++visible;
        assert(visible>500);
        const size_t opens=assetPathOpens["/backgrounds/background.vpa"];
        const size_t io=assetOpens;
        panels.drawPractice(session,pet,1100,spanish ? "ES" : "EN");
        assert(assetPathOpens["/backgrounds/background.vpa"]==opens);
        assert(assetOpens==io+2); // Only the two animated fighters read LittleFS.
        session.cursor=1;
        panels.drawPractice(session,pet,1200,spanish ? "ES" : "EN");
        uncached.drawPractice(session,pet,1200,spanish ? "ES" : "EN");
        assert(canvas.pixels==reference.pixels); // Cursor rebuilds only the footer.
        for (int cursor=0;cursor<session.count(pet);++cursor) {
            session.cursor=cursor;
            panels.drawPractice(session,pet,1200,spanish ? "ES" : "EN");
            uncached.drawPractice(session,pet,1200,spanish ? "ES" : "EN");
            assert(canvas.pixels==reference.pixels);
            const int selected=session.equippedAt(pet,cursor-1);
            if (cursor>0 && cursor<session.count(pet)-2 && selected>=3) {
                const auto name=spanish ? vpet::techniques::kCatalog[selected].es : vpet::techniques::kCatalog[selected].en;
                assert(std::find(canvas.labels.begin(),canvas.labels.end(),name)!=canvas.labels.end());
            }
        }
    }
    vpet::ExplorationSession explore;
    panels.drawExploration(explore,pet,1791979200,2000,spanish ? "ES" : "EN");
    const size_t chrome=assetPathOpens[vpet::menu_bar::icons[0]];
    explore.cursor=1;
    panels.drawExploration(explore,pet,1791979200,2050,spanish ? "ES" : "EN");
    assert(assetPathOpens[vpet::menu_bar::icons[0]]==chrome);
    for(auto page : {vpet::ExplorationSession::Page::Routes,vpet::ExplorationSession::Page::Stats,
                    vpet::ExplorationSession::Page::Confirm,vpet::ExplorationSession::Page::Clock}) {
        explore.page=page;
        for(int menu=0;menu<9;++menu) {
            panels.drawExploration(explore,pet,1791979200,2100,spanish ? "ES" : "EN",false,menu);
            uncached.drawExploration(explore,pet,1791979200,2100,spanish ? "ES" : "EN",false,menu);
            assert(canvas.pixels==reference.pixels);
        }
    }
    panels.invalidate();
    // The same shared memory may have held Home or another scene meanwhile.
    scene.fillSprite(TFT_RED);
    panels.drawPractice(session,pet,2200,spanish ? "ES" : "EN");
    uncached.drawPractice(session,pet,2200,spanish ? "ES" : "EN");
    assert(canvas.pixels==reference.pixels);
    std::cout << "ARENA_PANEL_OK\n";
}
