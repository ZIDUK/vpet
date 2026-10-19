#pragma once

#include <TFT_eSPI.h>

#include "vpet/AssetStore.h"
#include "vpet/BleService.h"
#include "vpet/DateTimeMenu.h"
#include "vpet/Navigation.h"
#include "vpet/PetState.h"
#include "vpet/PracticeSession.h"
#include "vpet/TrainingSession.h"
#include "vpet/ExplorationSession.h"

namespace vpet {

class Panels {
public:
    Panels(TFT_eSPI& display, TFT_eSprite& canvas, AssetStore& assets, TFT_eSprite* scene = nullptr);
    void draw(
        const Navigation& navigation,
        const PetState& pet,
        BleStatus bluetoothStatus,
        const DateTimeMenu& dateMenu,
        const char* language,
        bool soundEnabled,
        bool hasBackup = false,
        SpeciesId backupSpecies = SpeciesId::Egg,
        uint32_t nowMs = 0
    );
    void invalidate();
    void drawStorageError(const char* language);
    void drawPractice(const PracticeSession& session, const PetState& pet, uint32_t nowMs, const char* language = "ES");
    void drawTraining(const TrainingSession& session, const PetState& pet, uint32_t nowMs, const char* language);
    void drawExploration(const ExplorationSession& session, const PetState& pet,
                         uint64_t wall, uint32_t nowMs, const char* language,
                         bool home = false, uint8_t menu = 3);

private:
    void drawChrome(uint8_t selected, const char* title, bool calling);
    void beginPanel(bool panelChanged, uint8_t selected, const char* title, bool calling);
    void drawCallBadge(uint8_t selected, bool calling);
    void drawStatus(const PetState& pet, bool spanish, uint8_t page, uint32_t nowMs);
    void drawHelix(
        int16_t x, int16_t y, const uint8_t dna[4], float spin,
        int16_t width = 36, int16_t height = 74
    );
    void drawDnaPage(const PetState& pet, bool spanish, uint32_t nowMs);
    void drawInventory(uint8_t selected, bool spanish, const PetState& pet);
    void drawFeeding(uint8_t selected, bool spanish, const PetState& pet);
    void drawBar(const char* label, int value, int16_t y);
    void drawVital(const char* icon, const char* label, int value, int16_t y, uint16_t barColor, uint8_t minLuma = 60);
    void drawEvolution(const Navigation& navigation, bool spanish, const PetState& pet, bool detail);
    void drawEvolutionTree(const Navigation& navigation, bool spanish);
    void drawEvolutionNode(const Navigation& navigation, uint8_t index, bool spanish);
    void drawEvolutionProgress(const Navigation& navigation, bool spanish);
    void drawOptions(
        uint8_t selected,
        BleStatus bluetoothStatus,
        bool spanish,
        const char* language,
        bool soundEnabled,
        uint8_t onlyIndex = 255
    );
    void drawOptionsChip(
        uint8_t index,
        uint8_t selected,
        BleStatus bluetoothStatus,
        bool spanish,
        const char* language,
        bool soundEnabled
    );
    void drawRest(uint8_t selected, bool spanish, bool cold, bool hasBackup, SpeciesId backupSpecies);
    void drawDateTime(const DateTimeMenu& dateMenu);
    void drawStat(
        const char* icon,
        const char* label,
        const char* value,
        int16_t x,
        int16_t y,
        int16_t width = 64,
        const char* extra = nullptr
    );
    void drawStatusPet(const PetState& pet, uint32_t nowMs, bool spanish);
    void drawLabel(const char* text, int16_t x, int16_t y, int16_t width, uint8_t font = 1);

    TFT_eSPI& output_;
    TFT_eSprite& display_;
    AssetStore& assets_;
    // Borrow Home's existing framebuffer; App invalidates its owner before use.
    TFT_eSprite* scene_;
    enum class Scene : uint8_t { None, Arena, Exploration };
    Scene sceneKind_ = Scene::None;
    uint16_t arenaFooterKey_ = 0xFFFF;
    PanelId lastPanel_ = PanelId::Home;
    bool lastSpanish_ = true;
    uint8_t lastStatusPage_ = 255;
    uint32_t lastDnaHelixMs_ = 0;
    uint32_t lastStatusDataMs_ = 0;
    uint8_t lastOptionsIndex_ = 255;
    uint8_t lastInventoryIndex_ = 255;
    uint8_t lastEvolutionIndex_ = 255;
    BleStatus lastBluetoothStatus_ = BleStatus::Off;
    bool lastSoundEnabled_ = true;
    char lastLanguage_[4] = "";
};

}  // namespace vpet
