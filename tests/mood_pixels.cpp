#include <cassert>
#include <cstdio>
#include <LittleFS.h>
#include "vpet/Renderer.h"
#include "vpet/Panels.h"
#include "vpet/UiCue.h"

int main(int argc,char** argv) {
    assert(argc==6 || argc==7); assetRoot=argv[1];
    const bool es=argc==6 || std::string(argv[6])=="ES";
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
    const std::string panel=argv[5];
    if(panel=="status" || panel=="restmenu" || panel=="options") {
        vpet::Navigation navigation;
        navigation.setPanel(panel=="restmenu" ? vpet::PanelId::Rest : panel=="options" ?
                            vpet::PanelId::Options : vpet::PanelId::Status,panel=="status"?0:x);
        vpet::DateTimeMenu clock;
        vpet::Panels panels(display,canvas,assets,&scene);
        panels.draw(navigation,pet,vpet::BleStatus::Off,clock,es?"ES":"EN",false);
        if(panel=="status") assert(assetPathOpens[vpet::cue::facePath(vpet::cue::forPet(pet).face)]>0);
        else if(panel=="restmenu") {
            const auto& labels=canvas.labels;
            const char* light=mode=="sleep" ? (es?"ENCENDER LUZ":"LIGHTS ON") : (es?"APAGAR LUZ":"LIGHTS OFF");
            assert(std::find(labels.begin(),labels.end(),light)!=labels.end());
            assert(std::find(labels.begin(),labels.end(),es?"VOLVER":"BACK")!=labels.end());
            for(const auto& label:labels) assert(label.find("COLD")==std::string::npos &&
                label.find("FRIO")==std::string::npos && label.find("BACKUP")==std::string::npos &&
                label.find("RESERVA")==std::string::npos);
        } else if(x==vpet::option_menu::pause) {
            const char* before=es ? (mode=="cold"?"PAUSAR CRIANZA  SI":"PAUSAR CRIANZA  NO") :
                                   (mode=="cold"?"PAUSE PET  ON":"PAUSE PET  OFF");
            assert(std::find(canvas.labels.begin(),canvas.labels.end(),before)!=canvas.labels.end());
            assert(std::find(canvas.labels.begin(),canvas.labels.end(),"BACK")!=canvas.labels.end());
            canvas.labels.clear(); pet.setCold(!pet.cold());
            panels.draw(navigation,pet,vpet::BleStatus::Off,clock,es?"ES":"EN",false);
            const char* after=es ? (mode=="cold"?"PAUSAR CRIANZA  NO":"PAUSAR CRIANZA  SI") :
                                  (mode=="cold"?"PAUSE PET  OFF":"PAUSE PET  ON");
            assert(std::find(canvas.labels.begin(),canvas.labels.end(),after)!=canvas.labels.end());
        }
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
