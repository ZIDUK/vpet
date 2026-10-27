#include <algorithm>
#include <cassert>
#include <cerrno>
#include <cstdio>
#include <cstring>
#include <limits>
#include <vector>
#include <sys/stat.h>
#include <sys/statvfs.h>
#include <unistd.h>
#include "vpet/LittleFsCollectionRepository.h"

static int opens=0, seeks=0;
namespace std {
FILE* countedOpen(const char* path,const char* mode) { ++opens; return fopen(path,mode); }
int countedSeek(FILE* file,long offset,int whence) { ++seeks; return fseek(file,offset,whence); }
}
#define fopen countedOpen
#define fseek countedSeek
#include "../firmware/t-display/src/LittleFsCollectionRepository.cpp"
#undef fopen
#undef fseek

int main() {
    using namespace vpet;
    char path[]="/tmp/vpet-io-XXXXXX";
    const char* temporary=mkdtemp(path); assert(temporary);
    const std::string root=std::string(temporary)+"/collection";
    {
        LittleFsCollectionRepository repository(root.c_str());
        CollectionStore store(repository); CollectionState state; Settings settings;
        PetState active, reserve;
        active.restore(SpeciesId::Champion,70,40,70,0,100,0);
        const uint32_t a[]={1,2,3,4}, b[]={5,6,7,8};
        active.profile=PetProfile::fromWords(a); active.rollDna(7);
        reserve=active; reserve.profile=PetProfile::fromWords(b);
        std::string first,second;
        assert(CollectionStore::capture(active,settings,first));
        assert(CollectionStore::capture(reserve,settings,second));
        assert(store.migrate(state,first,&second));
        opens=seeks=0;
        active.setEnergy(60);
        assert(store.saveActive(state,active,settings));
        std::printf("SAVE_IO opens=%d seeks=%d\n",opens,seeks);
        std::fflush(stdout);
        assert(opens<=12 && seeks<=24);
        size_t bytes=0;
        assert(repository.size(bytes)==CollectionRead::Present);
        std::vector<char> committed(bytes), readback(bytes);
        assert(repository.read(0,committed.data(),bytes));
        assert(repository.begin(state.sequence,bytes));
        assert(repository.write(0,committed.data(),8));
        assert(repository.readPrepared(0,readback.data(),8));
        assert(repository.write(8,committed.data()+8,bytes-8)); // Read -> write at the same cursor.
        assert(repository.readPrepared(0,readback.data(),bytes) && readback==committed);
        repository.abort();
        assert(repository.size(bytes)==CollectionRead::Present);
        assert(repository.read(0,readback.data(),bytes) && readback==committed);
        // A new size probe must invalidate cached reads after external corruption.
        FILE* file=std::fopen((root+"/current.bin").c_str(),"r+b"); assert(file);
        assert(std::fputc(0,file)!=EOF && std::fclose(file)==0);
        assert(store.load(state)==CollectionLoad::Corrupt);
    }
    for(const char* name : {"current.bin","previous.bin","pending.bin"})
        std::remove((root+"/"+name).c_str());
    assert(rmdir(root.c_str())==0 && rmdir(temporary)==0);
}
