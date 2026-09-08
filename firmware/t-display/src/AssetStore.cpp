#include "vpet/AssetStore.h"

#include <LittleFS.h>

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

}  // namespace vpet
