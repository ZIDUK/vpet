#include "vpet/AssetStore.h"

#include <LittleFS.h>
#include <TFT_eSPI.h>

namespace vpet {

AssetStatus AssetStore::begin() {
    AssetStatus status;
    status.mounted = LittleFS.begin(false, "/littlefs", 10, "littlefs");
    if (!status.mounted) {
        return status;
    }
    File manifest = LittleFS.open("/manifest.json", "r");
    status.manifestPresent = static_cast<bool>(manifest);
    if (!manifest) {
        return status;
    }
    // Keep the generated-manifest check streaming: String growth can briefly
    // hold two large buffers while both display framebuffers are allocated.
    status.version = manifest.find("\"format\": 1") ? "1" : "invalid";
    manifest.close();
    return status;
}

namespace {
uint16_t read16(File& file) {
    const uint16_t low = file.read();
    return low | (static_cast<uint16_t>(file.read()) << 8);
}

uint32_t read32(File& file) {
    uint32_t value = 0;
    for (uint8_t shift = 0; shift < 32; shift += 8) {
        value |= static_cast<uint32_t>(file.read()) << shift;
    }
    return value;
}
}

bool AssetStore::drawFrame(
    TFT_eSprite& canvas,
    const char* path,
    uint16_t frame,
    int16_t x,
    int16_t y,
    bool flipHorizontal,
    int32_t tint,
    uint8_t minLuma
) {
    File file = LittleFS.open(path, "r");
    if (!file) {
        return false;
    }
    CachedPalette* cached = nullptr;
    for (auto& entry : paletteCache_) {
        if (entry.path[0] && strcmp(entry.path, path) == 0) {
            cached = &entry;
            break;
        }
    }
    if (!cached) {
        char magic[4];
        if (file.readBytes(magic, sizeof(magic)) != sizeof(magic) ||
            magic[0] != 'V' || magic[1] != 'P' || magic[2] != 'A' || magic[3] != '1') {
            file.close();
            return false;
        }
        uint16_t width = read16(file);
        uint16_t height = read16(file);
        uint16_t frameCount = read16(file);
        uint16_t paletteCount = read16(file);
        uint8_t transparent = file.read();
        if (width == 0 || width > 240 || height == 0 || height > 135 ||
            frameCount == 0 || paletteCount == 0 || paletteCount > 256) {
            file.close();
            return false;
        }
        CachedPalette* target = &paletteCache_[0];
        for (auto& entry : paletteCache_) {
            if (!entry.path[0]) {
                target = &entry;
                break;
            }
            if (target->path[0] && entry.age < target->age) target = &entry;
        }
        target->width = width;
        target->height = height;
        target->frameCount = frameCount;
        target->paletteCount = paletteCount;
        target->transparent = transparent;
        // ESP32 is little endian, matching the VPA palette.
        const size_t paletteBytes = paletteCount * sizeof(uint16_t);
        if (file.read(reinterpret_cast<uint8_t*>(target->colors), paletteBytes) != paletteBytes) {
            target->path[0] = '\0';
            file.close();
            return false;
        }
        strncpy(target->path, path, sizeof(target->path) - 1);
        target->path[sizeof(target->path) - 1] = '\0';
        cached = target;
    }
    cached->age = ++cacheAge_;
    const uint16_t width = cached->width;
    const uint16_t height = cached->height;
    const uint16_t frameCount = cached->frameCount;
    const uint16_t paletteCount = cached->paletteCount;
    const uint8_t transparent = cached->transparent;
    const uint16_t* palette = cached->colors;
    frame %= frameCount;
    if (!file.seek(13 + paletteCount * 2 + frame * 4) || file.available() < 4) {
        file.close();
        return false;
    }
    const uint32_t frameOffset = read32(file);
    if (!file.seek(frameOffset)) {
        file.close();
        return false;
    }

    uint16_t colors[240];
    constexpr uint16_t rowsPerRead = sizeof(indexRows_) / 240;
    for (uint16_t firstRow = 0; firstRow < height; firstRow += rowsPerRead) {
        const uint16_t rowCount = (height - firstRow < rowsPerRead)
            ? height - firstRow : rowsPerRead;
        const size_t bytesToRead = static_cast<size_t>(rowCount) * width;
        if (file.read(indexRows_, bytesToRead) != bytesToRead) {
            file.close();
            return false;
        }
        for (uint16_t row = 0; row < rowCount; ++row) {
            const uint8_t* indices = indexRows_ + static_cast<size_t>(row) * width;
            uint16_t column = 0;
            while (column < width) {
                const uint16_t source = flipHorizontal ? width - column - 1 : column;
                const uint8_t paletteIndex = indices[source];
                if (paletteIndex == transparent) {
                    ++column;
                    continue;
                }
                if (minLuma > 0) {
                    const uint16_t color = tint >= 0 ? static_cast<uint16_t>(tint) : palette[paletteIndex];
                    const uint8_t red = (color >> 11) & 0x1F;
                    const uint8_t green = (color >> 5) & 0x3F;
                    const uint8_t blue = color & 0x1F;
                    if ((red * 2 + green + blue) * 255 / 156 < minLuma) {
                        ++column;
                        continue;
                    }
                }
                const uint16_t runStart = column;
                uint16_t runLength = 0;
                while (column < width) {
                    const uint16_t runSource = flipHorizontal ? width - column - 1 : column;
                    const uint8_t runIndex = indices[runSource];
                    if (runIndex == transparent) break;
                    const uint16_t color = tint >= 0 ? static_cast<uint16_t>(tint) : palette[runIndex];
                    if (minLuma > 0) {
                        const uint8_t red = (color >> 11) & 0x1F;
                        const uint8_t green = (color >> 5) & 0x3F;
                        const uint8_t blue = color & 0x1F;
                        if ((red * 2 + green + blue) * 255 / 156 < minLuma) break;
                    }
                    colors[runLength++] = color;
                    ++column;
                }
                canvas.pushImage(x + runStart, y + firstRow + row, runLength, 1, colors);
            }
        }
    }
    file.close();
    return true;
}

bool AssetStore::drawFrameScaled(
    TFT_eSprite& canvas,
    const char* path,
    uint16_t frame,
    int16_t x, int16_t y,
    int16_t w, int16_t h,
    bool flipHorizontal,
    int32_t tint,
    uint8_t minLuma
) {
    if (w <= 0 || h <= 0 || w > 240 || h > 240 ||
        static_cast<int32_t>(w) * h > 240 * 240) {
        return false;
    }
    // 20 px is the native icon size; if the caller asks for the same
    // size we can skip the scratch sprite and scaling.
    if (w == 20 && h == 20) {
        return drawFrame(canvas, path, frame, x, y, flipHorizontal, tint, minLuma);
    }
    // Sample the destination pixel at (x, y) to use as the sprite
    // background. This makes the scaled icon blend with whatever is
    // already on the canvas (typically the card chip color).
    const uint16_t bg = canvas.readPixel(x, y);
    TFT_eSprite tmp(&canvas);
    tmp.setColorDepth(16);
    if (!tmp.createSprite(20, 20)) {
        return false;
    }
    tmp.fillSprite(bg);
    if (!drawFrame(tmp, path, frame, 0, 0, flipHorizontal, tint, minLuma)) {
        tmp.deleteSprite();
        return false;
    }
    // Read the rendered icon into a 20x20 RGB565 buffer, then scale
    // it with nearest-neighbor sampling into the destination size.
    // This TFT_eSPI build does not expose a scaled pushSprite, so we
    // do the scaling ourselves before pushImage.
    uint16_t src[20 * 20];
    for (uint16_t row = 0; row < 20; ++row) {
        for (uint16_t col = 0; col < 20; ++col) {
            src[row * 20 + col] = tmp.readPixel(col, row);
        }
    }
    tmp.deleteSprite();
    uint16_t rowBuffer[240];
    for (int16_t dy = 0; dy < h; ++dy) {
        const int16_t sy = static_cast<int16_t>(static_cast<int32_t>(dy) * 20 / h);
        for (int16_t dx = 0; dx < w; ++dx) {
            const int16_t sx = static_cast<int16_t>(static_cast<int32_t>(dx) * 20 / w);
            rowBuffer[dx] = src[sy * 20 + sx];
        }
        canvas.pushImage(x, y + dy, w, 1, rowBuffer);
    }
    return true;
}

}  // namespace vpet
