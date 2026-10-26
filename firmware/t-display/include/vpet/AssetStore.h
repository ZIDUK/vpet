#pragma once

#include <Arduino.h>
#include <memory>

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
    void releaseTrainingCache() { iconCache_.reset(); }
    bool drawFrame(
        TFT_eSprite& canvas,
        const char* path,
        uint16_t frame,
        int16_t x,
        int16_t y,
        bool flipHorizontal = false,
        int32_t tint = -1,
        uint8_t minLuma = 0,
        uint16_t anchorSize = 0,
        // Destination's first opaque row, or -1 when nothing is drawn.
        int16_t* visibleTop = nullptr
    );
    // Like drawFrame but renders into a square scratch sprite and pushes
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
        uint8_t minLuma = 0,
        uint16_t sourceSize = 20
    );

private:
    struct CachedIcon {
        char path[32]{};
        uint16_t colors[16 * 16]{};
        uint8_t opaque[16 * 16 / 8]{};
        uint8_t width = 0, height = 0;
        uint32_t age = 0;
    };
    // Keep all ten decoded icons while Training is active, not during breeding
    // or Home. Animated palettes cannot evict this separate cache.
    static constexpr size_t kIconCacheCount = 10;
    std::unique_ptr<CachedIcon[]> iconCache_;
    struct CachedPalette {
        char path[64]{};
        uint16_t width = 0;
        uint16_t height = 0;
        uint16_t frameCount = 0;
        uint16_t paletteCount = 0;
        uint8_t transparent = 0;
        uint32_t age = 0;
        uint16_t colors[256]{};
    };

    // Reused scratch space keeps multi-row LittleFS reads off the loop stack.
    uint8_t indexRows_[240 * 8]{};
    CachedPalette paletteCache_[8]{};
    uint32_t cacheAge_ = 0;
};

}  // namespace vpet
