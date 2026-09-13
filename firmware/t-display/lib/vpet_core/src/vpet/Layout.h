#pragma once

#include <math.h>
#include <stdint.h>

#include "vpet/PetState.h"

namespace vpet {

constexpr int16_t kStatusSplitX = 100;
constexpr int16_t kStatusCardY = 54;
constexpr int16_t kStatusCardRow = 27;
constexpr int16_t kStatusCardH = 24;
constexpr int16_t kEvoChip = 40;
constexpr int16_t kEvoGap = 6;
constexpr int16_t kEvoX0 = 5;
constexpr int16_t kEvoColorY = 50;
constexpr int16_t kEvoDarkY = 94;
constexpr uint8_t kInventoryWindow = 3;

inline uint8_t inventoryWindowStart(uint8_t count, uint8_t pos, uint8_t size = kInventoryWindow) {
    if (count <= size) return 0;
    uint8_t start = pos == 0 ? 0 : static_cast<uint8_t>(pos - 1);
    if (start + size > count) start = static_cast<uint8_t>(count - size);
    return start;
}
constexpr int16_t kHelixY = 56;
constexpr int16_t kHelixWidth = 36;
constexpr int16_t kHelixHeight = 74;
constexpr uint8_t kHelixRungs = 6;
constexpr float kHelixTurns = 1.f;

inline int16_t statusPetX(int16_t petSize, int16_t splitX = kStatusSplitX) {
    const int16_t x = static_cast<int16_t>((splitX - petSize) / 2);
    return x < 0 ? 0 : x;
}

inline int bagDrawY(int petY, int bagHeight, int displayHeight) {
    if (bagHeight >= displayHeight) return 0;
    if (petY + bagHeight > displayHeight) return displayHeight - bagHeight;
    return petY;
}

inline uint8_t callMenuIndex(CallReason reason) {
    switch (reason) {
        case CallReason::Hunger: return 1;
        case CallReason::Strength: return 2;
        case CallReason::Lights: return 4;
        case CallReason::None: return 255;
    }
    return 255;
}

inline bool callBlinkOn(uint32_t nowMs) {
    return (nowMs / 400U) % 2U == 0U;
}

inline uint16_t helixColor(const uint8_t dna[4], uint8_t strand) {
    if (dna == nullptr || (dna[0] | dna[1] | dna[2] | dna[3]) == 0) return 0x7BEF;
    if (strand == 0) return static_cast<uint16_t>((dna[0] << 8) | dna[1]);
    return static_cast<uint16_t>((dna[2] << 8) | dna[3]);
}

inline int helixX(uint8_t strand, uint8_t step, int width) {
    static const int8_t kPhase[2][5] = {
        {-1, 0, 1, 0, -1},
        {1, 0, -1, 0, 1},
    };
    const int mid = width / 2;
    const int amp = width / 2 - 2;
    return mid + amp * kPhase[strand & 1][step % 5];
}

inline float helixSpin(uint32_t nowMs, uint16_t periodMs = 2400) {
    if (periodMs == 0) return 0.f;
    return (static_cast<float>(nowMs % periodMs) / static_cast<float>(periodMs)) * 2.f * 3.14159265f;
}

inline float helixPose() {
    return 1.57079633f;
}

inline int helixSample(uint8_t strand, uint8_t step, uint8_t steps, int width, float spin = 0.f) {
    const float t = steps == 0 ? 0.f : static_cast<float>(step) / static_cast<float>(steps);
    const float angle = t * (kHelixTurns * 2.f * 3.14159265f) + spin;
    const float phase = (strand & 1) ? 3.14159265f : 0.f;
    const float mid = static_cast<float>(width) * 0.5f;
    const float amp = mid - 3.f;
    return static_cast<int>(lroundf(mid + amp * sinf(angle + phase)));
}

inline float helixDepth(uint8_t strand, uint8_t step, uint8_t steps, float spin = 0.f) {
    const float t = steps == 0 ? 0.f : static_cast<float>(step) / static_cast<float>(steps);
    const float angle = t * (kHelixTurns * 2.f * 3.14159265f) + spin;
    const float phase = (strand & 1) ? 3.14159265f : 0.f;
    return cosf(angle + phase);
}

}  // namespace vpet
