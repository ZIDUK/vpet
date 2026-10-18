#pragma once
#include "vpet/Elements.h"

namespace vpet { namespace techniques {
constexpr int kCount = 5;
struct Technique {
    const char* id;
    const char* es;
    const char* en;
    int power, mp, range, cooldown, stage, training;
};
static constexpr Technique kCatalog[kCount] = {
    {"punch", "GOLPE", "PUNCH", 12, 0, 1, 0, 1, 0},
    {"flame", "LLAMA", "FLAME", 24, 8, 2, 1, 1, 2},
    {"guard", "GUARDIA", "GUARD", 0, 0, 2, 0, 1, 0},
    {"flare", "RAFAGA", "FLARE", 30, 12, 2, 1, 2, 4},
    {"inferno", "INFERNO", "INFERNO", 38, 18, 2, 2, 3, 6},
};
inline const char* icon(int i) {
    static const char* paths[] = {"/training/tech_punch.vpa", "/training/tech_flame.vpa",
        "/training/tech_guard.vpa", "/training/tech_flare.vpa", "/training/tech_inferno.vpa"};
    return i >= 0 && i < kCount ? paths[i] : "/ui/icons/back.vpa";
}
} }
