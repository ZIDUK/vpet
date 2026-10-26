#pragma once

#include <cstdio>
#include <string>
#include "vpet/CollectionStore.h"

namespace vpet {

// Uses the already-mounted ESP32 LittleFS POSIX/VFS path. Construction performs
// no IO, mounting, formatting, recovery, migration or startup registration.
// One writer, called serially by the owning loop. Do not instantiate concurrent
// writers for the same directory. External learning blobs need their own adapter.
// Max 24 KiB each for current/previous/pending (72 KiB total); begin requires a
// 192 KiB operational budget including these files. A failed preparation may
// leave previous incomplete; current remains authoritative and is never removed.
// Recovery of previous is an explicit user flow, never automatic. Atomic durable
// rename relies on the mounted LittleFS implementation; physical power-cut / heap
// validation and deployment backup protection remain integration requirements.
class LittleFsCollectionRepository final : public CollectionRepository {
public:
    static constexpr size_t kStorageBudgetBytes = 192 * 1024;
    explicit LittleFsCollectionRepository(const char* directory = "/littlefs/collection");
    ~LittleFsCollectionRepository() override;
    LittleFsCollectionRepository(const LittleFsCollectionRepository&) = delete;
    LittleFsCollectionRepository& operator=(const LittleFsCollectionRepository&) = delete;

    CollectionRead size(size_t& bytes) override;
    bool read(size_t offset, void* data, size_t bytes) override;
    bool begin(uint64_t expectedSequence, size_t bytes) override;
    bool write(size_t offset, const void* data, size_t bytes) override;
    bool readPrepared(size_t offset, void* data, size_t bytes) override;
    bool commit(uint64_t nextSequence) override;
    void abort() override;

private:
    bool syncPrepared();
    bool freeBudget() const;
    std::string directory_;
    std::FILE* prepared_ = nullptr;
    size_t preparedBytes_ = 0;
    uint64_t expectedSequence_ = 0;
    bool dirty_ = false;
};

}  // namespace vpet
