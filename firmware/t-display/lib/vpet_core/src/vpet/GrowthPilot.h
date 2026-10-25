#pragma once

#include <stdint.h>

// Experimental reference only: not included by the running firmware.
namespace vpet { namespace growth_pilot {
struct Point {
    uint16_t base = 0, cap = 0, stat = 0;
    uint16_t capEv = 0, activeEv = 0, storedEv = 0;
};

inline uint16_t halfUp(uint32_t numerator, uint32_t denominator) {
    return static_cast<uint16_t>((2 * numerator + denominator) / (2 * denominator));
}

inline bool point(int iv, int ev, int rank, int ranks, Point& out) {
    out = {};
    if (ranks < 1 || ranks > 3 || rank < 1 || rank > ranks ||
        iv < 0 || iv > 15 || ev < 0 || ev > 252) return false;
    out.cap = halfUp((200 + 8 * iv) * rank, ranks);
    out.base = halfUp((10 + 3 * iv) * (rank + 4), 5);
    out.capEv = static_cast<uint16_t>(6 * ((252 * rank) / (6 * ranks)));
    out.storedEv = static_cast<uint16_t>(ev);
    out.activeEv = ev < out.capEv ? ev : out.capEv;
    out.stat = out.base + static_cast<uint32_t>(out.cap - out.base) * out.activeEv / out.capEv;
    return true;
}

struct Projection {
    Point before, after;
    uint16_t added = 0;
    uint8_t energyCost = 0;
};

inline bool projectTraining(int iv, int ev, int rank, int ranks, int requested, Projection& out) {
    out = {};
    if (requested < 1 || requested > 252 || !point(iv, ev, rank, ranks, out.before)) return false;
    const int room = ev < out.before.capEv ? out.before.capEv - ev : 0;
    out.added = requested < room ? requested : room;
    out.energyCost = out.added ? 8 : 0;
    return point(iv, ev + out.added, rank, ranks, out.after);
}
} } // namespace vpet::growth_pilot
