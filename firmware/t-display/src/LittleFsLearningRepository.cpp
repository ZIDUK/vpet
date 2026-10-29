#include "vpet/LittleFsLearningRepository.h"
#include "vpet/StorageTiming.h"
#include <cerrno>
#include <cstdio>
#include <cstring>
#include <climits>
#include <dirent.h>
#include <memory>
#include <new>
#include <set>
#include <sys/stat.h>
#include <unistd.h>
#ifdef ARDUINO
#include <LittleFS.h>
#else
#include <fcntl.h>
#include <sys/statvfs.h>
#endif

namespace vpet {
namespace {
bool ownerValid(const std::string& owner) {
    return owner.size()==32 && owner!=std::string(32,'0') &&
        owner.find_first_not_of("0123456789abcdef")==std::string::npos;
}
bool compactRefValid(const std::string& ref) {
    return ref.size()==26 && ref[0]=='P' && ref[17]=='.' &&
        ref.substr(1,16).find_first_not_of("0123456789abcdef")==std::string::npos &&
        ref.substr(18).find_first_not_of("0123456789abcdef")==std::string::npos;
}
bool refValid(const std::string& owner,const std::string& ref) {
    return ownerValid(owner) && (compactRefValid(ref) ||
        (ref.size()<=64 && ref.size()>43 && ref.compare(0,34,"L"+owner+".")==0 &&
         ref.find_first_not_of("L0123456789abcdef.")==std::string::npos && ref.find("..") == std::string::npos));
}
uint32_t checksum(const std::string& data) {
    uint32_t crc=0xffffffffu;
    for (const unsigned char c:data) {
        crc^=c;
        for (int i=0;i<8;++i) crc=(crc>>1)^((crc&1)?0xedb88320u:0);
    }
    return ~crc;
}
std::string compactKey(const std::string& envelope) {
    // Hash the full owner-bound envelope, including its sequence. Always verify
    // existing bytes on a collision; hashes are identity hints, not authority.
    uint64_t hash=14695981039346656037ULL;
    for (const unsigned char c:envelope) hash=(hash^c)*1099511628211ULL;
    char key[27];
    std::snprintf(key,sizeof(key),"P%016llx.%08x",static_cast<unsigned long long>(hash),checksum(envelope));
    return key;
}
std::FILE* openFile(const std::string& path,const char* mode) {
    auto* file=std::fopen(path.c_str(),mode);
    if (file) std::setvbuf(file,nullptr,_IONBF,0);
    return file;
}
bool readFile(const std::string& path,std::string& record) {
    struct stat info;
    if (::stat(path.c_str(),&info) || !S_ISREG(info.st_mode) || info.st_size<38 ||
        info.st_size>static_cast<off_t>(LittleFsLearningRepository::kMaxBlobBytes)) return false;
    auto* file=openFile(path,"rb"); if (!file) return false;
    std::string next(static_cast<size_t>(info.st_size),0);
    const bool ok=std::fread(&next[0],1,next.size(),file)==next.size();
    const bool closed=std::fclose(file)==0;
    if (!ok || !closed) return false;
    record=std::move(next); return true;
}
bool budget(const std::string& path) {
    uint64_t free=0;
#ifdef ARDUINO
    (void)path;
    const auto total=LittleFS.totalBytes(),used=LittleFS.usedBytes();
    if (!total || used>total) return false;
    free=total-used;
#else
    struct statvfs info;
    if (::statvfs(path.c_str(),&info)) return false;
    free=uint64_t(info.f_bavail)*info.f_frsize;
#endif
    // Preserve room for collection generations and another policy preparation.
    return free>=192*1024+2*LittleFsLearningRepository::kMaxBlobBytes;
}
bool directorySync(const std::string& path) {
#ifdef ARDUINO
    (void)path;
    // ESP32 LittleFS commits metadata atomically within its rename operation.
    return true;
#else
    const int fd=::open(path.c_str(),O_RDONLY);
    if (fd<0) return false;
    const bool ok=::fsync(fd)==0; const bool closed=::close(fd)==0;
    return ok && closed;
#endif
}
class ReadOnlyGeneration final : public CollectionRepository {
public:
    explicit ReadOnlyGeneration(const std::string& path) : path_(path) {}
    ReadOnlyGeneration(const ReadOnlyGeneration&)=delete;
    ReadOnlyGeneration& operator=(const ReadOnlyGeneration&)=delete;
    ~ReadOnlyGeneration() override { finish(); }
    bool finish() {
        if (!file_) return true;
        auto* closing=file_; file_=nullptr;
        return std::fclose(closing)==0;
    }
    CollectionRead size(size_t& bytes) override {
        // A stream lasts one complete validation, never the next generation.
        sized_=false; position_=0;
        if (!finish()) return CollectionRead::Error;
        struct stat info;
        if (::stat(path_.c_str(),&info)) return errno==ENOENT?CollectionRead::Missing:CollectionRead::Error;
        if (!S_ISREG(info.st_mode) || info.st_size<0) return CollectionRead::Error;
        bytes=length_=static_cast<size_t>(info.st_size); sized_=true;
        return CollectionRead::Present;
    }
    bool read(size_t offset,void* data,size_t bytes) override {
        if (!sized_ || offset>length_ || bytes>length_-offset || offset>static_cast<size_t>(LONG_MAX)) return false;
        if (!file_) { file_=openFile(path_,"rb"); position_=0; }
        if (!file_) return false;
        if (position_!=offset && std::fseek(file_,static_cast<long>(offset),SEEK_SET)) return false;
        const size_t read=std::fread(data,1,bytes,file_);
        position_=offset+read;
        return read==bytes;
    }
    bool begin(uint64_t,size_t) override { return false; }
    bool write(size_t,const void*,size_t) override { return false; }
    bool readPrepared(size_t,void*,size_t) override { return false; }
    bool commit(uint64_t) override { return false; }
    void abort() override {}
private:
    std::string path_;
    std::FILE* file_=nullptr;
    size_t length_=0, position_=0;
    bool sized_=false;
};
}
LittleFsLearningRepository::LittleFsLearningRepository(const char* directory) : directory_(directory?directory:"") {
    if (directory_.empty() || directory_[0]!='/' || directory_.size()>180 || directory_.back()=='/' ||
        directory_.find("..")!=std::string::npos) directory_.clear();
}
bool LittleFsLearningRepository::read(const std::string& owner,const char* reference,std::string& record) {
    const std::string ref=reference?reference:"";
    if (directory_.empty() || !refValid(owner,ref)) return false;
    std::string envelope;
    if (!readFile(directory_+"/"+ref,envelope) || envelope.compare(0,38,"VPR1\n"+owner+"\n")) return false;
    char crc[9]; std::snprintf(crc,sizeof(crc),"%08x",checksum(envelope));
    if (ref.substr(ref.size()-9)!="."+std::string(crc)) return false;
    if (compactRefValid(ref) && compactKey(envelope)!=ref) return false;
    record=envelope.substr(38);
    return record.size()<=LearningState::MAX_ENCODED_SIZE;
}
bool LittleFsLearningRepository::prepare(const std::string& owner,const LearningState& policy,std::string& ref) {
    StorageTiming timing("policy");
    failureReason_="policy_path";
    if (directory_.empty() || !ownerValid(owner)) return false;
    if (::mkdir(directory_.c_str(),0700) && errno!=EEXIST) return false;
    failureReason_="policy_collect";
    if (!collect()) return false;
    timing.mark("collect");
    failureReason_="policy_encode";
    const std::string encoded=policy.encode();
    if (encoded.empty() || encoded.size()>LearningState::MAX_ENCODED_SIZE) return false;
    const std::string envelope="VPR1\n"+owner+"\n"+encoded;
    const std::string next=compactKey(envelope);
    if (!refValid(owner,next)) return false;
    const std::string final=directory_+"/"+next;
    struct stat info;
    if (::stat(final.c_str(),&info)==0) {
        failureReason_="policy_existing";
        std::string existing;
        if (!readFile(final,existing) || existing!=envelope) return false;
        ref=next; failureReason_="none"; return true;
    }
    if (errno!=ENOENT) return false;
    timing.mark("encode_existing");
    failureReason_="policy_space";
    if (!budget(directory_)) return false;
    timing.mark("space");
    failureReason_="policy_write";
    const std::string pending=directory_+"/.pending";
    auto* file=openFile(pending,"wb"); if (!file) return false;
    bool ok=std::fwrite(envelope.data(),1,envelope.size(),file)==envelope.size();
    if (ok) ok=std::fflush(file)==0 && ::fsync(::fileno(file))==0;
    const bool closed=std::fclose(file)==0;
    timing.mark("write_sync");
    std::string verified;
    if (!ok || !closed || !readFile(pending,verified) || verified!=envelope) return false;
    timing.mark("readback");
    failureReason_="policy_publish";
    if (::rename(pending.c_str(),final.c_str()) || !directorySync(directory_)) return false;
    timing.mark("publish");
    // Even if interrupted here, the collection still points to its old policy.
    ref=next; failureReason_="none"; return true;
}

bool LittleFsLearningRepository::collect(bool cleanup) {
    // Read-only validation of BOTH complete generations precedes any deletion.
    // A future/corrupt generation blocks cleanup, preserving all possible refs.
    const auto slash=directory_.find_last_of('/');
    const std::string parent=directory_.substr(0,slash);
    std::set<std::string> protectedRefs;
    std::unique_ptr<CollectionState> state(new (std::nothrow) CollectionState);
    if (!state) return false;
    for (const auto name:{"current.bin","previous.bin"}) {
        failureReason_=!std::strcmp(name,"current.bin")?"policy_collect_current":"policy_collect_previous";
        ReadOnlyGeneration generation(parent+"/"+name); CollectionStore reader(generation);
        const auto loaded=reader.load(*state);
        if (!generation.finish()) return false;
        if (loaded==CollectionLoad::Missing) {
            if (!std::strcmp(name,"current.bin")) return false;
            continue;
        }
        if (loaded!=CollectionLoad::Loaded) return false;
        for (const auto& slot:state->slots) if (slot.occupied && slot.learningRef[0]) protectedRefs.insert(slot.learningRef);
    }
    failureReason_="policy_collect_directory";
    DIR* directory=::opendir(directory_.c_str()); if (!directory) return false;
    size_t retainedBytes=0; bool ok=true;
    while (auto* entry=::readdir(directory)) {
        const std::string name=entry->d_name;
        if (name=="." || name=="..") continue;
        struct stat info;
        const std::string path=directory_+"/"+name;
        if (::stat(path.c_str(),&info) || !S_ISREG(info.st_mode) || info.st_size<0) { ok=false; break; }
        const bool own=compactRefValid(name) ||
            (name.size()>34 && name[0]=='L' && refValid(name.substr(1,32),name));
        if ((own && !protectedRefs.count(name)) || name==".pending") {
            if (cleanup && std::remove(path.c_str())) { ok=false; break; }
        } else {
            if (static_cast<uint64_t>(info.st_size)>kStorageBudgetBytes-retainedBytes) { ok=false; break; }
            retainedBytes+=static_cast<size_t>(info.st_size);
        }
    }
    const bool closed=::closedir(directory)==0;
    const bool valid=ok && closed && retainedBytes+2*kMaxBlobBytes<=kStorageBudgetBytes &&
        (!cleanup || directorySync(directory_));
    if (valid) failureReason_="none";
    return valid;
}
}  // namespace vpet
