#include <cassert>
#include <cstdio>
#include <LittleFS.h>
#include <TFT_eSPI.h>
#include "vpet/AssetStore.h"

int main(int argc, char** argv) {
    assert(argc==2); assetRoot=argv[1];
    vpet::AssetStore store;
    TFT_eSprite canvas;
    canvas.setSwapBytes(true);
    assert(store.begin().mounted);
    for(int i=0;i<10;++i) {
        char path[32]; snprintf(path,sizeof(path),"/training/icon%d.vpa",i);
        int16_t top=-1;
        assert(store.drawFrame(canvas,path,0,i*16,0,false,-1,0,0,&top));
        assert(top==2);
    }
    const auto expected=canvas.pixels;
    const size_t opens=assetOpens, reads=assetReads;
    for(int repeat=0;repeat<20;++repeat) {
        canvas.fillSprite(0);
        for(int i=0;i<10;++i) {
            char path[32]; snprintf(path,sizeof(path),"/training/icon%d.vpa",i);
            int16_t top=-1;
            assert(store.drawFrame(canvas,path,repeat,i*16,0,false,-1,0,0,&top));
            assert(top==2);
        }
        assert(canvas.pixels==expected);
    }
    assert(assetOpens==opens && assetReads==reads);
    // A new animated frame still comes from LittleFS, without evicting icons.
    assert(store.drawFrame(canvas,"/training/pet.vpa",1,0,30));
    assert(assetOpens==opens+1);
    const size_t beforeFrame=assetReads;
    assert(store.drawFrame(canvas,"/training/pet.vpa",0,0,30));
    assert(assetReads-beforeFrame<=7);
    assert(store.drawFrame(canvas,"/training/icon0.vpa",0,0,0));
    assert(assetOpens==opens+2);
    // Cached transparency preserves the current background, not the old one.
    vpet::AssetStore cold;
    TFT_eSprite reference;
    reference.setSwapBytes(true);
    for(uint16_t background : {uint16_t(0),uint16_t(0xFFFF),uint16_t(0x284B)}) {
        canvas.fillSprite(background); reference.fillSprite(background);
        assert(store.drawFrame(canvas,"/training/icon0.vpa",0,3,4));
        assert(cold.drawFrame(reference,"/training/icon0.vpa",0,3,4));
        assert(canvas.pixels==reference.pixels);
    }
    // Special rendering modes must not reuse an untransformed cached image.
    for(int mode=0;mode<3;++mode) {
        canvas.fillSprite(0x284B); reference.fillSprite(0x284B);
        assert(store.drawFrame(canvas,"/training/icon0.vpa",0,-3,4,mode==0,mode==1?0xF800:-1,mode==2?100:0));
        assert(cold.drawFrame(reference,"/training/icon0.vpa",0,-3,4,mode==0,mode==1?0xF800:-1,mode==2?100:0));
        assert(canvas.pixels==reference.pixels);
    }
    // The eleventh static icon evicts the least recently used entry safely.
    assert(store.drawFrame(canvas,"/training/icon10.vpa",0,0,0));
    const size_t beforeReload=assetOpens;
    assert(store.drawFrame(canvas,"/training/icon1.vpa",0,0,0));
    assert(assetOpens==beforeReload+1);
    assert(sizeof(vpet::AssetStore)<7500);
    store.releaseTrainingCache();
    const size_t beforeReleaseReload=assetOpens;
    assert(store.drawFrame(canvas,"/training/icon1.vpa",0,0,0));
    assert(assetOpens==beforeReleaseReload+1);
    const size_t beforeReleasedCacheHit=assetOpens;
    assert(store.drawFrame(canvas,"/training/icon1.vpa",0,0,0));
    assert(assetOpens==beforeReleasedCacheHit);
    store.begin();
    const size_t beforeReset=assetOpens;
    assert(store.drawFrame(canvas,"/training/icon1.vpa",0,0,0));
    assert(assetOpens==beforeReset+1);
    // Status portraits must sample all 88px, including feet, not an icon crop.
    canvas.fillSprite(0x284B); reference.fillSprite(0x284B);
    assert(store.drawFrame(reference,"/training/portrait.vpa",0,0,0));
    assert(reference.readPixel(0,0)==TFT_RED);
    assert(store.drawFrameScaled(canvas,"/training/portrait.vpa",0,12,59,76,76,false,-1,0,88));
    for(int y=0;y<76;++y) for(int x=0;x<76;++x)
        assert(canvas.readPixel(12+x,59+y)==reference.readPixel(x*88/76,y*88/76));
    assert(canvas.readPixel(12,58)==0x284B);
    assert(canvas.readPixel(88,134)==0x284B);
    assert(!store.drawFrameScaled(canvas,"/training/portrait.vpa",0,0,0,76,76,false,-1,0,0));
    assert(!store.drawFrameScaled(canvas,"/training/portrait.vpa",0,0,0,76,76,false,-1,0,240));
    int16_t top=123;
    assert(!store.drawFrame(canvas,"/missing.vpa",0,0,0,false,-1,0,0,&top));
    assert(top==-1);
}
