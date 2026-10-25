#pragma once

#include <stdint.h>
#include <algorithm>
#include <sstream>
#include <string>

namespace vpet {

enum class CombatStat : uint8_t;
enum class ExploreRoute : uint8_t { Patio = 0, Jornada = 1, Noche = 2 };

struct ExploreReward {
    ExploreRoute route = ExploreRoute::Patio;
    CombatStat stat = static_cast<CombatStat>(0);
    bool good = false;
    bool full = false;
    uint32_t elapsed = 0;
    uint8_t energy = 0;
    uint8_t ev = 0;
    uint8_t mastery = 0;
    uint8_t learning = 0;
    bool guide = false;
    bool learned = false;
};

// Header-only so host adapters can keep their existing explicit source lists.
// Calendar seconds and clock trust are supplied by the platform owner.
struct Exploration {
    bool guide = false;
    bool guidePending = false;
    uint64_t week = 0;
    uint8_t weekEv = 0;
    uint8_t weekMastery = 0;
    uint64_t clockCheckpoint = 0;
    ExploreRoute route = ExploreRoute::Patio;
    CombatStat stat = static_cast<CombatStat>(0);
    uint64_t started = 0;
    bool good = false;
    bool learning = false;
    ExploreReward receipt;

    bool away() const { return away_; }
    bool hasReceipt() const { return receipt_; }
    static uint32_t duration(ExploreRoute route) {
        return route == ExploreRoute::Patio ? 1800 :
            route == ExploreRoute::Jornada || route == ExploreRoute::Noche ? 28800 : 0;
    }

    template<class Pet>
    bool start(Pet& pet, ExploreRoute nextRoute, CombatStat nextStat, uint64_t now) {
        // Species numeric values are the persisted, stable domain contract.
        if (away_ || pet.sleep.asleep || static_cast<uint8_t>(pet.species()) >= 3 || pet.dead() ||
            !duration(nextRoute) || (nextRoute == ExploreRoute::Jornada && static_cast<uint8_t>(nextStat) >= 6)) return false;
        route = nextRoute;
        stat = route == ExploreRoute::Jornada ? nextStat : static_cast<CombatStat>(0);
        started = std::min(now, maxTime());
        good = !pet.injured() && pet.hunger() >= 50 && pet.energy() >= 50 && pet.happiness() >= 50;
        learning = !pet.practice.learned(1);
        away_ = true;
        receipt_ = false;
        receipt = ExploreReward();
        return true;
    }

    uint32_t remaining(uint64_t now) const {
        return away_ ? duration(route) - elapsedAt(now) : 0;
    }

    template<class Pet>
    ExploreReward preview(const Pet& pet, uint64_t now) const {
        ExploreReward r;
        if (!away_) return r;
        r.route = route; r.stat = stat; r.good = good;
        r.elapsed = elapsedAt(now); r.full = r.elapsed == duration(route);
        const bool reset = weekAt(now) > week;
        const int spentEv = reset ? 0 : weekEv;
        const int spentMastery = reset ? 0 : weekMastery;
        if (route == ExploreRoute::Patio) {
            const int amount = (good ? 25 : 10) * r.elapsed / duration(route);
            r.energy = static_cast<uint8_t>(std::max(0, std::min(amount, 100 - pet.energy())));
        } else if (route == ExploreRoute::Jornada) {
            r.ev = static_cast<uint8_t>(std::max(0,std::min(int(r.elapsed / 14400), std::min(8 - spentEv, int(pet.evLimit()) - int(pet.evAt(stat))))));
            r.guide = good && r.full && !(guide || guidePending);
        } else if (learning) {
            r.learning = r.full && !pet.practice.learned(1) ? 1 : 0;
            r.learned = r.learning && pet.practice.training >= 1;
        } else {
            r.mastery = static_cast<uint8_t>(std::min(int(r.elapsed / 14400), std::min(4 - spentMastery, 100 - int(pet.practice.mastery[1]))));
        }
        return r;
    }

    template<class Pet>
    bool claim(Pet& pet, uint64_t now) {
        if (!away_) return false;
        const ExploreReward r = preview(pet, now);
        const uint64_t currentWeek = weekAt(now);
        if (currentWeek > week) { week = currentWeek; weekEv = weekMastery = 0; }
        pet.setEnergy(pet.energy() + r.energy);
        if (r.ev) { pet.addEv(r.stat, r.ev); weekEv += r.ev; }
        if (r.mastery) { pet.practice.mastery[1] += r.mastery; weekMastery += r.mastery; }
        if (r.learning && pet.practice.training < 255) ++pet.practice.training;
        if (r.guide) guide = true;
        away_ = false;
        receipt_ = true;
        receipt = r;
        // Inactive trip fields have a canonical representation.
        route = ExploreRoute::Patio; stat = static_cast<CombatStat>(0);
        started = 0; good = learning = false;
        return true;
    }

