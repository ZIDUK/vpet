#pragma once

#include <stdint.h>
#include "vpet/TechniqueCatalog.h"

namespace vpet {

// Versioned, compact progress independent from the official battle counters.
struct PracticeProgress {
    uint8_t version = 1;
    uint8_t training = 0;
    uint8_t bond = 50;
    uint8_t mastery[techniques::kCount] = {};
    uint8_t equipped = 0b101; // punch + guard; flame is learned later.

    bool flameLearned() const { return training >= 2; }
    bool learned(uint8_t technique, int stage=1) const {
        return technique < techniques::kCount && stage >= techniques::kCatalog[technique].stage &&
            training >= techniques::kCatalog[technique].training;
    }
    bool isEquipped(uint8_t technique) const { return technique < techniques::kCount && (equipped & (1u << technique)); }

    void sanitize(int stage=1) {
        if (bond > 100) bond = 100;
        for (uint8_t i = 0; i < techniques::kCount; ++i) {
            if (mastery[i] > 100) mastery[i] = 100;
        }
        uint8_t allowed=0;
        int count=0;
        for (int i=0;i<techniques::kCount;++i)
            if (learned(i,stage) && isEquipped(i) && count++ < stage+1) allowed |= 1u<<i;
        equipped=allowed;
        if (equipped == 0) equipped = 0b101;
    }
    bool toggle(uint8_t technique, int stage=1) {
        if (!learned(technique,stage)) return false;
        const uint8_t bit = 1u << technique;
        if (equipped == bit) return false;
        if (equipped & bit) equipped &= ~bit;
        else {
            int count=0;
            for (int i=0;i<techniques::kCount;++i) if (isEquipped(i)) ++count;
            if (count >= stage+1) {
                for (int i = techniques::kCount-1; i >= 0; --i) if (equipped & (1u << i)) {
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
