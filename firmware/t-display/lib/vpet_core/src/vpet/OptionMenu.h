#pragma once
#include <stdint.h>

namespace vpet { namespace option_menu {
constexpr uint8_t count=11, back=8, pause=9, collection=10;
inline uint8_t slot(uint8_t index) { return index==back ? 10 : index==pause ? 8 : index==collection ? 9 : index%count; }
inline uint8_t at(uint8_t position) { return position==8 ? pause : position==9 ? collection : position==10 ? back : position%count; }
inline uint8_t next(uint8_t index) { return at((slot(index)+1)%count); }
} }
