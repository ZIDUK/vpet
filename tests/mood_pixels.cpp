#include <cassert>
#include <cstdio>
#include <LittleFS.h>
#include "vpet/Renderer.h"
#include "vpet/Panels.h"
#include "vpet/UiCue.h"

int main(int argc,char** argv) {
    assert(argc==6); assetRoot=argv[1];
    const std::string mode=argv[2];
    const int mood=atoi(argv[3]), x=atoi(argv[4]);
    vpet::PetState pet;
    pet.evolveTo(vpet::SpeciesId::Rookie);
    pet.setHappiness(mood);
    if(mode=="food" || mode=="eat") pet.setHunger(10);
    if(mode=="rest") pet.setEnergy(20);
    if(mode=="hurt") pet.restoreInjury(true,1,false);
    if(mode=="egg") { pet.resetToEgg(); pet.setHunger(0); }
    if(mode=="dead") { pet.setHunger(0); pet.restoreInjury(true,15,true); }
    if(mode=="cold") { pet.setHunger(0); pet.setCold(true); }
    if(mode=="away") {
        assert(pet.exploration.start(pet,vpet::ExploreRoute::Patio,vpet::CombatStat::Hp,1000));
        pet.setHunger(0);
    }
    if(mode=="sleep") { pet.sleep.asleep=true; pet.setHunger(0); }
    vpet::Motion motion(x*2+88,135,24,88); motion.setSpecies(pet.species());
    if(mode=="eat") motion.startAction(vpet::Action::Feed,0);
    if(mode=="sleep") motion.startAction(vpet::Action::Rest,0);
    TFT_eSPI display; TFT_eSprite canvas,scene; canvas.setSwapBytes(true); scene.setSwapBytes(true);
    vpet::AssetStore assets; assert(assets.begin().mounted);
    vpet::Renderer renderer(display,canvas,scene,assets);
    if(std::string(argv[5])=="status") {
        vpet::Navigation navigation; navigation.setPanel(vpet::PanelId::Status);
        vpet::DateTimeMenu clock;
        vpet::Panels panels(display,canvas,assets,&scene);
        panels.draw(navigation,pet,vpet::BleStatus::Off,clock,"ES",false);
        assert(assetPathOpens[vpet::cue::facePath(vpet::cue::forPet(pet).face)]>0);
    } else {
        renderer.draw({pet,motion,5,0,false,720,false},mode=="panel"?104:0);
        const char* bubble=vpet::cue::bubblePath(vpet::cue::forPet(pet));
        const bool hidden=mode=="eat" || mode=="sleep" || mode=="panel";
        if(bubble) assert((assetPathOpens[bubble]>0)==!hidden);
    }
    printf("P6\n240 135\n255\n");
    for(int y=0;y<135;++y) for(int x=0;x<240;++x) {
        const uint16_t c=canvas.readPixel(x,y);
        const unsigned char rgb[]={static_cast<unsigned char>(((c>>11)&31)*255/31),
            static_cast<unsigned char>(((c>>5)&63)*255/63),static_cast<unsigned char>((c&31)*255/31)};
        fwrite(rgb,1,3,stdout);
    }
}
