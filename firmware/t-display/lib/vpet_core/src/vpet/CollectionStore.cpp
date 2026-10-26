#include "vpet/CollectionStore.h"
#include "vpet/StateSnapshot.h"
#include <algorithm>
#include <limits>
#include <memory>
#include <new>

namespace vpet {
namespace {
constexpr size_t kHeaderBytes = 24, kMetadataBytes = 2048, kChunkBytes = 256;
const char* const kStockKeys[] = {"invMeat", "invEner", "invExp", "invRing", "invProt", "invMed"};

void putNumber(std::string& out, uint64_t value, size_t bytes) {
    for (size_t i = 0; i < bytes; ++i) { out.push_back(static_cast<char>(value & 255)); value >>= 8; }
}
uint64_t number(const char* data, size_t bytes) {
    uint64_t value = 0;
    for (size_t i = 0; i < bytes; ++i) value |= uint64_t(static_cast<uint8_t>(data[i])) << (8*i);
    return value;
}
uint32_t crcUpdate(uint32_t crc, const void* data, size_t bytes) {
    const auto* p = static_cast<const uint8_t*>(data);
    for (size_t i = 0; i < bytes; ++i) {
        crc ^= p[i];
        for (int bit = 0; bit < 8; ++bit) crc = (crc >> 1) ^ ((crc & 1) ? 0xedb88320U : 0);
    }
    return crc;
}
uint32_t checksum(const std::string& s) { return ~crcUpdate(~uint32_t(0), s.data(), s.size()); }

template<size_t N> bool text(const char (&value)[N]) {
    const auto* end = static_cast<const char*>(std::memchr(value, 0, N));
    return end && std::all_of(end, value+N, [](char c) { return c == 0; });
}
bool validId(const char* id) {
    const std::string value(id);
    return value.empty() || (value.size() == 32 && value != std::string(32, '0') &&
        value.find_first_not_of("0123456789abcdef") == std::string::npos);
}
template<size_t N> bool fileKey(const char (&value)[N]) {
    if (!text(value)) return false;
    const std::string key(value);
    return key.find_first_not_of("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-.") == std::string::npos &&
        key.find("..") == std::string::npos && key != ".";
}
template<size_t N> bool copyText(char (&out)[N], const char* value) {
    if (!value || std::strlen(value) >= N) return false;
    std::memset(out, 0, N); std::memcpy(out, value, std::strlen(value)); return true;
}

std::string metadata(const CollectionState& state) {
    std::string out; out.reserve(kMetadataBytes);
    putNumber(out, state.sequence, 8); putNumber(out, state.active, 1);
    putNumber(out, state.migrated, 1);
    out.append(reinterpret_cast<const char*>(state.stock), sizeof(state.stock));
    putNumber(out, state.adoptedStock.cursor, 4); putNumber(out, state.adoptedStock.rewards, 4);
    for (uint8_t i = 0; i < adopted::kCount; ++i) putNumber(out, state.adoptedStock.count(i), 1);
    for (const auto& slot : state.slots) {
        putNumber(out, slot.occupied, 1); putNumber(out, slot.form, 1);
        out.append(slot.profileRecord, sizeof(slot.profileRecord));
        out.append(slot.lineage, sizeof(slot.lineage));
        out.append(reinterpret_cast<const char*>(slot.ancestors), sizeof(slot.ancestors));
        out.append(slot.learningRef, sizeof(slot.learningRef));
        putNumber(out, slot.body.offset, 4); putNumber(out, slot.body.length, 4); putNumber(out, slot.body.checksum, 4);
        putNumber(out, slot.breedingId, 8); putNumber(out, slot.seed, 8);
        putNumber(out, slot.cooldownMs, 4); putNumber(out, slot.incubationMs, 4);
        putNumber(out, slot.incubationRequiredMs, 4); putNumber(out, slot.rulesVersion, 2);
    }
    if (out.size() > kMetadataBytes) return "";
    out.resize(kMetadataBytes, 0); return out;
}

struct Reader {
    const std::string& data;
    size_t at = 0;
    bool ok = true;
    uint64_t take(size_t bytes) {
        if (at > data.size() || bytes > data.size()-at) { ok = false; return 0; }
        const auto value = number(data.data()+at, bytes); at += bytes; return value;
    }
    void fixed(void* value, size_t bytes) {
        if (at > data.size() || bytes > data.size()-at) { ok = false; return; }
        std::memcpy(value, data.data()+at, bytes); at += bytes;
    }
};
bool decodeMetadata(const std::string& record, CollectionState& state) {
    Reader r{record}; auto& next = state;
    next.sequence = r.take(8); next.active = r.take(1);
    const auto migrated = r.take(1); if (migrated > 1) return false;
    next.migrated = migrated;
    r.fixed(next.stock, sizeof(next.stock));
    next.adoptedStock.cursor = r.take(4); next.adoptedStock.rewards = r.take(4);
    for (uint8_t i = 0; i < adopted::kCount; ++i) {
        const auto count = r.take(1);
        if (count > adopted::limit(i)) return false;
        next.adoptedStock.set(i, count);
    }
    for (auto& slot : next.slots) {
        const auto occupied = r.take(1); if (occupied > 1) return false;
        slot.occupied = occupied; slot.form = r.take(1);
        r.fixed(slot.profileRecord, sizeof(slot.profileRecord));
        r.fixed(slot.lineage, sizeof(slot.lineage));
        r.fixed(slot.ancestors, sizeof(slot.ancestors));
        r.fixed(slot.learningRef, sizeof(slot.learningRef));
        slot.body.offset = r.take(4); slot.body.length = r.take(4); slot.body.checksum = r.take(4);
        slot.breedingId = r.take(8); slot.seed = r.take(8);
        slot.cooldownMs = r.take(4); slot.incubationMs = r.take(4);
        slot.incubationRequiredMs = r.take(4); slot.rulesVersion = r.take(2);
    }
    if (!r.ok || std::any_of(record.begin()+r.at, record.end(), [](char c) { return c != 0; })) return false;
    return true;
}

bool validState(const CollectionState& state, size_t bytes) {
    if (!state.sequence || !state.migrated || !state.count() || state.active >= CollectionState::kSlots ||
        !state.slots[state.active].occupied || state.adoptedStock.cursor >= adopted::kCount) return false;
    for (auto count : state.stock) if (count > items::kStackMax) return false;
    size_t offset = kHeaderBytes + kMetadataBytes;
    for (size_t i = 0; i < CollectionState::kSlots; ++i) {
        const auto& slot = state.slots[i];
        if (!text(slot.profileRecord) || !text(slot.lineage) || !fileKey(slot.learningRef)) return false;
        if (std::strcmp(slot.lineage, "builtin") || slot.form > 4 || slot.cooldownMs > 86400000 ||
            slot.incubationRequiredMs > 1800000 || slot.incubationMs > slot.incubationRequiredMs) return false;
        for (const auto& ancestor : slot.ancestors) if (!text(ancestor) || !validId(ancestor)) return false;
        const auto profile = slot.profile();
        if (!slot.occupied) {
            if (slot.profileRecord[0] || slot.learningRef[0] || slot.body.offset || slot.body.length || slot.body.checksum ||
                slot.breedingId || slot.seed || slot.cooldownMs || slot.incubationMs || slot.incubationRequiredMs ||
                slot.rulesVersion || slot.form != 3) return false;
            for (const auto& ancestor : slot.ancestors) if (ancestor[0]) return false;
            continue;
        }
        if (!profile.assigned() || profile.encode() != slot.profileRecord || slot.body.offset != offset ||
            !slot.body.length || slot.body.length > CollectionStore::kMaxSnapshotBytes) return false;
        if (slot.breedingId ? (slot.rulesVersion != 1 || slot.incubationRequiredMs != 1800000 || profile.parentA().empty()) :
            (slot.rulesVersion || slot.seed)) return false;
        for (const auto& ancestor : slot.ancestors) if (profile.petId() == ancestor) return false;
        for (size_t j = 0; j < i; ++j) if (state.slots[j].occupied &&
            (state.slots[j].profile().petId() == profile.petId() ||
             (slot.breedingId && state.slots[j].breedingId == slot.breedingId))) return false;
        offset += slot.body.length;
    }
    return offset == bytes && bytes <= CollectionStore::kMaxRecordBytes;
}
void sharedFrom(CollectionState& state, const PetState& pet) {
    for (size_t i = 0; i < 6; ++i) state.stock[i] = pet.itemCount(i);
    state.adoptedStock = pet.adoptedStock;
}
void applyShared(const CollectionState& state, PetState& pet) {
    pet.restoreItems(state.stock[0], state.stock[1], state.stock[2], state.stock[3], state.stock[4], state.stock[5]);
    pet.adoptedStock = state.adoptedStock;
}
bool captureBody(const PetState& pet, const Settings& settings, std::string& record) {
    PetState individual = pet;
    individual.restoreItems(0, 0, 0, 0, 0, 0); individual.adoptedStock = AdoptedInventory();
    return CollectionStore::capture(individual, settings, record);
}
bool bodyMatches(const CollectionSlot& slot, const std::string& body) {
    PetState pet; Settings settings;
    if (!CollectionStore::restore(body, pet, settings) || pet.profile.encode() != slot.profileRecord ||
        static_cast<uint8_t>(pet.species()) != slot.form || pet.adoptedStock.encode() != AdoptedInventory().encode()) return false;
    for (size_t i = 0; i < 6; ++i) if (pet.itemCount(i)) return false;
    return true;
}
size_t emptySlot(const CollectionState& state) {
    for (size_t i = 0; i < CollectionState::kSlots; ++i) if (!state.slots[i].occupied) return i;
    return CollectionState::kSlots;
}
bool identityExists(const CollectionState& state, const PetProfile& profile) {
    for (const auto& slot : state.slots) if (slot.occupied && slot.profile().petId() == profile.petId()) return true;
    return false;
}
bool idle(const PetState& pet) {
    return pet.pendingAction() == Action::None && !pet.exploration.away() && !pet.sleep.asleep;
}
bool parentEligible(const PetState& pet) {
    return idle(pet) && static_cast<uint8_t>(pet.species()) <= 2 && !pet.dead() && !pet.injured() &&
        pet.health() >= 80 && pet.hunger() >= 60 && pet.energy() >= 70 && pet.happiness() >= 60;
}
}  // namespace

CollectionLoad CollectionStore::load(CollectionState& state) {
    const auto fail = [this](CollectionLoad result) { blocked_ = true; return result; };
    size_t bytes = 0; const auto present = repository_.size(bytes);
    if (present == CollectionRead::Error) return fail(CollectionLoad::Error);
    if (present == CollectionRead::Missing) { blocked_ = false; return CollectionLoad::Missing; }
    if (bytes < kHeaderBytes+kMetadataBytes || bytes > kMaxRecordBytes) return fail(CollectionLoad::Corrupt);
    char header[kHeaderBytes];
    if (!repository_.read(0, header, sizeof(header))) return fail(CollectionLoad::Error);
    if (std::memcmp(header, "VPCL", 4)) return fail(CollectionLoad::Corrupt);
    const auto version = number(header+4, 4);
    if (version > 1) return fail(CollectionLoad::Future);
    if (version != 1 || number(header+16, 4) != bytes-kHeaderBytes) return fail(CollectionLoad::Corrupt);
    uint32_t crc = crcUpdate(~uint32_t(0), header, 20);
    char chunk[kChunkBytes];
    for (size_t at = kHeaderBytes; at < bytes;) {
        const auto n = std::min(sizeof(chunk), bytes-at);
        if (!repository_.read(at, chunk, n)) return fail(CollectionLoad::Error);
        crc = crcUpdate(crc, chunk, n); at += n;
    }
    if (~crc != number(header+20, 4)) return fail(CollectionLoad::Corrupt);
    std::string encoded(kMetadataBytes, 0);
    std::unique_ptr<CollectionState> scratch(new (std::nothrow) CollectionState);
    if (!scratch) return fail(CollectionLoad::Error);
    auto& next = *scratch;
    if (!repository_.read(kHeaderBytes, &encoded[0], encoded.size())) return fail(CollectionLoad::Error);
    if (!decodeMetadata(encoded, next) || next.sequence != number(header+8, 8) || !validState(next, bytes))
        return fail(CollectionLoad::Corrupt);
    for (const auto& slot : next.slots) if (slot.occupied) {
        std::string body;
        if (!readBody(slot, body)) return fail(CollectionLoad::Error);
        if (!bodyMatches(slot, body)) return fail(CollectionLoad::Corrupt);
    }
    state = next; blocked_ = false; return CollectionLoad::Loaded;
}

bool CollectionStore::capture(const PetState& pet, const Settings& settings, std::string& record) {
    storage::SnapshotStore snapshot;
    if (!SettingsStore(snapshot).save(pet, settings)) return false;
    auto next = storage::encodeSnapshot(snapshot);
    if (next.empty() || next.size() > kMaxSnapshotBytes) return false;
    record = std::move(next); return true;
}
bool CollectionStore::restore(const std::string& record, PetState& pet, Settings& settings) {
    storage::SnapshotStore snapshot;
    if (!storage::decodeSnapshot(record, snapshot)) return false;
    // The legacy decoder clamps inventory. Require canonical adopted quantities
    // here so malformed/duplicate/unknown stock fields never migrate silently.
    AdoptedInventory adopted;
    const auto& bag = snapshot.strings.at("adoptBag");
    if (!adopted.decode(bag) || adopted.encode() != bag) return false;
    for (const auto key : kStockKeys) if (snapshot.ints.at(key) > items::kStackMax) return false;
    PetState next; Settings nextSettings;
    if (SettingsStore(snapshot).load(next, nextSettings) != LoadResult::Loaded) return false;
    // Legacy load treats zero DNA as unassigned and rolls live pets. Collection
    // snapshots already own all four bytes; zero is a valid inherited genome.
    const uint8_t dna[] = {static_cast<uint8_t>(snapshot.ints.at("dna0")),
        static_cast<uint8_t>(snapshot.ints.at("dna1")), static_cast<uint8_t>(snapshot.ints.at("dna2")),
        static_cast<uint8_t>(snapshot.ints.at("dna3"))};
    next.restoreDna(dna);
    pet = next; settings = nextSettings; return true;
}
bool CollectionStore::readBody(const CollectionSlot& slot, std::string& body) {
    if (!slot.occupied || !slot.body.length || slot.body.length > kMaxSnapshotBytes) return false;
    std::string next(slot.body.length, 0);
    if (!repository_.read(slot.body.offset, &next[0], next.size()) || checksum(next) != slot.body.checksum) return false;
    body = std::move(next); return true;
}
bool CollectionStore::current(const CollectionState& state) {
    if (blocked_) return false;
    std::unique_ptr<CollectionState> durable(new (std::nothrow) CollectionState);
    if (!durable) { blocked_ = true; return false; }
    return load(*durable) == CollectionLoad::Loaded && metadata(state) == metadata(*durable);
}
bool CollectionStore::readPet(const CollectionState& state, size_t slot, PetState& pet, Settings& settings) {
    if (slot >= CollectionState::kSlots || !state.slots[slot].occupied || !current(state)) return false;
    std::string body; PetState next; Settings nextSettings;
    if (!readBody(state.slots[slot], body)) { blocked_ = true; return false; }
    if (!restore(body, next, nextSettings)) { blocked_ = true; return false; }
    applyShared(state, next); pet = next; settings = nextSettings; return true;
}

bool CollectionStore::persist(CollectionState& state, const CollectionState& proposed,
                              const std::string* const replacements[CollectionState::kSlots]) {
    if (blocked_ || state.sequence == std::numeric_limits<uint64_t>::max()) return false;
    std::unique_ptr<CollectionState> scratch(new (std::nothrow) CollectionState(proposed));
    if (!scratch) { blocked_ = true; return false; }
    if (state.sequence) { if (!current(state)) return false; }
    else {
        // Missing load leaves its argument untouched, so this scratch serves as
        // the initial probe without another metadata-sized frame on the stack.
        if (load(*scratch) != CollectionLoad::Missing) return false;
    }
    auto& candidate = *scratch;
    candidate.sequence = state.sequence+1;
    size_t bytes = kHeaderBytes+kMetadataBytes;
    for (size_t i = 0; i < CollectionState::kSlots; ++i) if (candidate.slots[i].occupied) {
        auto& body = candidate.slots[i].body;
        if (replacements[i]) {
            if (replacements[i]->size() > kMaxSnapshotBytes || !bodyMatches(candidate.slots[i], *replacements[i])) return false;
            body.length = replacements[i]->size(); body.checksum = checksum(*replacements[i]);
        } else {
            if (!state.slots[i].occupied) return false;
            body = state.slots[i].body;
        }
        body.offset = bytes; bytes += body.length;
    }
    if (!validState(candidate, bytes)) return false;
    const auto encoded = metadata(candidate); if (encoded.empty()) return false;
    std::string header("VPCL", 4);
    putNumber(header, 1, 4); putNumber(header, candidate.sequence, 8); putNumber(header, bytes-kHeaderBytes, 4);
    uint32_t crc = crcUpdate(~uint32_t(0), header.data(), header.size());
    crc = crcUpdate(crc, encoded.data(), encoded.size());
    const auto fail = [this]() { repository_.abort(); blocked_ = true; return false; };
    if (!repository_.begin(state.sequence, bytes)) return fail();
    if (!repository_.write(kHeaderBytes, encoded.data(), encoded.size())) return fail();
    char chunk[kChunkBytes];
    for (size_t i = 0; i < CollectionState::kSlots; ++i) if (candidate.slots[i].occupied) {
        const auto& body = candidate.slots[i].body;
        for (size_t at = 0; at < body.length;) {
            const size_t n = std::min(sizeof(chunk), size_t(body.length)-at);
            if (replacements[i]) std::memcpy(chunk, replacements[i]->data()+at, n);
            else if (!repository_.read(state.slots[i].body.offset+at, chunk, n)) return fail();
            if (!repository_.write(body.offset+at, chunk, n)) return fail();
            crc = crcUpdate(crc, chunk, n); at += n;
        }
    }
    putNumber(header, ~crc, 4);
    if (!repository_.write(0, header.data(), header.size())) return fail();
    // Verify the exact proposed bytes before the adapter's durable commit point.
    char verifiedHeader[kHeaderBytes];
    if (!repository_.readPrepared(0, verifiedHeader, sizeof(verifiedHeader)) ||
        std::memcmp(verifiedHeader, header.data(), header.size())) return fail();
    uint32_t verified = crcUpdate(~uint32_t(0), verifiedHeader, 20);
    for (size_t at = kHeaderBytes; at < bytes;) {
        const auto n = std::min(sizeof(chunk), bytes-at);
        if (!repository_.readPrepared(at, chunk, n)) return fail();
        verified = crcUpdate(verified, chunk, n); at += n;
    }
    if (verified != crc || !repository_.commit(candidate.sequence)) return fail();
    state = candidate; return true;
}

bool CollectionStore::migrate(CollectionState& state, const std::string& active, const std::string* backup,
                              const PetProfile& missingActive, const PetProfile& missingBackup) {
    if (blocked_) return false;
    std::unique_ptr<CollectionState> scratch(new (std::nothrow) CollectionState);
    if (!scratch) { blocked_ = true; return false; }
    const auto result = load(*scratch);
    if (result == CollectionLoad::Loaded) { state = *scratch; return true; }
    if (result != CollectionLoad::Missing) return false;
    std::unique_ptr<PetState> individual(new (std::nothrow) PetState);
    if (!individual) { blocked_ = true; return false; }
    auto& pet = *individual;
    Settings settings;
    if (!restore(active, pet, settings)) { blocked_ = true; return false; }
    if (!pet.profile.assigned()) pet.profile = missingActive;
    if (!pet.profile.assigned()) return false;
    auto& candidate = *scratch;
    candidate.migrated = true; sharedFrom(candidate, pet);
    candidate.slots[0].occupied = true; candidate.slots[0].setProfile(pet.profile);
    candidate.slots[0].form = static_cast<uint8_t>(pet.species());
    std::string canonicalActive, bodyActive, bodyBackup;
    if (!capture(pet, settings, canonicalActive) || !captureBody(pet, settings, bodyActive)) return false;
    const std::string* replacements[CollectionState::kSlots] = {&bodyActive, nullptr, nullptr, nullptr};
    if (backup) {
        if (!restore(*backup, pet, settings)) { blocked_ = true; return false; }
        if (!pet.profile.assigned()) pet.profile = missingBackup;
        if (!pet.profile.assigned()) return false;
        std::string canonicalBackup;
        if (!capture(pet, settings, canonicalBackup)) return false;
        if (pet.profile.petId() == candidate.slots[0].profile().petId()) {
            if (canonicalActive != canonicalBackup) { blocked_ = true; return false; }
        } else {
            candidate.slots[1].occupied = true; candidate.slots[1].setProfile(pet.profile);
            candidate.slots[1].form = static_cast<uint8_t>(pet.species());
            if (!captureBody(pet, settings, bodyBackup)) return false;
            replacements[1] = &bodyBackup;
        }
    }
    // A caller's stale RAM metadata must never turn migration into an overwrite.
    std::unique_ptr<CollectionState> empty(new (std::nothrow) CollectionState);
    if (!empty) { blocked_ = true; return false; }
    if (!persist(*empty, candidate, replacements)) return false;
    state = *empty; return true;
}
bool CollectionStore::saveActive(CollectionState& state, const PetState& pet, const Settings& settings,
                                 const char* learningRef, uint32_t elapsedMs) {
    if (!current(state) || pet.profile.encode() != state.slots[state.active].profileRecord) return false;
    std::unique_ptr<CollectionState> scratch(new (std::nothrow) CollectionState(state));
    if (!scratch) { blocked_ = true; return false; }
    auto& candidate = *scratch; sharedFrom(candidate, pet);
    advanceSlots(candidate,elapsedMs);
    auto& slot = candidate.slots[state.active]; slot.form = static_cast<uint8_t>(pet.species());
    if (learningRef && (!copyText(slot.learningRef, learningRef) || !fileKey(slot.learningRef))) return false;
    std::string body; if (!captureBody(pet, settings, body)) return false;
    const std::string* replacements[CollectionState::kSlots] = {};
    replacements[state.active] = &body;
    return persist(state, candidate, replacements);
}
bool CollectionStore::activate(CollectionState& state, size_t target, PetState& pet, Settings& settings,
                               const CollectionSwitchGuard& guard, bool confirmed) {
    if (!confirmed || guard.blocked() || !idle(pet) || target >= CollectionState::kSlots ||
        !current(state) || !state.slots[target].occupied || pet.profile.encode() != state.slots[state.active].profileRecord) return false;
    if (target == state.active) return true;
    PetState next; Settings ignored;
    if (!readPet(state, target, next, ignored) || next.pendingAction()!=Action::None || next.exploration.away()) return false;
    std::unique_ptr<CollectionState> scratch(new (std::nothrow) CollectionState(state));
    if (!scratch) { blocked_ = true; return false; }
    auto& candidate = *scratch; sharedFrom(candidate, pet); applyShared(candidate, next);
    candidate.active = target;
    std::string body; if (!captureBody(pet, settings, body)) return false;
    candidate.slots[state.active].form = static_cast<uint8_t>(pet.species());
    const std::string* replacements[CollectionState::kSlots] = {};
    replacements[state.active] = &body;
    std::string targetBody;
    if (!captureBody(next,settings,targetBody)) return false;
    replacements[target]=&targetBody;
    if (!persist(state, candidate, replacements)) return false;
    pet = next; return true;
}
bool CollectionStore::addFounder(CollectionState& state, const PetState& egg, const Settings& settings, bool confirmed) {
    if (!confirmed || !current(state) || !egg.profile.assigned() || !egg.profile.parentA().empty() ||
        egg.species() != SpeciesId::Egg || !idle(egg) || identityExists(state, egg.profile)) return false;
    const auto index = emptySlot(state); if (index == CollectionState::kSlots) return false;
    std::unique_ptr<CollectionState> scratch(new (std::nothrow) CollectionState(state));
    if (!scratch) { blocked_ = true; return false; }
    auto& candidate = *scratch; auto& slot = candidate.slots[index];
    slot.occupied = true; slot.setProfile(egg.profile);
    std::string body; if (!captureBody(egg, settings, body)) return false;
    const std::string* replacements[CollectionState::kSlots] = {}; replacements[index] = &body;
    return persist(state, candidate, replacements);
}
bool CollectionStore::commitEgg(CollectionState& state, const CollectionEggTransaction& tx,
                                const PetState& egg, const Settings& settings, size_t& childSlot, bool confirmed) {
    if (!confirmed || !current(state) || !tx.id) return false;
    // Check the durable receipt before capacity, cooldown or re-evaluating parents.
    for (size_t i = 0; i < CollectionState::kSlots; ++i) if (state.slots[i].occupied && state.slots[i].breedingId == tx.id) {
        childSlot = i; return true;
    }
    const auto index = emptySlot(state);
    if (index == CollectionState::kSlots || tx.parentA >= CollectionState::kSlots || tx.parentB >= CollectionState::kSlots ||
        tx.parentA == tx.parentB || !state.slots[tx.parentA].occupied || !state.slots[tx.parentB].occupied ||
        state.slots[tx.parentA].cooldownMs || state.slots[tx.parentB].cooldownMs || tx.rulesVersion != 1 ||
        tx.cooldownMs != 86400000 || tx.incubationMs != 1800000 || !fileKey(tx.learningRef) ||
        !egg.profile.assigned() || egg.species() != SpeciesId::Egg || !idle(egg) || identityExists(state, egg.profile)) return false;
    const auto a = state.slots[tx.parentA].profile(), b = state.slots[tx.parentB].profile();
    if (egg.profile.parentA() != a.petId() || egg.profile.parentB() != b.petId() || a.sex() == b.sex() ||
        std::strcmp(state.slots[tx.parentA].lineage, state.slots[tx.parentB].lineage)) return false;
    // Pair ancestry and genetic/policy inheritance are checked by the breeding core.
    PetState parent; Settings ignored;
    if (!readPet(state, tx.parentA, parent, ignored) || !parentEligible(parent) ||
        !readPet(state, tx.parentB, parent, ignored) || !parentEligible(parent)) return false;
    std::unique_ptr<CollectionState> scratch(new (std::nothrow) CollectionState(state));
    if (!scratch) { blocked_ = true; return false; }
    auto& candidate = *scratch; auto& slot = candidate.slots[index];
    slot.occupied = true; slot.setProfile(egg.profile); slot.breedingId = tx.id; slot.seed = tx.seed;
    slot.rulesVersion = tx.rulesVersion; slot.incubationRequiredMs = tx.incubationMs;
    copyText(slot.learningRef, tx.learningRef);
    copyText(slot.ancestors[0], a.parentA().c_str()); copyText(slot.ancestors[1], a.parentB().c_str());
    copyText(slot.ancestors[2], b.parentA().c_str()); copyText(slot.ancestors[3], b.parentB().c_str());
    candidate.slots[tx.parentA].cooldownMs = candidate.slots[tx.parentB].cooldownMs = tx.cooldownMs;
    std::string body; if (!captureBody(egg, settings, body)) return false;
    const std::string* replacements[CollectionState::kSlots] = {}; replacements[index] = &body;
    if (!persist(state, candidate, replacements)) return false;
    childSlot = index; return true;
}
bool CollectionStore::advanceSlots(CollectionState& state, uint32_t elapsedMs) {
    if (!elapsedMs) return false;
    bool changed = false;
    for (auto& slot : state.slots) if (slot.occupied && slot.cooldownMs) {
        slot.cooldownMs -= std::min(slot.cooldownMs, elapsedMs); changed = true;
    }
    auto& active = state.slots[state.active];
    if (active.form == 3 && active.incubationMs < active.incubationRequiredMs) {
        active.incubationMs += std::min(active.incubationRequiredMs-active.incubationMs, elapsedMs); changed = true;
    }
    return changed;
}
bool CollectionStore::advance(CollectionState& state, uint32_t elapsedMs, bool paused) {
    if (!current(state)) return false;
    if (paused || !elapsedMs) return true;
    std::unique_ptr<CollectionState> scratch(new (std::nothrow) CollectionState(state));
    if (!scratch) { blocked_ = true; return false; }
    auto& candidate = *scratch;
    if (!advanceSlots(candidate,elapsedMs)) return true;
    const std::string* replacements[CollectionState::kSlots] = {};
    return persist(state, candidate, replacements);
}
}  // namespace vpet
