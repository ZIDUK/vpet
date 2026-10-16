#pragma once
#include <stdint.h>

namespace vpet { namespace menu_bar {
constexpr uint8_t count = 9;
constexpr int left(uint8_t index) { return (index % count) * 240 / count; }
constexpr int width(uint8_t index) { return ((index % count) + 1) * 240 / count - left(index); }
constexpr int iconX(uint8_t index) { return left(index) + (width(index) - 20) / 2; }
constexpr const char* icons[] = {
    "/ui/icons/status.vpa", "/ui/icons/feed.vpa", "/ui/icons/training.vpa",
    "/ui/icons/explore.vpa", "/ui/icons/battle.vpa", "/ui/icons/rest.vpa",
    "/ui/icons/backpack.vpa", "/ui/icons/pedia.vpa", "/ui/icons/options.vpa"
};
} }
