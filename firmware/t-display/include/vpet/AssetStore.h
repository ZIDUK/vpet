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
        bool flipHorizontal = false,
        int32_t tint = -1,
        uint8_t minLuma = 0
    );
    // Like drawFrame but renders into a 20x20 scratch sprite and pushes
    // the sprite scaled to (w, h) at (x, y). Used by Status 4/4 stat
    // rows where the card slot is 12 px but the asset is 20 px. The
    // scratch sprite is filled with the destination canvas pixel at
    // (x, y) so the scaled icon blends with the card chip background.
    bool drawFrameScaled(
        TFT_eSprite& canvas,
        const char* path,
        uint16_t frame,
        int16_t x, int16_t y,
        int16_t w, int16_t h,
        bool flipHorizontal = false,
        int32_t tint = -1,
        uint8_t minLuma = 0
    );

private:
    // Reused scratch space keeps multi-row LittleFS reads off the loop stack.
    uint8_t indexRows_[240 * 8]{};
};

}  // namespace vpet
