#include <algorithm>
#include <cassert>
#include <cerrno>
#include <cstdio>
#include <cstring>
#include <dirent.h>
#include <limits>
#include <memory>
#include <new>
#include <set>
#include <string>
#include <sys/stat.h>
#include <sys/statvfs.h>
#include <unistd.h>
#include "vpet/LittleFsLearningRepository.h"
#include "vpet/LittleFsCollectionRepository.h"

static int opens=0, closes=0, seeks=0;
static bool failClose=false;
static std::set<FILE*> generations;
namespace std {
FILE* countedOpen(const char* path,const char* mode) {
    FILE* file=fopen(path,mode);
    const string name(path);
    if (file && (name.find("/current.bin")!=string::npos || name.find("/previous.bin")!=string::npos)) {
        ++opens; generations.insert(file);
    }
    return file;
}
int countedClose(FILE* file) {
    const bool generation=generations.erase(file)!=0;
    if (generation) ++closes;
    const int result=fclose(file);
    return generation && failClose ? EOF : result;
}
int countedSeek(FILE* file,long offset,int whence) { ++seeks; return fseek(file,offset,whence); }
}
#define fopen countedOpen
#define fclose countedClose
#define fseek countedSeek
#include "../firmware/t-display/src/LittleFsLearningRepository.cpp"
#undef fopen
#undef fclose
#undef fseek

int main(int argc,char** argv) {
    assert(argc==2);
    using namespace vpet;
    const std::string root=std::string(argv[1])+"/collection";
    LittleFsCollectionRepository repository(root.c_str());
    CollectionStore store(repository); CollectionState state; Settings settings;
    PetState pet, reserve;
    const uint32_t a[]={1,2,3,4}, b[]={5,6,7,8};
    pet.restore(SpeciesId::Champion,90,90,90,0,100,0);
    pet.profile=PetProfile::fromWords(a); pet.rollDna(42);
    reserve=pet; reserve.profile=PetProfile::fromWords(b);
    std::string first, second;
    assert(CollectionStore::capture(pet,settings,first));
    assert(CollectionStore::capture(reserve,settings,second));
    assert(store.migrate(state,first,&second));
    assert(store.saveActive(state,pet,settings));
    LittleFsLearningRepository files((root+"/policies").c_str());
    LearningState policy; assert(policy.record(1,0,0,0,50)); std::string ref;
    assert(files.prepare(pet.profile.petId(),policy,ref));
    opens=closes=seeks=0;
    assert(files.inspect());
    std::printf("LEARNING_SCAN_IO opens=%d closes=%d seeks=%d\n",opens,closes,seeks);
    std::fflush(stdout);
    assert(opens==2 && closes==2 && seeks<=6 && generations.empty());
    failClose=true;
    assert(!files.inspect() && generations.empty());
    failClose=false;
    // Each new operation reopens/validates bytes: no CRC or body cache.
    FILE* previous=std::fopen((root+"/previous.bin").c_str(),"r+b"); assert(previous);
    assert(!std::fseek(previous,-1,SEEK_END));
    const int byte=std::fgetc(previous); assert(byte!=EOF);
    assert(!std::fseek(previous,-1,SEEK_CUR));
    assert(std::fputc(byte^1,previous)!=EOF && !std::fclose(previous));
    assert(!files.inspect() && generations.empty());
    assert(std::string(files.failureReason())=="policy_collect_previous");
}
