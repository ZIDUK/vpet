#include <algorithm>
#include <cerrno>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fcntl.h>
#include <fstream>
#include <map>
#include <string>
#include <sys/stat.h>
#include <unistd.h>
#include "vpet/LittleFsCollectionRepository.h"
#include "vpet/LittleFsLearningRepository.h"

#define CHECK(condition) do { if (!(condition)) { \
    std::fprintf(stderr, "line %d: %s\n", __LINE__, #condition); std::exit(1); \
} } while (false)

using namespace vpet;
namespace {
struct Control {
    bool requested=false, fail=false;
    size_t samples=0, cancelAt=0, events=0, eventAt=1, maxRead=0, maxWrite=0;
    std::string event, path, armEvent, armPath;
    bool armed=false;
    bool hit(const char* kind, const std::string& name) {
        if (!armEvent.empty() && !armed) {
            if (armEvent==kind && name.find(armPath)!=std::string::npos) armed=true;
            return false;
        }
        if (event!=kind || name.find(path)==std::string::npos || ++events<eventAt) return false;
        requested=true;
        return fail;
    }
} control;
std::map<FILE*,std::string> streams;
bool interrupt(void* context) {
    CHECK(context==&control);
    ++control.samples;
    return control.requested || (control.cancelAt && control.samples>=control.cancelAt);
}
void watch(const char* event, const std::string& path, bool fail=false) {
    control=Control{};
    control.event=event; control.path=path; control.fail=fail;
}
std::string contents(const std::string& path) {
    std::ifstream input(path,std::ios::binary);
    return std::string(std::istreambuf_iterator<char>(input),{});
}
void put(const std::string& path,const std::string& bytes) {
    std::ofstream output(path,std::ios::binary|std::ios::trunc);
    output.write(bytes.data(),bytes.size()); CHECK(output.good());
}
bool exists(const std::string& path) { struct stat info; return !::stat(path.c_str(),&info); }
void number(std::string& bytes,size_t at,uint64_t value,size_t length) {
    for (size_t i=0;i<length;++i) bytes[at+i]=static_cast<char>(value>>(8*i));
}
void checksum(std::string& bytes) {
    uint32_t crc=~uint32_t(0);
    for (size_t i=0;i<bytes.size();++i) {
        if (i>=20 && i<24) continue;
        crc^=static_cast<unsigned char>(bytes[i]);
        for (int bit=0;bit<8;++bit) crc=(crc>>1)^((crc&1)?0xedb88320u:0);
    }
    number(bytes,20,~crc,4);
}
struct Fixture {
    std::string root, policies, owner, first, second, firstBytes, secondBytes, current, previous, next;
    LittleFsCollectionRepository collection;
    LittleFsLearningRepository learning;
    CollectionStore store;
    CollectionState state;
    Settings settings;
    PetState pet;
    LearningState policy;
    explicit Fixture(const std::string& directory) :
        root(directory+"/collection"), policies(root+"/policies"),
        collection(root.c_str()), learning(policies.c_str()), store(collection) {
        const uint32_t words[]={1,2,3,4};
        pet.profile=PetProfile::fromWords(words); pet.rollDna(42);
        pet.restore(SpeciesId::Champion,90,90,90,0,100,0);
        owner=pet.profile.petId();
        std::string snapshot; CHECK(CollectionStore::capture(pet,settings,snapshot));
        CHECK(store.migrate(state,snapshot));
        // Large policies require several adapter chunks, including on readback.
        for (uint64_t i=1;i<=80;++i) CHECK(policy.record(i,0,0,0,50));
        CHECK(learning.prepare(owner,policy,first));
        CHECK(store.saveActive(state,pet,settings,first.c_str()));
        CHECK(policy.record(81,0,0,0,-20));
        CHECK(learning.prepare(owner,policy,second));
        CHECK(store.saveActive(state,pet,settings,second.c_str()));
        CHECK(policy.record(82,0,0,0,30));
        firstBytes=contents(policies+"/"+first); secondBytes=contents(policies+"/"+second);
        current=contents(root+"/current.bin"); previous=contents(root+"/previous.bin");
        next=current; number(next,8,state.sequence+1,8); checksum(next);
        CHECK(current.size()>2048 && contents(policies+"/"+first).size()>256);
        control=Control{};
    }
    void callbacks() {
        CollectionRepository& a=collection; LearningRepository& b=learning;
        a.setInterrupt(interrupt,&control); b.setInterrupt(interrupt,&control);
    }
    void stage() {
        CHECK(collection.begin(state.sequence,next.size()));
        CHECK(collection.write(0,next.data(),next.size()));
    }
    void preserved() {
        CHECK(contents(root+"/current.bin")==current);
        CHECK(contents(policies+"/"+first)==firstBytes);
        CHECK(contents(policies+"/"+second)==secondBytes);
    }
    void recovered() {
        collection.setInterrupt(nullptr,nullptr); learning.setInterrupt(nullptr,nullptr);
        collection.abort();
        CollectionState loaded; CHECK(store.load(loaded)==CollectionLoad::Loaded);
        CHECK(loaded.sequence==state.sequence);
        std::string record;
        CHECK(learning.read(owner,first.c_str(),record));
        CHECK(learning.read(owner,second.c_str(),record));
        collection.abort();
        CHECK(!exists(root+"/previous.bin.pending"));
    }
};
}

