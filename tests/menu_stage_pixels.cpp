#include <cassert>
#include <cstdio>
#include <LittleFS.h>
#include "vpet/MenuBar.h"
#include "vpet/Panels.h"
#include "vpet/Renderer.h"
#include "vpet/Strings.h"

int main(int argc, char** argv) {
    assert(argc == 5 || argc == 6);
    assetRoot = argv[1];
    const auto species = static_cast<vpet::SpeciesId>(atoi(argv[2]));
    const std::string view = argv[3];
    const uint8_t selected = atoi(argv[4]);
    const bool spanish = argc == 5 || std::string(argv[5]) == "ES";
    vpet::PetState pet;
    pet.evolveTo(vpet::SpeciesId::Rookie);
    TFT_eSPI display;
    TFT_eSprite canvas, scene;
    canvas.setSwapBytes(true);
    scene.setSwapBytes(true);
    vpet::AssetStore assets;
    assert(assets.begin().mounted);
    vpet::Renderer renderer(display, canvas, scene, assets);
    vpet::Panels panels(display, canvas, assets, view == "explore-uncached" ? nullptr : &scene);
    vpet::Motion motion(240,135,24,88);
    vpet::Navigation navigation;
    navigation.setPanel(vpet::PanelId::Status);
    vpet::DateTimeMenu clock;
    vpet::ExplorationSession exploration;
    auto draw = [&]() {
        motion.setSpecies(pet.species());
        if (view == "home") renderer.draw({pet,motion,selected,0,true});
        else if (view == "status") panels.draw(navigation,pet,vpet::BleStatus::Off,clock,"ES",false);
        else if (view == "evolution") {
            navigation.setCurrentSpecies(pet.species());
            navigation.setPanel(vpet::PanelId::EvolutionTree);
            navigation.setPanelIndex(selected);
            panels.draw(navigation,pet,vpet::BleStatus::Off,clock,spanish ? "ES" : "EN",false);
        }
        else panels.drawExploration(exploration,pet,1791979200,0,"ES",false,selected);
    };
    auto menuOpens = [&]() {
        size_t count = 0;
        // Pedia is also drawn inside the route list, outside the cached bar.
        for (int i=0;i<vpet::menu_bar::count;++i)
            if (i != 7) count += assetPathOpens[vpet::menu_bar::icons[i]];
        return count;
    };
    draw();
    pet.evolveTo(species);
    draw(); // The same renderer must notice evolution without manual invalidation.
    const auto warm = menuOpens();
    draw();
    if (view != "explore-uncached") assert(menuOpens() == warm);
    if (view == "evolution") {
        bool nameFound=false, progressFound=false;
        for (const auto& text : canvas.textDraws) {
            if (text.value == vpet::copy::evoShort(navigation.currentStage(),spanish)) {
                assert(text.foreground == 0x31C7);
                nameFound=true;
            }
            if (text.value.find(vpet::copy::evoNow(spanish)) == 0) {
                assert(text.foreground == 0x31C7);
                progressFound=true;
            }
        }
        assert(nameFound && progressFound);
    }
    printf("P6\n240 135\n255\n");
    for (int y=0;y<135;++y) for (int x=0;x<240;++x) {
        const uint16_t pixel=canvas.readPixel(x,y);
        const unsigned char rgb[]={static_cast<unsigned char>(((pixel>>11)&31)*255/31),
            static_cast<unsigned char>(((pixel>>5)&63)*255/63),static_cast<unsigned char>((pixel&31)*255/31)};
        fwrite(rgb,1,3,stdout);
    }
}