    void acknowledge() { receipt_ = false; receipt = ExploreReward(); }

    // Fixed, versioned decimal fields; strict parsing never mutates on failure.
    std::string encode() const {
        std::ostringstream out;
        const uint64_t fields[] = {1, week, weekEv, weekMastery, guide, guidePending, clockCheckpoint,
            away_, static_cast<uint8_t>(route), static_cast<uint8_t>(stat), started, good, learning,
            receipt_, static_cast<uint8_t>(receipt.route), static_cast<uint8_t>(receipt.stat), receipt.good,
            receipt.full, receipt.elapsed, receipt.energy, receipt.ev, receipt.mastery, receipt.learning,
            receipt.guide, receipt.learned};
        for (size_t i = 0; i < sizeof(fields)/sizeof(fields[0]); ++i) {
            if (i) out << ',';
            out << fields[i];
        }
        return out.str();
    }

    bool decode(const std::string& record) {
        if (record.empty()) { *this = Exploration(); return true; }
        if (record.size() > 320) return false;
        uint64_t v[25] = {};
        const uint64_t limits[] = {1, maxTime()/604800+1, 8, 4, 1, 1, maxTime(),
            1, 2, 5, maxTime(), 1, 1, 1, 2, 5, 1, 1, 28800, 25, 2, 2, 1, 1, 1};
        size_t pos = 0;
        for (size_t i = 0; i < 25; ++i) {
            const size_t first = pos;
            while (pos < record.size() && record[pos] >= '0' && record[pos] <= '9') {
                const unsigned digit = record[pos++] - '0';
                if (v[i] > limits[i]/10 || (v[i] == limits[i]/10 && digit > limits[i]%10)) return false;
                v[i] = v[i]*10 + digit;
            }
            if (pos == first || (pos-first > 1 && record[first] == '0')) return false;
            if (i < 24 && (pos == record.size() || record[pos++] != ',')) return false;
        }
        if (pos != record.size() || v[0] != 1 || (v[4] && v[5]) || (v[7] && v[13])) return false;
        if (v[18] > duration(static_cast<ExploreRoute>(v[14]))) return false;
        if (!v[7]) {
            for (size_t i = 8; i <= 12; ++i) if (v[i]) return false;
        }
        if (!v[13]) {
            for (size_t i = 14; i < 25; ++i) if (v[i]) return false;
        } else {
            if (v[17] != (v[18] == duration(static_cast<ExploreRoute>(v[14])))) return false;
            if (v[14] != 1 && (v[15] || v[20] || v[23])) return false;
            if (v[14] != 0 && v[19]) return false;
            if (v[14] != 2 && (v[21] || v[22] || v[24])) return false;
            if ((v[23] && (!v[16] || !v[17])) || (v[22] && (!v[17] || v[21])) || (v[24] && !v[22])) return false;
            if (v[20] > v[18]/14400 || v[21] > v[18]/14400) return false;
            if (v[14] == 0 && v[19] > (v[16] ? 25 : 10)*v[18]/1800) return false;
        }
        Exploration next;
        next.week = v[1]; next.weekEv = v[2]; next.weekMastery = v[3];
        next.guide = v[4]; next.guidePending = v[5]; next.clockCheckpoint = v[6];
        next.away_ = v[7]; next.route = static_cast<ExploreRoute>(v[8]);
        next.stat = static_cast<CombatStat>(v[9]); next.started = v[10]; next.good = v[11]; next.learning = v[12];
        next.receipt_ = v[13]; next.receipt.route = static_cast<ExploreRoute>(v[14]);
        next.receipt.stat = static_cast<CombatStat>(v[15]); next.receipt.good = v[16]; next.receipt.full = v[17];
        next.receipt.elapsed = v[18]; next.receipt.energy = v[19]; next.receipt.ev = v[20];
        next.receipt.mastery = v[21]; next.receipt.learning = v[22]; next.receipt.guide = v[23]; next.receipt.learned = v[24];
        if (next.route != ExploreRoute::Jornada && v[9] != 0) return false;
        *this = next;
        return true;
    }

private:
    bool away_ = false;
    bool receipt_ = false;
    static uint64_t maxTime() { return UINT64_C(9007199254740991); }
    static uint64_t weekAt(uint64_t now) { return (std::min(now, maxTime()) + 259200) / 604800; }
    uint32_t elapsedAt(uint64_t now) const {
        now = std::min(now, maxTime());
        return static_cast<uint32_t>(std::min<uint64_t>(duration(route), now > started ? now-started : 0));
    }
};

}  // namespace vpet
