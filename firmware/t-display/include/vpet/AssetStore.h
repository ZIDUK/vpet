#pragma once

#include <Arduino.h>

class TFT_eSPI;

namespace vpet {

struct AssetStatus {
    bool mounted = false;
    bool manifestPresent = false;
    String version = "missing";
};

class AssetStore {
public:
    AssetStatus begin();
    bool drawFrame(
        TFT_eSPI& display,
        const char* path,
        uint16_t frame,
        int16_t x,
        int16_t y,
        bool flipHorizontal = false
    );
};

}  // namespace vpet
