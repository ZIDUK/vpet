#pragma once

#include <stdint.h>

namespace vpet {

// Versioned, compact progress independent from the official battle counters.
struct PracticeProgress {
    uint8_t version = 1;
    uint8_t training = 0;
    uint8_t bond = 50;
    uint8_t mastery[3] = {0, 0, 0};
    uint8_t equipped = 0b101; // punch + guard; flame is learned later.

    bool flameLearned() const { return training >= 2; }
    bool learned(uint8_t technique) const { return technique < 3 && (technique != 1 || flameLearned()); }
    bool isEquipped(uint8_t technique) const { return technique < 3 && (equipped & (1u << technique)); }

    void sanitize() {
        if (bond > 100) bond = 100;
        for (uint8_t i = 0; i < 3; ++i) {
            if (mastery[i] > 100) mastery[i] = 100;
        }
        equipped &= 0b111;
        equipped &= static_cast<uint8_t>((1u << 0) | (1u << 2) | (flameLearned() ? (1u << 1) : 0));
        if (equipped == 0) equipped = 0b101;
        if (equipped == 7) equipped = 3;
    }
    bool toggle(uint8_t technique) {
        if (!learned(technique)) return false;
        const uint8_t bit = 1u << technique;
        if (equipped == bit) return false;
        if (equipped & bit) equipped &= ~bit;
        else {
            if (equipped == 3 || equipped == 5 || equipped == 6) {
                for (int i = 2; i >= 0; --i) if (equipped & (1u << i)) {
                    equipped &= ~(1u << i);
                    break;
                }
            }
            equipped |= bit;
        }
        return true;
    }
};

}  // namespace vpet
