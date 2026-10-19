#pragma once
#include <stdint.h>

namespace vpet { namespace option_menu {
constexpr uint8_t count=10, back=8, pause=9;
inline uint8_t slot(uint8_t index) { return index==back ? 9 : index==pause ? 8 : index%count; }
inline uint8_t at(uint8_t position) { return position==8 ? pause : position==9 ? back : position%count; }
inline uint8_t next(uint8_t index) { return at((slot(index)+1)%count); }
} }
