#include <cassert>
#include <cstdio>
#include <map>
#include <LittleFS.h>
#include <TFT_eSPI.h>
#include "vpet/CollectionPanel.h"
#include "vpet/AssetStore.h"

struct Legacy : vpet::KeyValueStore {
    int32_t getInt(const char*,int32_t fallback) override { return fallback; }
    std::string getString(const char*,const char* fallback) override { return fallback; }
    bool putInt(const char*,int32_t) override { return true; }
    bool putString(const char*,const char*) override { return true; }
};
struct Repository : vpet::CollectionRepository {
    std::string data, pending; uint64_t sequence=0; int commits=0;
    vpet::CollectionRead size(size_t& n) override { n=data.size(); return n?vpet::CollectionRead::Present:vpet::CollectionRead::Missing; }
    bool read(size_t at,void* p,size_t n) override { if(at+n>data.size()) return false; std::memcpy(p,data.data()+at,n); return true; }
    bool begin(uint64_t s,size_t n) override { if(s!=sequence) return false; pending.assign(n,0); return true; }
    bool write(size_t at,const void* p,size_t n) override { if(at+n>pending.size()) return false; std::memcpy(&pending[at],p,n); return true; }
    bool readPrepared(size_t at,void* p,size_t n) override { if(at+n>pending.size()) return false; std::memcpy(p,pending.data()+at,n); return true; }
    bool commit(uint64_t s) override { data=pending; pending.clear(); sequence=s; ++commits; return true; }
    void abort() override { pending.clear(); }
};
int main(int argc,char** argv) {
    assert(argc==4); assetRoot=argv[1]; const std::string mode=argv[2];
    using namespace vpet;
    Legacy legacy; SettingsStore old(legacy); Repository repository; CollectionStore store(repository);
    PetState a,b,egg; Settings settings;
    uint32_t words[]={2,1,2,3}; a.profile=PetProfile::fromWords(words);
    words[0]=3; b.profile=PetProfile::fromWords(words);
    words[0]=4; egg.profile=PetProfile::fromWords(words);
    a.restore(SpeciesId::Rookie,100,90,90,0,100,0); a.setHappiness(90);
    b.restore(SpeciesId::Champion,100,90,90,0,100,0); b.setHappiness(90);
    CollectionState state;
    if(mode!="welcome" && mode!="enable") {
        std::string active, reserve;
        assert(CollectionStore::capture(a,settings,active) && CollectionStore::capture(b,settings,reserve));
        assert(store.migrate(state,active,&reserve));
        assert(store.addFounder(state,egg,settings,true));
    }
    TFT_eSprite canvas; canvas.setSwapBytes(true); AssetStore assets; assert(assets.begin().mounted);
    CollectionPanel panel(store,old,nullptr,nullptr,&canvas,&assets);
    panel.load(a,settings); panel.setPreview(a); panel.open();
    auto key=[&](InputEvent input){ panel.input(input,a,settings,{}); };
    if(mode=="enable") key(InputEvent::Action);
    else if(mode=="detail" || mode=="preferences" || mode=="activate") {
        if(mode=="activate") key(InputEvent::Next);
        key(InputEvent::Action);
        if(mode=="preferences") { for(int i=0;i<2;++i) key(InputEvent::Next); key(InputEvent::Action); }
        if(mode=="activate") key(InputEvent::Action);
    } else if(mode=="founder") { for(int i=0;i<4;++i) key(InputEvent::Next); key(InputEvent::Action); }
    else if(mode=="first" || mode=="second" || mode=="breed") {
        for(int i=0;i<5;++i) key(InputEvent::Next);
        key(InputEvent::Action);
        if(mode!="first") { key(InputEvent::Action); key(InputEvent::Next); }
        if(mode=="breed") key(InputEvent::Action);
    }
    const auto before=repository.data; const auto commits=repository.commits;
    panel.draw(argv[3]); panel.draw(argv[3]);
    assert(before==repository.data && commits==repository.commits);
    for(const auto& label:canvas.textDraws) {
        assert(label.x>=0 && label.y>=0 && label.x+int(label.value.size())*6<=240 && label.y+8<=135);
        assert(label.value.find("MIGRAR")==std::string::npos);
        assert(label.value.find(a.profile.petId())==std::string::npos);
    }
    printf("P6\n240 135\n255\n");
    for(auto color:canvas.pixels) {
        const unsigned char rgb[]={static_cast<unsigned char>(((color>>11)&31)*255/31),
            static_cast<unsigned char>(((color>>5)&63)*255/63),static_cast<unsigned char>((color&31)*255/31)};
        fwrite(rgb,1,3,stdout);
    }
}
