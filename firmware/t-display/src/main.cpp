#include <Arduino.h>
#include <LittleFS.h>
#include <TFT_eSPI.h>

#include "vpet/AssetStore.h"
#include "vpet/App.h"
#include "vpet/BoardInput.h"
#include "vpet/Renderer.h"

namespace {
TFT_eSPI display;
vpet::AssetStore assets;
vpet::BoardInput buttons;
vpet::Renderer renderer(display, assets);
vpet::App app(renderer);

void drawBoot(const vpet::AssetStatus& status) {
    display.fillScreen(TFT_BLACK);
    display.drawRect(3, 3, 234, 129, TFT_DARKGREY);
    display.setTextColor(TFT_ORANGE, TFT_BLACK);
    display.setTextDatum(MC_DATUM);
    display.drawString("vPET", 120, 42, 2);
    display.setTextColor(status.manifestPresent ? TFT_GREEN : TFT_RED, TFT_BLACK);
    display.drawString(status.manifestPresent ? "ASSETS OK" : "ASSETS MISSING", 120, 76, 2);
    display.setTextColor(TFT_LIGHTGREY, TFT_BLACK);
    display.drawString("NEXT: GPIO35  ACTION: GPIO0", 120, 108, 1);
}
}

void setup() {
    Serial.begin(115200);
    pinMode(TFT_BL, OUTPUT);
    digitalWrite(TFT_BL, TFT_BACKLIGHT_ON);
    display.init();
    display.setRotation(1);
    buttons.begin();
    const vpet::AssetStatus status = assets.begin();
    drawBoot(status);
    Serial.printf(
        "VPET_READY heap_free=%u heap_min=%u flash=%u fs_used=%u fs_total=%u manifest=%s\n",
        ESP.getFreeHeap(),
        ESP.getMinFreeHeap(),
        ESP.getFlashChipSize(),
        status.mounted ? LittleFS.usedBytes() : 0,
        status.mounted ? LittleFS.totalBytes() : 0,
        status.version.c_str()
    );
    app.begin(millis());
}

void loop() {
    const vpet::InputEvent event = buttons.poll(millis());
    if (event != vpet::InputEvent::None) {
        Serial.printf("VPET_INPUT event=%u\n", static_cast<unsigned>(event));
    }
    app.tick(millis(), event);
    delay(2);
}
