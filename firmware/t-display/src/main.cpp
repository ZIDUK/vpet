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
vpet::Panels panels(display, framebuffer, assets, &staticScene);
vpet::NvsKeyValueStore stateStore("vpet_state");
vpet::NvsKeyValueStore backupStore("vpet_bak");
vpet::SettingsStore settingsStore(stateStore, &backupStore);
vpet::BleService bluetooth;
vpet::App app(renderer, panels, settingsStore, bluetooth);
vpet::AssetStatus startupAssets;
bool readyReported = false;
uint32_t lastRuntimeMs=0;
uint32_t maxLoopUs=0;

void reportRuntime(uint32_t nowMs) {
    if (!app.ready() || nowMs-lastRuntimeMs<10000) return;
    lastRuntimeMs=nowMs;
    Serial.printf("VPET_RUNTIME uptime_ms=%u heap_free=%u heap_min=%u loop_max_us=%u ble=%u\n",
                  nowMs,ESP.getFreeHeap(),ESP.getMinFreeHeap(),maxLoopUs,
                  static_cast<unsigned>(bluetooth.status()));
    maxLoopUs=0;
}

void reportHeap(const char* stage) {
    Serial.printf("VPET_HEAP stage=%s heap_free=%u heap_min=%u\n",
                  stage, ESP.getFreeHeap(), ESP.getMinFreeHeap());
}

void reportReady() {
    if (readyReported || !app.ready()) return;
    Serial.printf(
        "VPET_READY heap_free=%u heap_min=%u flash=%u fs_used=%u fs_total=%u manifest=%s\n",
        ESP.getFreeHeap(), ESP.getMinFreeHeap(), ESP.getFlashChipSize(),
        startupAssets.mounted ? LittleFS.usedBytes() : 0,
        startupAssets.mounted ? LittleFS.totalBytes() : 0,
        startupAssets.version.c_str()
    );
    readyReported = true;
}

void drawBoot(const vpet::AssetStatus& status) {
    display.fillScreen(TFT_BLACK);
    display.drawRect(3, 3, 234, 129, TFT_DARKGREY);
    display.setTextDatum(MC_DATUM);
    display.setTextColor(TFT_ORANGE, TFT_BLACK);
    display.drawString("vPET", 120, 42, 2);
    display.setTextColor(status.manifestPresent ? TFT_GREEN : TFT_RED, TFT_BLACK);
    display.drawString(status.manifestPresent ? "ASSETS OK" : "ASSETS MISSING", 120, 76, 2);
    display.setTextColor(TFT_LIGHTGREY, TFT_BLACK);
    display.drawString("NEXT: GPIO0  ACTION: GPIO35", 120, 108, 1);
}

void drawBootIntro(const vpet::AssetStatus& status) {
    constexpr uint16_t kIntroFrameMs = 110;
    constexpr uint8_t kIntroFrames = 15;
    for (uint8_t frame = 0; frame < kIntroFrames; ++frame) {
        framebuffer.fillSprite(TFT_BLACK);
        framebuffer.drawRect(3, 3, 234, 129, TFT_DARKGREY);
        framebuffer.setTextDatum(MC_DATUM);
        framebuffer.setTextColor(TFT_ORANGE, TFT_BLACK);
        framebuffer.drawString("vPET", 120, frame < 7 ? 54 : 28, 4);

        const int16_t flameX = 82 + frame * 9;
        const int16_t flameY = frame < 7 ? 43 - frame * 2 : 25;
        framebuffer.fillTriangle(flameX, flameY + 13, flameX + 7, flameY - 2,
                                 flameX + 14, flameY + 13, TFT_ORANGE);
        framebuffer.fillTriangle(flameX + 4, flameY + 12, flameX + 7, flameY + 3,
                                 flameX + 11, flameY + 12, TFT_YELLOW);
        if (frame >= 7) {
            framebuffer.drawPixel(flameX - 5, flameY + 5, TFT_YELLOW);
            framebuffer.drawPixel(flameX + 20, flameY + 1, TFT_ORANGE);
        }
        framebuffer.pushSprite(0, 0);
        delay(kIntroFrameMs);
    }

    framebuffer.fillSprite(TFT_BLACK);
    framebuffer.drawRect(3, 3, 234, 129, TFT_DARKGREY);
    framebuffer.setTextDatum(MC_DATUM);
    framebuffer.setTextColor(TFT_ORANGE, TFT_BLACK);
    framebuffer.drawString("vPET", 120, 18, 2);
    if (status.manifestPresent) {
        assets.drawFrame(framebuffer, "/animations/rookie/firemon_idle.vpa", 0, 76, 35);
        framebuffer.setTextColor(TFT_GREEN, TFT_BLACK);
        framebuffer.drawString("ASSETS OK", 120, 119, 2);
    } else {
        framebuffer.setTextColor(TFT_RED, TFT_BLACK);
        framebuffer.drawString("ASSETS MISSING", 120, 76, 2);
    }
    framebuffer.pushSprite(0, 0);
    delay(550);
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
    bluetooth.begin();
    reportHeap("before_assets");
    const vpet::AssetStatus status = assets.begin();
    reportHeap("after_assets");
    startupAssets = status;
    drawBootIntro(status);
    if (!buttons.begin()) {
        Serial.println("VPET_FATAL code=INPUT_TASK_ALLOCATION");
        display.fillScreen(TFT_BLACK);
        display.drawString("INPUT ERROR", 20, 60, 2);
        while (true) delay(1000);
    }
    reportHeap("before_app");
    app.begin(millis());
    reportHeap("after_app");
    reportReady();
}

void loop() {
    const uint32_t startedUs=micros();
    const vpet::InputEvent event = buttons.poll(millis());
    if (event != vpet::InputEvent::None) {
        Serial.printf("VPET_INPUT event=%u\n", static_cast<unsigned>(event));
    }
    app.tick(millis(), event);
    reportReady();
    const uint32_t loopUs=micros()-startedUs;
    if (loopUs>maxLoopUs) maxLoopUs=loopUs;
    reportRuntime(millis());
    delay(2);
}
