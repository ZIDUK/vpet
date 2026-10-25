#pragma once
#include <stdint.h>

namespace vpet { namespace growth {
constexpr uint16_t kMaxStat = 320;
constexpr uint16_t kMaxBattleStat = 448;
constexpr uint8_t kAdultRanks = 3;
inline uint8_t evLimit(uint8_t rank) { return rank ? 252 * rank / kAdultRanks : 252; }
inline uint16_t statLimit(uint8_t iv, uint8_t rank) {
    return ((200U + 8U * iv) * rank * 2U + kAdultRanks) / (2U * kAdultRanks);
}
inline uint16_t statValue(uint8_t iv, uint8_t ev, uint8_t rank) {
    const uint16_t base = ((10U + 3U * iv) * (rank + 4U) * 2U + 5U) / 10U;
    const uint16_t cap = statLimit(iv, rank);
    const uint8_t limit = evLimit(rank);
    const uint8_t active = ev < limit ? ev : limit;
    return base + static_cast<uint32_t>(cap - base) * active / limit;
}
} }
