#pragma once
#include "vpet/PetState.h"
#include "vpet/Input.h"

namespace vpet {

class ExplorationClock {
public:
    static constexpr uint64_t kEarliest = 1704067200ULL;
    void begin(uint64_t now, uint64_t checkpoint) { trusted_ = now >= kEarliest && now >= checkpoint; }
    bool trusted(uint64_t now) const { return trusted_ && now >= kEarliest; }
    void adjusted(uint64_t now) { trusted_ = now >= kEarliest; }
private:
    bool trusted_ = false;
};

struct ExplorationSession {
    enum class Page : uint8_t { Routes, Stats, Confirm, Trip, Recall, Receipt, Clock };
    enum class Operation : uint8_t { None, Start, Claim, Acknowledge, SetClock, Close };
    Page page = Page::Routes;
    uint8_t cursor = 0;
    ExploreRoute route = ExploreRoute::Patio;
    CombatStat stat = CombatStat::Off;
    bool saveFailed = false;

    static bool eligible(const PetState& p) {
        return p.species() != SpeciesId::Egg && p.species() != SpeciesId::Baby && !p.dead();
    }
    void open(const PetState& p, bool clockReady) {
        page = p.exploration.away() && !clockReady ? Page::Clock : p.exploration.away() ? Page::Trip :
            p.exploration.hasReceipt() ? Page::Receipt : Page::Routes;
        cursor = 0;
        saveFailed = false;
    }
    uint8_t count(const PetState& p) const {
        if (!eligible(p)) return 1;
        return page == Page::Routes ? 4 : page == Page::Stats ? 7 :
            page == Page::Receipt ? 1 : 2;
    }
    Operation input(const PetState& p, InputEvent event, uint64_t now) {
        if (cursor >= count(p)) cursor = 0;
        if (event == InputEvent::Next) { cursor = (cursor + 1) % count(p); saveFailed = false; }
        if (event == InputEvent::Back) {
            if (page == Page::Stats || page == Page::Confirm) { page = Page::Routes; cursor = static_cast<uint8_t>(route); }
            else if (page == Page::Recall) { page = Page::Trip; cursor = 0; }
            else return Operation::Close;
        }
        if (event != InputEvent::Action) return Operation::None;
        if (!eligible(p)) return Operation::Close;
        if (page == Page::Clock) return cursor ? Operation::Close : Operation::SetClock;
        if (page == Page::Routes) {
            if (cursor == 3) return Operation::Close;
            route = static_cast<ExploreRoute>(cursor);
            page = route == ExploreRoute::Jornada ? Page::Stats : Page::Confirm;
            cursor = 0;
        } else if (page == Page::Stats) {
            if (cursor == 6) { page = Page::Routes; cursor = 1; }
            else { stat = static_cast<CombatStat>(cursor); page = Page::Confirm; cursor = 0; }
        } else if (page == Page::Confirm) {
            if (!cursor) return Operation::Start;
            page = Page::Routes; cursor = static_cast<uint8_t>(route);
        } else if (page == Page::Trip) {
            if (p.exploration.remaining(now) == 0) return cursor ? Operation::Close : Operation::Claim;
            if (!cursor) return Operation::Close;
            page = Page::Recall; cursor = 0;
        } else if (page == Page::Recall) {
            if (cursor) return Operation::Claim;
            page = Page::Trip; cursor = 0;
        } else if (page == Page::Receipt) return Operation::Acknowledge;
        return Operation::None;
    }
};
}
