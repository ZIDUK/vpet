#include <Arduino.h>
#include <LittleFS.h>
#include <TFT_eSPI.h>

#include "vpet/AssetStore.h"
#include "vpet/App.h"
#include "vpet/BleService.h"
#include "vpet/BoardInput.h"
#include "vpet/Panels.h"
#include "vpet/Renderer.h"
#include "vpet/NvsKeyValueStore.h"
#include "vpet/SettingsStore.h"

namespace {
TFT_eSPI display;
TFT_eSprite framebuffer(&display);
TFT_eSprite staticScene(&display);
vpet::AssetStore assets;
vpet::BoardInput buttons;
vpet::Renderer renderer(display, framebuffer, staticScene, assets);
vpet::Panels panels(display, framebuffer, assets);
vpet::NvsKeyValueStore stateStore("vpet_state");
vpet::NvsKeyValueStore backupStore("vpet_bak");
vpet::SettingsStore settingsStore(stateStore, &backupStore);
vpet::BleService bluetooth;
vpet::App app(renderer, panels, settingsStore, bluetooth);

void drawBoot(const vpet::AssetStatus& status) {
    display.fillScreen(TFT_BLACK);
    display.drawRect(3, 3, 234, 129, TFT_DARKGREY);
    display.setTextColor(TFT_ORANGE, TFT_BLACK);
    display.setTextDatum(MC_DATUM);
    display.drawString("vPET", 120, 42, 2);
    display.setTextColor(status.manifestPresent ? TFT_GREEN : TFT_RED, TFT_BLACK);
    display.drawString(status.manifestPresent ? "ASSETS OK" : "ASSETS MISSING", 120, 76, 2);
    display.setTextColor(TFT_LIGHTGREY, TFT_BLACK);
    display.drawString("NEXT: GPIO0  ACTION: GPIO35", 120, 108, 1);
}
}

void setup() {
    Serial.begin(115200);
    pinMode(TFT_BL, OUTPUT);
    digitalWrite(TFT_BL, TFT_BACKLIGHT_ON);
    display.init();
    display.setRotation(1);
    display.setSwapBytes(true);
    framebuffer.setColorDepth(16);
    if (framebuffer.createSprite(240, 135) == nullptr) {
        display.fillScreen(TFT_BLACK);
        display.setTextColor(TFT_RED, TFT_BLACK);
        display.drawString("FRAMEBUFFER ERROR", 20, 60, 2);
        Serial.println("VPET_FATAL code=FRAMEBUFFER_ALLOCATION");
        while (true) delay(1000);
    }
    framebuffer.setSwapBytes(true);
    staticScene.setColorDepth(16);
    if (staticScene.createSprite(240, 135) == nullptr) {
        display.fillScreen(TFT_BLACK);
        display.setTextColor(TFT_RED, TFT_BLACK);
        display.drawString("SCENE BUFFER ERROR", 16, 60, 2);
        Serial.println("VPET_FATAL code=SCENE_BUFFER_ALLOCATION");
        while (true) delay(1000);
    }
    staticScene.setSwapBytes(true);
    buttons.begin();
    bluetooth.begin();
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
