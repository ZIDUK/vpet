#include "vpet/LittleFsCollectionRepository.h"
#include <algorithm>
#include <cerrno>
#include <cstring>
#include <limits>
#include <sys/stat.h>
#include <unistd.h>
#ifdef ARDUINO
#include <LittleFS.h>
#else
#include <sys/statvfs.h>
#endif

namespace vpet {
namespace {
constexpr size_t kHeaderBytes = 24, kChunkBytes = 256;
uint64_t number(const uint8_t* data, size_t n) {
    uint64_t value = 0;
    for (size_t i = 0; i < n; ++i) value |= uint64_t(data[i]) << (i*8);
    return value;
}
uint32_t crcUpdate(uint32_t crc, const uint8_t* data, size_t n) {
    for (size_t i = 0; i < n; ++i) {
        crc ^= data[i];
        for (int bit = 0; bit < 8; ++bit) crc = (crc >> 1) ^ ((crc & 1) ? 0xedb88320U : 0);
    }
    return crc;
}
CollectionRead probe(const std::string& path, size_t& bytes) {
    struct stat info;
    if (::stat(path.c_str(), &info)) return errno == ENOENT ? CollectionRead::Missing : CollectionRead::Error;
    if (!S_ISREG(info.st_mode) || info.st_size < 0) return CollectionRead::Error;
    bytes = static_cast<size_t>(info.st_size); return CollectionRead::Present;
}
std::FILE* openFile(const std::string& path, const char* mode) {
    auto* file = std::fopen(path.c_str(), mode);
    // Avoid libc's per-stream block buffers on the small ESP32 heap.
    if (file) std::setvbuf(file, nullptr, _IONBF, 0);
    return file;
}
bool syncFile(std::FILE* file) {
    return std::fflush(file) == 0 && ::fsync(::fileno(file)) == 0;
}
bool readRange(const std::string& path, size_t offset, void* data, size_t bytes) {
    size_t total = 0;
    if (probe(path, total) != CollectionRead::Present || offset > total || bytes > total-offset ||
        offset > static_cast<size_t>(std::numeric_limits<long>::max())) return false;
    auto* file = openFile(path, "rb"); if (!file) return false;
    const bool ok = std::fseek(file, static_cast<long>(offset), SEEK_SET) == 0 &&
        std::fread(data, 1, bytes, file) == bytes;
    const bool closed = std::fclose(file) == 0; return ok && closed;
}
// This envelope check is deliberately streaming; core validates every body and
// metadata field separately. A future version never becomes an empty repository.
bool generation(const std::string& path, uint64_t& sequence, size_t& bytes) {
    if (probe(path, bytes) != CollectionRead::Present || bytes < kHeaderBytes+2048 ||
        bytes > CollectionStore::kMaxRecordBytes) return false;
    auto* file = openFile(path, "rb"); if (!file) return false;
    uint8_t header[kHeaderBytes], chunk[kChunkBytes];
    bool ok = std::fread(header, 1, sizeof(header), file) == sizeof(header);
    if (ok) ok = !std::memcmp(header, "VPCL", 4) && number(header+4, 4) == 1 &&
        number(header+16, 4) == bytes-kHeaderBytes && number(header+8, 8) != 0;
    uint32_t crc = ok ? crcUpdate(~uint32_t(0), header, 20) : 0;
    for (size_t at = kHeaderBytes; ok && at < bytes;) {
        const auto n = std::min(sizeof(chunk), bytes-at);
        ok = std::fread(chunk, 1, n, file) == n;
        if (ok) crc = crcUpdate(crc, chunk, n);
        at += n;
    }
    if (ok) ok = ~crc == number(header+20, 4);
    const bool closed = std::fclose(file) == 0;
    if (ok && closed) sequence = number(header+8, 8);
    return ok && closed;
}
bool copyGeneration(const std::string& source, const std::string& destination, size_t bytes, uint64_t sequence) {
    auto* input = openFile(source, "rb"); if (!input) return false;
    auto* output = openFile(destination, "wb");
    if (!output) { std::fclose(input); return false; }
    uint8_t chunk[kChunkBytes]; bool ok = true;
    for (size_t at = 0; ok && at < bytes;) {
        const auto n = std::min(sizeof(chunk), bytes-at);
        ok = std::fread(chunk, 1, n, input) == n && std::fwrite(chunk, 1, n, output) == n;
        at += n;
    }
    if (ok) ok = syncFile(output);
    const bool inputClosed = std::fclose(input) == 0, outputClosed = std::fclose(output) == 0;
    uint64_t verified = 0; size_t length = 0;
    return ok && inputClosed && outputClosed && generation(destination, verified, length) &&
        verified == sequence && length == bytes;
}
bool directoryExists(const std::string& path) {
    struct stat info; return ::stat(path.c_str(), &info) == 0 && S_ISDIR(info.st_mode);
}
}  // namespace

LittleFsCollectionRepository::LittleFsCollectionRepository(const char* path) : directory_(path ? path : "") {
    if (directory_.empty() || directory_[0] != '/' || directory_.size() > 180 || directory_.back() == '/' ||
        directory_.find("/../") != std::string::npos || directory_.find("/./") != std::string::npos ||
        directory_.find("..") != std::string::npos) directory_.clear();
}
LittleFsCollectionRepository::~LittleFsCollectionRepository() { abort(); }

CollectionRead LittleFsCollectionRepository::size(size_t& bytes) {
    if (directory_.empty()) return CollectionRead::Error;
    const auto result = probe(directory_+"/current.bin", bytes);
    if (result != CollectionRead::Missing) return result;
    size_t previous = 0;
    if (probe(directory_+"/previous.bin", previous) != CollectionRead::Missing) return CollectionRead::Error;
    const auto slash = directory_.find_last_of('/');
    if (!directoryExists(directory_.substr(0, slash ? slash : 1))) return CollectionRead::Error;
    bytes = 0; return CollectionRead::Missing;
}
bool LittleFsCollectionRepository::read(size_t offset, void* data, size_t bytes) {
    return !directory_.empty() && readRange(directory_+"/current.bin", offset, data, bytes);
}
bool LittleFsCollectionRepository::freeBudget() const {
    size_t occupied = 0;
    for (const auto name : {"current.bin", "previous.bin", "pending.bin"}) {
        size_t bytes = 0; const auto result = probe(directory_+"/"+name, bytes);
        if (result == CollectionRead::Error || bytes > CollectionStore::kMaxRecordBytes) return false;
        occupied += bytes;
    }
    uint64_t available = 0;
#ifdef ARDUINO
    const auto total = LittleFS.totalBytes(), used = LittleFS.usedBytes();
    if (!total || used > total) return false;
    available = total-used;
#else
    struct statvfs info;
    if (::statvfs(directory_.c_str(), &info)) return false;
    available = uint64_t(info.f_bavail)*info.f_frsize;
#endif
    return available+occupied >= kStorageBudgetBytes;
}
bool LittleFsCollectionRepository::begin(uint64_t expectedSequence, size_t bytes) {
    if (prepared_ || directory_.empty() || bytes < kHeaderBytes+2048 || bytes > CollectionStore::kMaxRecordBytes) return false;
    size_t currentBytes = 0; const auto result = size(currentBytes); uint64_t currentSequence = 0;
    if (result == CollectionRead::Error || (result == CollectionRead::Missing && expectedSequence) ||
        (result == CollectionRead::Present && (!generation(directory_+"/current.bin", currentSequence, currentBytes) ||
         currentSequence != expectedSequence))) return false;
    if (::mkdir(directory_.c_str(), 0700) && (errno != EEXIST || !directoryExists(directory_))) return false;
    if (!freeBudget()) return false;
    prepared_ = openFile(directory_+"/pending.bin", "w+b"); if (!prepared_) return false;
    preparedBytes_ = bytes; expectedSequence_ = expectedSequence; dirty_ = true;
    if (std::fseek(prepared_, static_cast<long>(bytes-1), SEEK_SET) || std::fputc(0, prepared_) == EOF || !syncPrepared()) {
        abort(); return false;
    }
    return true;
}
bool LittleFsCollectionRepository::write(size_t offset, const void* data, size_t bytes) {
    if (!prepared_ || offset > preparedBytes_ || bytes > preparedBytes_-offset) return false;
    dirty_ = true;
    return std::fseek(prepared_, static_cast<long>(offset), SEEK_SET) == 0 && std::fwrite(data, 1, bytes, prepared_) == bytes;
}
bool LittleFsCollectionRepository::syncPrepared() {
    if (!prepared_ || (dirty_ && !syncFile(prepared_))) return false;
    dirty_ = false; return true;
}
bool LittleFsCollectionRepository::readPrepared(size_t offset, void* data, size_t bytes) {
    if (!prepared_ || offset > preparedBytes_ || bytes > preparedBytes_-offset || !syncPrepared()) return false;
    return std::fseek(prepared_, static_cast<long>(offset), SEEK_SET) == 0 && std::fread(data, 1, bytes, prepared_) == bytes;
}
bool LittleFsCollectionRepository::commit(uint64_t nextSequence) {
    if (!prepared_ || expectedSequence_ == std::numeric_limits<uint64_t>::max() ||
        nextSequence != expectedSequence_+1 || !syncPrepared()) return false;
    const bool closed = std::fclose(prepared_) == 0; prepared_ = nullptr;
    if (!closed) return false;
    uint64_t sequence = 0; size_t bytes = 0;
    if (!generation(directory_+"/pending.bin", sequence, bytes) || sequence != nextSequence || bytes != preparedBytes_) return false;
    size_t currentBytes = 0; const auto result = size(currentBytes);
    if (expectedSequence_) {
        if (result != CollectionRead::Present || !generation(directory_+"/current.bin", sequence, currentBytes) ||
            sequence != expectedSequence_ || !copyGeneration(directory_+"/current.bin", directory_+"/previous.bin", currentBytes, sequence)) return false;
    } else if (result != CollectionRead::Missing) return false;
    // LittleFS's atomic rename is the sole visibility point. In particular,
    // never remove current first, and never return false after a successful rename.
    if (::rename((directory_+"/pending.bin").c_str(), (directory_+"/current.bin").c_str())) return false;
    preparedBytes_ = 0; expectedSequence_ = 0; dirty_ = false; return true;
}
void LittleFsCollectionRepository::abort() {
    if (prepared_) { std::fclose(prepared_); prepared_ = nullptr; }
    // Only this object's staging attempt is disposable. Construction/read never
    // cleans or recovers files, and neither durable generation is deleted here.
    if (preparedBytes_ && !directory_.empty()) std::remove((directory_+"/pending.bin").c_str());
    preparedBytes_ = 0; expectedSequence_ = 0; dirty_ = false;
}
}  // namespace vpet
