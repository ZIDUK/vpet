#include "vpet/AssetStore.h"

#include <LittleFS.h>
#include <TFT_eSPI.h>

namespace vpet {

AssetStatus AssetStore::begin() {
    AssetStatus status;
    status.mounted = LittleFS.begin(false);
    if (!status.mounted) {
        return status;
    }
    File manifest = LittleFS.open("/manifest.json", "r");
    status.manifestPresent = static_cast<bool>(manifest);
    if (!manifest) {
        return status;
    }
    String contents = manifest.readString();
    manifest.close();
    int format = contents.indexOf("\"format\": 1");
    status.version = format >= 0 ? "1" : "invalid";
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
    TFT_eSPI& display,
    const char* path,
    uint16_t frame,
    int16_t x,
    int16_t y,
    bool flipHorizontal
) {
    File file = LittleFS.open(path, "r");
    if (!file) {
        return false;
    }
    char magic[4];
    if (file.readBytes(magic, sizeof(magic)) != sizeof(magic) ||
        magic[0] != 'V' || magic[1] != 'P' || magic[2] != 'A' || magic[3] != '1') {
        file.close();
        return false;
    }
    const uint16_t width = read16(file);
    const uint16_t height = read16(file);
    const uint16_t frameCount = read16(file);
    const uint16_t paletteCount = read16(file);
    const uint8_t transparent = file.read();
    if (width == 0 || width > 240 || height == 0 || height > 135 ||
        frameCount == 0 || paletteCount == 0 || paletteCount > 256) {
        file.close();
        return false;
    }
    uint16_t palette[256];
    for (uint16_t index = 0; index < paletteCount; ++index) {
        palette[index] = read16(file);
    }
    frame %= frameCount;
    file.seek(13 + paletteCount * 2 + frame * 4);
    const uint32_t frameOffset = read32(file);
    if (!file.seek(frameOffset)) {
        file.close();
        return false;
    }

    uint8_t indices[240];
    uint16_t colors[240];
    for (uint16_t row = 0; row < height; ++row) {
        if (file.read(indices, width) != width) {
            file.close();
            return false;
        }
        uint16_t column = 0;
        while (column < width) {
            const uint16_t source = flipHorizontal ? width - column - 1 : column;
            if (indices[source] == transparent) {
                ++column;
                continue;
            }
            const uint16_t runStart = column;
            uint16_t runLength = 0;
            while (column < width) {
                const uint16_t runSource = flipHorizontal ? width - column - 1 : column;
                const uint8_t paletteIndex = indices[runSource];
                if (paletteIndex == transparent) {
                    break;
                }
                colors[runLength++] = palette[paletteIndex];
                ++column;
            }
            display.pushImage(x + runStart, y + row, runLength, 1, colors);
        }
    }
    file.close();
    return true;
}

}  // namespace vpet
