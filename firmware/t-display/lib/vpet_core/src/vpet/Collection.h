#pragma once

#include <stddef.h>
#include <stdint.h>
#include <cstring>
#include "vpet/AdoptedInventory.h"
#include "vpet/PetProfile.h"

namespace vpet {

struct CollectionSnapshotRecord {
    uint32_t offset = 0, length = 0, checksum = 0;
};

// Fixed-size metadata only. Bodies and learning tables never live in this array.
struct CollectionSlot {
    bool occupied = false;
    uint8_t form = 3;
    char profileRecord[104] = {};
    char lineage[33] = "builtin";
    char ancestors[4][33] = {};  // Known grandparents; unknown remains empty.
    // Immutable, adapter-owned file key, committed durably before referencing it.
    char learningRef[65] = {};
    CollectionSnapshotRecord body;
    uint64_t breedingId = 0, seed = 0;
    uint32_t cooldownMs = 0, incubationMs = 0, incubationRequiredMs = 0;
    uint16_t rulesVersion = 0;

    PetProfile profile() const {
        PetProfile value;
        if (std::memchr(profileRecord, '\0', sizeof(profileRecord))) value.decode(profileRecord);
        return value;
    }
    bool setProfile(const PetProfile& value) {
        const auto record = value.encode();
        if (!value.assigned() || record.size() >= sizeof(profileRecord)) return false;
        std::memset(profileRecord, 0, sizeof(profileRecord));
        std::memcpy(profileRecord, record.data(), record.size());
        return true;
    }
};

struct CollectionState {
    static constexpr size_t kSlots = 4;
    CollectionSlot slots[kSlots];
    uint64_t sequence = 0;
    uint8_t active = 0;
    uint8_t stock[6] = {};  // Existing item indices; unlimited food rules stay in PetState.
    AdoptedInventory adoptedStock;  // Includes the sole authoritative reward cursor.
    bool migrated = false;

    size_t count() const {
        size_t n = 0;
        for (const auto& slot : slots) if (slot.occupied) ++n;
        return n;
    }
};

static_assert(sizeof(CollectionState) <= 2048, "Collection metadata exceeds 2 KiB");

struct CollectionSwitchGuard {
    bool training = false, arena = false, journey = false, sleeping = false;
    bool pendingJournal = false, storageError = false, paused = false;
    bool blocked() const {
        return training || arena || journey || sleeping || pendingJournal || storageError || paused;
    }
};

// Eligibility, inheritance and the inherited policy file are prepared by domain adapters.
// The store commits this receipt, the already-created egg and both cooldowns together.
struct CollectionEggTransaction {
    uint64_t id = 0, seed = 0;
    uint8_t parentA = 0, parentB = 1;
    uint16_t rulesVersion = 1;
    uint32_t cooldownMs = 86400000, incubationMs = 1800000;
    char learningRef[65] = {};
};

}  // namespace vpet
