#include "vpet/PracticeBattle.h"

// Compile the portable prototype on ESP32 even before wiring its UI adapter.
static_assert(sizeof(vpet::practice::Battle) < 256, "Practice state budget exceeded");
