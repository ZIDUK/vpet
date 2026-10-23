#pragma once
#include <stdint.h>
#include "vpet/MenuAccess.h"

namespace vpet { namespace menu_bar {
constexpr uint8_t count = menu_access::count;
constexpr int left(uint8_t index) { return (index % count) * 240 / count; }
constexpr int width(uint8_t index) { return ((index % count) + 1) * 240 / count - left(index); }
constexpr int iconX(uint8_t index) { return left(index) + (width(index) - 20) / 2; }
constexpr const char* icons[] = {
    "/ui/icons/status.vpa", "/ui/icons/feed.vpa", "/ui/icons/training.vpa",
    "/ui/icons/explore.vpa", "/ui/icons/battle.vpa", "/ui/icons/rest.vpa",
    "/ui/icons/backpack.vpa", "/ui/icons/pedia.vpa", "/ui/icons/options.vpa"
};
inline bool availableAtStage(SpeciesId species, uint8_t index) {
    return menu_access::availableAtStage(species, index);
}

template<class Canvas> void dimLockedIcon(Canvas& canvas, SpeciesId species, uint8_t index) {
    if (availableAtStage(species,index)) return;
    for (int y=2;y<22;++y) for (int x=iconX(index);x<iconX(index)+20;++x)
        canvas.drawPixel(x,y,(canvas.readPixel(x,y)>>1)&0x7BEF);
}
} }
