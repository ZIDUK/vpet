#pragma once

#include <map>
#include <sstream>
#include <cstring>
#include <limits>
#include "vpet/SettingsStore.h"

namespace vpet { namespace storage {

static const char* const kSnapshotKeys[] = {
    "legacyWeight", "schema", "nutVer", "species", "hunger", "energy", "happy",
    "effort", "health", "age", "invMeat", "invEner", "invExp", "invRing",
    "invProt", "invMed", "stageAge", "cm", "call", "meals", "training", "battles",
    "wins", "losses", "weight", "nutHunRem", "nutTrainRem", "nutProtein", "dp",
    "protein", "overfed", "overfeeds", "injured", "injuries", "injuredMs", "dead", "cold",
    "dna0", "dna1", "dna2", "dna3", "evHp", "evMp", "evOff", "evDef", "evSpd",
    "evBrn", "life", "sound", "bluetooth", "techVer", "techTrain", "techBond",
    "techM0", "techM1", "techM2", "techEquip"
};

// Capture the ordinary key writer before any persistent state is touched.
class SnapshotStore final : public KeyValueStore {
public:
    explicit SnapshotStore(KeyValueStore* base = nullptr) : base_(base) {}
    std::map<std::string, int32_t> ints;
    std::map<std::string, std::string> strings;
    int32_t getInt(const char* key, int32_t fallback) override {
        const auto found = ints.find(key);
        return found != ints.end() ? found->second : base_ ? base_->getInt(key, fallback) : fallback;
    }
    std::string getString(const char* key, const char* fallback) override {
        const auto found = strings.find(key);
        return found != strings.end() ? found->second : base_ ? base_->getString(key, fallback) : fallback;
    }
    bool putInt(const char* key, int32_t value) override { ints[key] = value; return true; }
    bool putString(const char* key, const char* value) override { strings[key] = value; return true; }
private:
    KeyValueStore* base_;
};

inline bool validSnapshotValue(const char* key, int32_t value) {
    if (value < 0) return false;
    if (!strcmp(key,"schema")) return value == 3;
    if (!strcmp(key,"nutVer") || !strcmp(key,"life") || !strcmp(key,"techVer")) return value == 1;
    if (!strcmp(key,"species")) return value <= 4;
    if (!strcmp(key,"legacyWeight") || !strcmp(key,"weight")) return value >= 1 && value <= 99;
    if (!strcmp(key,"injuredMs")) return value <= 21600000;
    if (!strcmp(key,"age") || !strcmp(key,"stageAge") || !strcmp(key,"training") || !strcmp(key,"battles")) return true;
    if (!strcmp(key,"call") || !strcmp(key,"nutTrainRem")) return value <= 3;
    if (!strcmp(key,"nutHunRem")) return value <= 19;
    if (!strcmp(key,"techEquip")) return value <= 7;
    if (!strcmp(key,"nutProtein") || !strcmp(key,"overfed") || !strcmp(key,"injured") ||
        !strcmp(key,"dead") || !strcmp(key,"cold") || !strcmp(key,"sound") || !strcmp(key,"bluetooth")) return value <= 1;
    if (!strncmp(key,"ev",2)) return value <= 252;
    if (!strcmp(key,"hunger") || !strcmp(key,"energy") || !strcmp(key,"happy") ||
        !strcmp(key,"effort") || !strcmp(key,"health") || !strcmp(key,"techBond") ||
        !strncmp(key,"techM",5)) return value <= 100;
    return value <= 255;
}

inline std::string encodeSnapshot(const SnapshotStore& snapshot) {
    std::ostringstream out;
    out << "1\n";
    for (const auto key : kSnapshotKeys) {
        const auto found = snapshot.ints.find(key);
        if (found == snapshot.ints.end() || !validSnapshotValue(key, found->second)) return "";
        out << key << ' ' << found->second << '\n';
    }
    for (const auto key : {"language", "adoptBag"}) {
        const auto found = snapshot.strings.find(key);
        if (found == snapshot.strings.end() || found->second.find('\n') != std::string::npos) return "";
        out << found->second << '\n';
    }
    out << "END\n";
    return out.str();
}

inline bool decodeSnapshot(const std::string& record, SnapshotStore& snapshot) {
    if (record.size() > 3800) return false;
    std::istringstream in(record);
    std::string line, key;
    if (!std::getline(in, line) || line != "1") return false;
    SnapshotStore next;
    for (const auto expected : kSnapshotKeys) {
        if (!std::getline(in, line)) return false;
        std::istringstream field(line);
        int32_t value;
        if (!(field >> key >> value) || key != expected || !validSnapshotValue(expected, value) || field >> key) return false;
        next.ints[expected] = value;
    }
    if (!std::getline(in, line) || (line != "ES" && line != "EN")) return false;
    next.strings["language"] = line;
    AdoptedInventory stock;
    if (!std::getline(in, line) || line.empty() || !stock.decode(line)) return false;
    next.strings["adoptBag"] = line;
    if (!std::getline(in, line) || line != "END") return false;
    if (std::getline(in, line)) return false;
    snapshot = next;
    return true;
}

inline bool replaySnapshot(KeyValueStore& destination, const SnapshotStore& snapshot) {
    for (const auto key : kSnapshotKeys)
        if (destination.getInt(key, std::numeric_limits<int32_t>::min()) != snapshot.ints.at(key) &&
            !destination.putInt(key, snapshot.ints.at(key))) return false;
    for (const auto key : {"language", "adoptBag"})
        if (destination.getString(key, "") != snapshot.strings.at(key) &&
            !destination.putString(key, snapshot.strings.at(key).c_str())) return false;
    return true;
}

} }  // namespace vpet::storage
