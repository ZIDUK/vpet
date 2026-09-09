#pragma once

#include <TFT_eSPI.h>

#include "vpet/AssetStore.h"
#include "vpet/Navigation.h"
#include "vpet/NetworkService.h"
#include "vpet/PasswordEditor.h"
#include "vpet/PetState.h"

namespace vpet {

class Panels {
public:
    Panels(TFT_eSPI& display, TFT_eSprite& canvas, AssetStore& assets);
    void draw(
        const Navigation& navigation,
        const PetState& pet,
        const NetworkService& network,
        const PasswordEditor& password,
        const char* selectedSsid,
        const int* dateTime,
        bool editingDate,
        uint8_t dateField
    );

private:
    void drawChrome(uint8_t selected, const char* title);
    void drawStatus(const PetState& pet);
    void drawInventory(uint8_t selected);
    void drawEvolution(const Navigation& navigation, bool detail);
    void drawOptions(uint8_t selected, ConnectResult networkStatus);
    void drawWifi(const Navigation& navigation, const NetworkService& network);
    void drawPassword(const PasswordEditor& password, const char* selectedSsid);
    void drawDateTime(const int* values, bool editingDate, uint8_t field);
    void drawLabel(const char* text, int16_t x, int16_t y, int16_t width, uint8_t font = 1);

    TFT_eSPI& output_;
    TFT_eSprite& display_;
    AssetStore& assets_;
};

}  // namespace vpet
