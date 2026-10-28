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
    "protein", "overfed", "overfeeds", "injured", "injuries", "injuredMs", "dead", "cold", "hunCritMs", "eneCritMs",
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
    if (!strcmp(key,"dna4")) return value <= 2;
    if (!strcmp(key,"schema")) return value == 3;
    if (!strcmp(key,"nutVer") || !strcmp(key,"life") || !strcmp(key,"techVer")) return value == 1;
    if (!strcmp(key,"species")) return value <= 4;
    if (!strcmp(key,"legacyWeight") || !strcmp(key,"weight")) return value >= 1 && value <= 99;
    if (!strcmp(key,"injuredMs")) return value <= 21600000;
    if (!strcmp(key,"hunCritMs") || !strcmp(key,"eneCritMs")) return value <= 43200000;
    if (!strcmp(key,"age") || !strcmp(key,"stageAge") || !strcmp(key,"training") || !strcmp(key,"battles")) return true;
    if (!strcmp(key,"call") || !strcmp(key,"nutTrainRem")) return value <= 3;
    if (!strcmp(key,"nutHunRem")) return value <= 19;
    if (!strcmp(key,"techEquip")) return value <= 31;
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
    const auto profile=snapshot.strings.find("petProfile");
    const bool profilePresent=profile!=snapshot.strings.end() && !profile->second.empty();
    out << (profilePresent ? "6\n" : "4\n");
    for (const auto key : kSnapshotKeys) {
        const auto found = snapshot.ints.find(key);
        if (found == snapshot.ints.end() || !validSnapshotValue(key, found->second)) return "";
        out << key << ' ' << found->second << '\n';
    }
    for (const auto key : {"techM3", "techM4"}) {
        const auto found = snapshot.ints.find(key);
        if (found == snapshot.ints.end() || !validSnapshotValue(key,found->second)) return "";
        out << key << ' ' << found->second << '\n';
    }
    if (profilePresent) {
        const auto locus = snapshot.ints.find("dna4");
        if (locus == snapshot.ints.end() || !validSnapshotValue("dna4", locus->second)) return "";
        out << "dna4 " << locus->second << '\n';
    }
    for (const auto key : {"language", "adoptBag", "expState", "sleepState"}) {
        const auto found = snapshot.strings.find(key);
        if (found == snapshot.strings.end() || found->second.find('\n') != std::string::npos) return "";
        out << found->second << '\n';
    }
    if (profilePresent) {
        PetProfile validated;
        if (!validated.decode(profile->second)) return "";
        out << profile->second << '\n';
    }
    out << "END\n";
    return out.str();
}

inline bool decodeSnapshot(const std::string& record, SnapshotStore& snapshot) {
    if (record.size() > 3800) return false;
    std::istringstream in(record);
    std::string line, key;
    if (!std::getline(in, line) || (line != "1" && line != "2" && line != "3" && line != "4" && line != "5" && line != "6")) return false;
    const bool profilePresent = line == "5" || line == "6";
    const bool version6 = line == "6";
    const bool sleepPresent = line == "4" || profilePresent;
    const bool explorationPresent = line != "1";
    const bool expandedTechniques = line == "3" || sleepPresent;
    SnapshotStore next;
    bool survivalPresent = version6;
    for (const auto expected : kSnapshotKeys) {
        // Old snapshots end care fields at cold. An interim v4 writer also
        // emitted the complete extension; accept both without relaxing v6.
        if (!version6 && !strcmp(expected, "hunCritMs")) {
            const auto position = in.tellg();
            if (!std::getline(in, line)) return false;
            survivalPresent = line.compare(0, 10, "hunCritMs ") == 0;
            in.clear();
            in.seekg(position);
        }
        if (!survivalPresent && (!strcmp(expected, "hunCritMs") || !strcmp(expected, "eneCritMs"))) {
            next.ints[expected] = 0;
            continue;
        }
        if (!std::getline(in, line)) return false;
        std::istringstream field(line);
        int32_t value;
        if (!(field >> key >> value) || key != expected || !validSnapshotValue(expected, value) || field >> key) return false;
        next.ints[expected] = value;
    }
    if (expandedTechniques) for (const auto expected : {"techM3", "techM4"}) {
        if (!std::getline(in,line)) return false;
        std::istringstream field(line);
        int32_t value;
        if (!(field>>key>>value) || key!=expected || !validSnapshotValue(expected,value) || field>>key) return false;
        next.ints[expected]=value;
    }
    if (version6) {
        if (!std::getline(in,line)) return false;
        std::istringstream field(line);
        int32_t value;
        if (!(field >> key >> value) || key != "dna4" || !validSnapshotValue(key.c_str(),value) || value > 2 || field >> key) return false;
        next.ints["dna4"] = value;
    }
    if (!std::getline(in, line) || (line != "ES" && line != "EN")) return false;
    next.strings["language"] = line;
    AdoptedInventory stock;
    if (!std::getline(in, line) || line.empty() || !stock.decode(line)) return false;
    next.strings["adoptBag"] = line;
    if (explorationPresent) {
        Exploration exploration;
        if (!std::getline(in, line) || line.empty() || !exploration.decode(line)) return false;
        next.strings["expState"] = line;
    }
    if (sleepPresent) {
        SleepRoutine routine;
        if (!std::getline(in,line) || line.empty() || !routine.decode(line)) return false;
        next.strings["sleepState"] = line;
    }
    if (profilePresent) {
        PetProfile profile;
        if (!std::getline(in,line) || line.empty() || !profile.decode(line)) return false;
        next.strings["petProfile"]=line;
    }
    if (!std::getline(in, line) || line != "END") return false;
    if (std::getline(in, line)) return false;
    snapshot = next;
    return true;
}

inline bool replaySnapshot(KeyValueStore& destination, const SnapshotStore& snapshot) {
    for (const auto key : kSnapshotKeys)
        if (destination.getInt(key, std::numeric_limits<int32_t>::min()) != snapshot.ints.at(key) &&
            !destination.putInt(key, snapshot.ints.at(key))) return false;
    for (const auto key : {"techM3", "techM4"}) {
        const auto found=snapshot.ints.find(key);
        if (found!=snapshot.ints.end() && destination.getInt(key,-1)!=found->second &&
            !destination.putInt(key,found->second)) return false;
    }
    const auto dna4 = snapshot.ints.find("dna4");
    if (dna4 != snapshot.ints.end() && destination.getInt("dna4", -1) != dna4->second &&
        !destination.putInt("dna4",dna4->second)) return false;
    for (const auto key : {"language", "adoptBag"})
        if (destination.getString(key, "") != snapshot.strings.at(key) &&
            !destination.putString(key, snapshot.strings.at(key).c_str())) return false;
    // V1 never owned this key: recovery must preserve the destination's trip.
    const auto exploration = snapshot.strings.find("expState");
    if (exploration != snapshot.strings.end() &&
        destination.getString("expState", "") != exploration->second &&
        !destination.putString("expState", exploration->second.c_str())) return false;
    const auto sleep = snapshot.strings.find("sleepState");
    if (sleep != snapshot.strings.end() && destination.getString("sleepState", "") != sleep->second &&
        !destination.putString("sleepState",sleep->second.c_str())) return false;
    const auto profile = snapshot.strings.find("petProfile");
    if (profile != snapshot.strings.end() && destination.getString("petProfile", "") != profile->second &&
        !destination.putString("petProfile",profile->second.c_str())) return false;
    return true;
}

} }  // namespace vpet::storage