namespace std {
FILE* storageOpen(const char* path,const char* mode) {
    FILE* file=fopen(path,mode); if (file) streams[file]=path; return file;
}
int storageClose(FILE* file) { streams.erase(file); return fclose(file); }
size_t storageRead(void* data,size_t size,size_t count,FILE* file) {
    control.maxRead=std::max(control.maxRead,size*count);
    if (control.hit("read",streams.at(file))) return 0;
    return fread(data,size,count,file);
}
size_t storageWrite(const void* data,size_t size,size_t count,FILE* file) {
    control.maxWrite=std::max(control.maxWrite,size*count);
    if (control.hit("write",streams.at(file))) return 0;
    return fwrite(data,size,count,file);
}
int storageRemove(const char* path) {
    if (control.hit("remove",path)) { errno=EIO; return -1; }
    return remove(path);
}
}
int storageRename(const char* from,const char* to) {
    if (control.hit("rename",to)) { errno=EIO; return -1; }
    return ::rename(from,to);
}
int storageSync(int fd) {
    std::string path="<directory>";
    for (const auto& stream:streams) if (::fileno(stream.first)==fd) path=stream.second;
    if (control.hit("sync",path)) { errno=EIO; return -1; }
    return ::fsync(fd);
}

int main(int argc,char** argv) {
    CHECK(argc==3);
    const std::string mode=argv[1]; Fixture f(argv[2]);
    f.callbacks();
    if (mode.find("failure")!=std::string::npos) {
        f.collection.setInterrupt(nullptr,nullptr); f.learning.setInterrupt(nullptr,nullptr);
    }
    std::string output="unchanged";
    if (mode=="collection_begin") {
        control.requested=true;
        CHECK(!f.collection.begin(f.state.sequence,f.next.size()));
        CHECK(!exists(f.root+"/pending.bin"));
    } else if (mode=="callback_sampling") {
        CollectionRepository& a=f.collection; LearningRepository& b=f.learning;
        CHECK(!a.interrupted() && !b.interrupted());
        control.requested=true; CHECK(a.interrupted() && b.interrupted());
        control.requested=false; CHECK(!a.interrupted() && !b.interrupted());
        a.setInterrupt(nullptr,nullptr); b.setInterrupt(nullptr,nullptr);
        control.requested=true; CHECK(!a.interrupted() && !b.interrupted());
    } else if (mode=="collection_read") {
        watch("read","/current.bin"); size_t bytes=0;
        CHECK(f.collection.size(bytes)==CollectionRead::Present);
        std::string data(bytes,0); CHECK(!f.collection.read(0,&data[0],data.size()));
        CHECK(control.events==1 && control.maxRead<=256);
    } else if (mode=="collection_write" || mode=="collection_write_failure") {
        CHECK(f.collection.begin(f.state.sequence,f.next.size()));
        watch("write","/pending.bin",mode=="collection_write_failure");
        CHECK(!f.collection.write(0,f.next.data(),f.next.size()));
        CHECK(control.events==1 && control.maxWrite<=256);
    } else if (mode=="collection_prepared") {
        f.stage(); watch("read","/pending.bin");
        std::string data(f.next.size(),0);
        CHECK(!f.collection.readPrepared(0,&data[0],data.size()));
        CHECK(control.events==1 && control.maxRead<=256);
    } else if (mode=="collection_validation" || mode=="collection_read_failure" ||
               mode=="collection_backup" || mode=="collection_sync_failure") {
        f.stage();
        if (mode=="collection_backup") watch("write","/previous.");
        else if (mode=="collection_sync_failure") watch("sync","/pending.bin",true);
        else watch("read","/pending.bin",mode=="collection_read_failure");
        CHECK(!f.collection.commit(f.state.sequence+1));
        CHECK(control.events==1 && control.maxRead<=256 && control.maxWrite<=256);
    } else if (mode=="collection_before_publish") {
        f.stage(); watch("sync","/previous.");
        CHECK(!f.collection.commit(f.state.sequence+1));
        CHECK(control.requested);
    } else if (mode=="collection_backup_rename_failure") {
        f.stage(); watch("rename","/previous.bin",true);
        CHECK(!f.collection.commit(f.state.sequence+1));
        CHECK(control.requested && contents(f.root+"/previous.bin")==f.previous);
    } else if (mode=="collection_publish" || mode=="collection_rename_failure") {
        f.stage(); watch("rename","/current.bin",mode=="collection_rename_failure");
        const bool saved=f.collection.commit(f.state.sequence+1);
        CHECK(control.requested && saved==(mode=="collection_publish"));
        CHECK(contents(f.root+"/previous.bin")==f.current);
        if (saved) {
            CHECK(contents(f.root+"/current.bin")==f.next);
            f.collection.abort(); CHECK(contents(f.root+"/current.bin")==f.next);
            CHECK(f.collection.interrupted()); return 0;
        }
    } else if (mode=="collection_versions") {
        for (unsigned version:{1,2}) {
            auto bytes=f.current; number(bytes,4,version,4); checksum(bytes);
            put(f.root+"/current.bin",bytes);
            CHECK(f.collection.begin(f.state.sequence,f.next.size()));
            auto next=f.next; number(next,4,version,4); checksum(next);
            CHECK(f.collection.write(0,next.data(),next.size()));
            CHECK(f.collection.commit(f.state.sequence+1));
            CHECK(contents(f.root+"/current.bin")==next);
            CHECK(contents(f.root+"/previous.bin")==bytes);
        }
        auto future=f.current; number(future,4,3,4); checksum(future);
        put(f.root+"/current.bin",future);
        CHECK(!f.collection.begin(f.state.sequence,f.next.size()));
        return 0;
    } else if (mode=="collection_fresh_validation") {
        f.stage(); f.collection.abort();
        auto damaged=f.current; damaged.back()^=1; put(f.root+"/current.bin",damaged);
        CHECK(!f.collection.begin(f.state.sequence,f.next.size()));
        CHECK(contents(f.root+"/current.bin")==damaged); return 0;
    } else if (mode=="policy_read") {
        watch("read",f.second);
        CHECK(!f.learning.read(f.owner,f.second.c_str(),output));
        CHECK(output=="unchanged" && control.events==1 && control.maxRead<=256);
    } else if (mode=="policy_existing") {
        // Use the current policy's exact bytes to take the collision/reuse path.
        LearningState existing; CHECK(existing.decode(contents(f.policies+"/"+f.second).substr(38)));
        watch("read",f.second);
        CHECK(!f.learning.prepare(f.owner,existing,output)); CHECK(output=="unchanged");
        CHECK(control.events==1 && control.maxRead<=256);
    } else if (mode=="gc_current" || mode=="gc_previous") {
        const auto orphan=f.policies+"/P1111111111111111.11111111"; put(orphan,"orphan");
        watch("read",mode=="gc_current"?"/current.bin":"/previous.bin");
        CHECK(!f.learning.prepare(f.owner,f.policy,output));
        CHECK(exists(orphan) && output=="unchanged" && control.events==1 && control.maxRead<=256);
    } else if (mode=="gc_remove") {
        for (unsigned i=1;i<=3;++i) put(f.policies+"/P1111111111111111.1111111"+std::to_string(i),"orphan");
        watch("remove","/P1111");
        CHECK(!f.learning.prepare(f.owner,f.policy,output));
        CHECK(control.events==1 && output=="unchanged");
    } else if (mode=="gc_versions") {
        number(f.current,4,2,4); checksum(f.current);
        number(f.previous,4,2,4); checksum(f.previous);
        put(f.root+"/current.bin",f.current); put(f.root+"/previous.bin",f.previous);
        CHECK(f.learning.inspect());
        CHECK(f.learning.prepare(f.owner,f.policy,output));
    } else if (mode=="gc_corruption" || mode=="gc_future") {
        CHECK(f.learning.inspect());
        const auto orphan=f.policies+"/P1111111111111111.11111111"; put(orphan,"orphan");
        auto damaged=f.previous;
        if (mode=="gc_future") { number(damaged,4,3,4); checksum(damaged); }
        else damaged.back()^=1;
        put(f.root+"/previous.bin",damaged);
        CHECK(!f.learning.prepare(f.owner,f.policy,output)); CHECK(exists(orphan));
        CHECK(contents(f.root+"/previous.bin")==damaged);
    } else if (mode=="cancel_sweep") {
        f.stage(); control=Control{};
        CHECK(f.collection.commit(f.state.sequence+1)); const size_t checkpoints=control.samples;
        CHECK(checkpoints>20);
        for (size_t at=1;at<=checkpoints;++at) {
            put(f.root+"/current.bin",f.current); put(f.root+"/previous.bin",f.previous);
            control=Control{}; f.stage(); control=Control{}; control.cancelAt=at;
            CHECK(!f.collection.commit(f.state.sequence+1));
            f.preserved(); f.collection.abort();
        }
        control=Control{}; put(f.root+"/previous.bin",f.previous);
        CHECK(f.learning.prepare(f.owner,f.policy,output));
        const std::string orphan=output; const size_t policyCheckpoints=control.samples;
        CHECK(policyCheckpoints>20);
        CHECK(!std::remove((f.policies+"/"+orphan).c_str()));
        for (size_t at=1;at<=policyCheckpoints;++at) {
            control=Control{}; control.cancelAt=at; output="unchanged";
            CHECK(!f.learning.prepare(f.owner,f.policy,output)); CHECK(output=="unchanged");
            f.preserved();
            std::remove((f.policies+"/"+orphan).c_str());
            std::remove((f.policies+"/.pending").c_str());
        }
        std::printf("CANCEL_SWEEP collection=%zu policy=%zu\n",checkpoints,policyCheckpoints);
    } else {
        const bool publish=mode=="policy_publish" || mode=="policy_directory_sync_failure";
        if (mode=="policy_write" || mode=="policy_write_failure")
            watch("write","/.pending",mode=="policy_write_failure");
        else if (mode=="policy_readback" || mode=="policy_read_failure")
            watch("read","/.pending",mode=="policy_read_failure");
        else if (mode=="policy_before_publish" || mode=="policy_sync_failure")
            watch("sync","/.pending",mode=="policy_sync_failure");
        else if (mode=="policy_directory_sync_failure") {
            watch("sync","<directory>",true); control.eventAt=2; // GC sync precedes publication.
        } else watch("rename","/policies/P",mode=="policy_rename_failure");
        CHECK(f.learning.prepare(f.owner,f.policy,output)==publish);
        CHECK(control.requested && control.maxRead<=256 && control.maxWrite<=256);
        if (publish) {
            CHECK(output!="unchanged"); control=Control{};
            std::string record; CHECK(f.learning.read(f.owner,output.c_str(),record));
            CHECK(record==f.policy.encode());
        } else CHECK(output=="unchanged");
    }
    f.preserved(); f.recovered(); CHECK(streams.empty());
    return 0;
}
