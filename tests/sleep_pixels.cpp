#include <cassert>
#include <cstdio>
#include <LittleFS.h>
#include "vpet/Renderer.h"
int main(int argc,char** argv) {
    assert(argc==7); assetRoot=argv[1];
    vpet::PetState pet; pet.evolveTo(static_cast<vpet::SpeciesId>(atoi(argv[2])));
    vpet::Motion motion(240,135,24,88); motion.setSpecies(pet.species());
    const bool sleeping=std::string(argv[3])=="sleep";
    if (sleeping) motion.startAction(vpet::Action::Rest,0);
    TFT_eSPI display; TFT_eSprite canvas,scene; canvas.setSwapBytes(true); scene.setSwapBytes(true);
    vpet::AssetStore assets; assert(assets.begin().mounted);
    vpet::Renderer renderer(display,canvas,scene,assets);
    const int minute=atoi(argv[4]), frame=atoi(argv[5]);
    if (sleeping) motion.tick(frame*105);
    const bool tired=std::string(argv[3])=="tired";
    renderer.draw({pet,motion,5,static_cast<uint32_t>(frame*90),atoi(argv[6])!=0,minute,tired});
    const auto expected=canvas.pixels;
    const auto first=assetPathOpens["/backgrounds/background_night.vpa"]+assetPathOpens["/backgrounds/background.vpa"];
    renderer.draw({pet,motion,5,static_cast<uint32_t>(frame*90),false,minute,tired});
    assert(expected==canvas.pixels); // Darkness must not accumulate across frames.
    if(sleeping) {
        motion.wake(0);
        renderer.draw({pet,motion,5,0,false,minute,false});
        for(int y=0;y<24;++y) for(int x=0;x<240;++x)
            assert(canvas.readPixel(x,y)==expected[y*240+x]);
        assert(canvas.readPixel(4,30)==scene.readPixel(4,30));
        assert(canvas.readPixel(4,30)!=expected[30*240+4]);
        motion.startAction(vpet::Action::Rest,0);
        motion.tick(frame*105);
        renderer.draw({pet,motion,5,static_cast<uint32_t>(frame*90),false,minute,tired});
    }
    assert(first==assetPathOpens["/backgrounds/background_night.vpa"]+assetPathOpens["/backgrounds/background.vpa"]);
    const bool night=vpet::SleepRoutine::isNight(minute);
    renderer.draw({pet,motion,5,static_cast<uint32_t>(frame*90),false,night?720:1080,tired});
    assert(first+1==assetPathOpens["/backgrounds/background_night.vpa"]+assetPathOpens["/backgrounds/background.vpa"]);
    assert(expected!=canvas.pixels);
    renderer.draw({pet,motion,5,static_cast<uint32_t>(frame*90),false,minute,tired});
    printf("P6\n240 135\n255\n");
    for(int y=0;y<135;++y) for(int x=0;x<240;++x) {
        const uint16_t c=canvas.readPixel(x,y);
        const unsigned char rgb[]={static_cast<unsigned char>(((c>>11)&31)*255/31),
            static_cast<unsigned char>(((c>>5)&63)*255/63),static_cast<unsigned char>((c&31)*255/31)};
        fwrite(rgb,1,3,stdout);
    }
}
