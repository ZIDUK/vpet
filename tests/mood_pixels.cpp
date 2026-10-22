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
    const uint8_t dna[]={1,2,3,0}; pet.restoreDna(dna);
    pet.setHappiness(mood);
    if(mode=="food" || mode=="eat") pet.setHunger(10);
    if(mode=="rest") pet.setEnergy(20);
    if(mode=="bedtime" || mode=="bedtime-low") {
        pet.sleep.bedtime=1320; pet.setEnergy(mode=="bedtime-low" ? 20 : 80);
    }
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
        const bool bedtime=mode=="bedtime" || mode=="bedtime-low";
        const bool tired=mode=="rest" || bedtime;
        const int minute=bedtime ? 1320 : 720;
        renderer.draw({pet,motion,5,0,es,minute,tired},mode=="panel"?104:0);
        const auto cue=vpet::cue::forPet(pet,tired);
        const char* bubble=mode=="rest" ? (cue.angry ? "/ui/mood/energy_angry.vpa" : "/ui/mood/energy.vpa") :
            vpet::cue::bubblePath(cue);
        const bool hidden=mode=="eat" || mode=="sleep" || mode=="panel";
        if(bubble) assert((assetPathOpens[bubble]>0)==!hidden);
        if(mode=="rest" || bedtime) {
            const auto pos=vpet::cue::position(x,43,1);
            const int left=vpet::cue::restLabelX(pos.x);
            assert(std::find(canvas.labels.begin(),canvas.labels.end(),bedtime ?
                (es?"HORA DE DORMIR":"BEDTIME") : (es?"POCA ENERGIA":"LOW ENERGY"))!=canvas.labels.end());
            assert(std::find(canvas.labels.begin(),canvas.labels.end(),bedtime?"22:00":"20/30")!=canvas.labels.end());
            if(!bedtime) for(int col=0;col<54;++col)
                assert(canvas.readPixel(left+43+col,37)==(col<36?TFT_YELLOW:TFT_DARKGREY));
            canvas.labels.clear(); pet.setEnergy(80);
            renderer.draw({pet,motion,5,0,es,720,false});
            assert(canvas.labels.empty());
            assert(canvas.readPixel(left+43,37)==scene.readPixel(left+43,37));
            pet.setEnergy(bedtime && mode!="bedtime-low" ? 80 : 20);
            renderer.draw({pet,motion,5,0,es,minute,tired});
        }
    }
    printf("P6\n240 135\n255\n");
    for(int y=0;y<135;++y) for(int x=0;x<240;++x) {
        const uint16_t c=canvas.readPixel(x,y);
        const unsigned char rgb[]={static_cast<unsigned char>(((c>>11)&31)*255/31),
            static_cast<unsigned char>(((c>>5)&63)*255/63),static_cast<unsigned char>((c&31)*255/31)};
        fwrite(rgb,1,3,stdout);
    }
}
