#pragma once

#include <Arduino.h>

class TFT_eSprite;

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
        TFT_eSprite& canvas,
        const char* path,
        uint16_t frame,
        int16_t x,
        int16_t y,
        bool flipHorizontal = false
    );
};

}  // namespace vpet
