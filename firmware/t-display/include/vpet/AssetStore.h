#pragma once

#include <Arduino.h>

namespace vpet {

struct AssetStatus {
    bool mounted = false;
    bool manifestPresent = false;
    String version = "missing";
};

class AssetStore {
public:
    AssetStatus begin();
};

}  // namespace vpet
