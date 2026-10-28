#pragma once

#include <stdint.h>
#include <memory>

#include "vpet/Input.h"
#include "vpet/BleService.h"
#include "vpet/DateTimeMenu.h"
#include "vpet/Evolution.h"
#include "vpet/Motion.h"
#include "vpet/Navigation.h"
#include "vpet/Panels.h"
#include "vpet/PetState.h"
#include "vpet/Renderer.h"
#include "vpet/SettingsStore.h"
#include "vpet/PracticeSession.h"
#include "vpet/TrainingSession.h"
#include "vpet/ExplorationSession.h"
#include "vpet/CollectionPanel.h"
#include "vpet/SaveTask.h"

namespace vpet {

class App {
public:
    using WallClock = uint64_t (*)();
    App(Renderer& renderer, Panels& panels, SettingsStore& settingsStore, BleService& bluetooth,
        WallClock wallClock = nullptr, CollectionPanel* collection = nullptr, SaveTask* saveTask = nullptr);
    ~App();
    void begin(uint32_t nowMs);
    void tick(uint32_t nowMs, InputEvent event);
    bool ready() const { return storageReady_ && !savePending_ && !careSave_; }

private:
    void activate(uint32_t nowMs);
    void handlePanelInput(uint32_t nowMs, InputEvent event);
    void drawHome(uint32_t nowMs);
    void drawPendingCare(uint32_t nowMs);
    void rollbackCare(uint32_t nowMs);
    bool prepareCare(uint32_t nowMs, bool& needsSave);
    static void writeCare(void* context);
    void submitCare(uint32_t nowMs);
    void pollCare(uint32_t nowMs, InputEvent event);
    void beginDateTime(bool date);
    void applyDateTime();
    uint8_t clockHour() const;
    int minuteOfDay() const;
    void toggleSleep(uint32_t nowMs);
    bool saveState();
    bool settleStorage();
    bool persistActive();
    bool persistExperience(const RuntimeExperience* events, size_t count);
    static int autoChoice(void* context, const practice::Fighter& fighter, int fallback);
    void activeChanged(uint32_t nowMs);
    CollectionSwitchGuard collectionGuard() const;
    uint64_t calendarNow() const;
    void openExploration();
    void explorationInput(InputEvent event);

    Renderer& renderer_;
    Panels& panels_;
    SettingsStore& settingsStore_;
    BleService& bluetooth_;
    CollectionPanel* collection_;
    enum class CareKind { Food, Item, Light };
    struct CareSave {
        PetState before, snapshot;
        Settings settings;
        CareKind kind = CareKind::Food;
        PanelId origin = PanelId::Feeding;
        uint8_t originIndex = 0;
        bool collection = false, started = false, committed = false, settled = false, careCheckpoint = false;
        uint32_t durationMs = 0, stackFreeBytes = 0, heapMin = 0;
    };
    std::unique_ptr<CareSave> careSave_;
    std::unique_ptr<CareSave> prepareSave(CareKind kind, PanelId origin, uint8_t index);
    std::unique_ptr<SaveTask> ownedSaveTask_;
    SaveTask* saveTask_;
    static constexpr uint32_t kCareTimeScale = 1;

    Settings settings_;
    DateTimeMenu dateMenu_;
    PetState pet_;
    Evolution evolution_;
    Motion motion_;
    Navigation navigation_;
    ExplorationSession exploration_;
    ExplorationClock explorationClock_;
    WallClock wallClock_;
    uint8_t explorationClockStep_ = 0;
    uint32_t lastExplorationCheckpointMs_ = 0;
    PracticeSession practice_;
    bool practicing_ = false;
    TrainingSession training_;
    bool trainingActive_ = false;
    bool storageReady_ = false;
    bool savePending_ = false;
    bool savePendingHome_ = false;
    bool careRecovery_ = false;
    uint32_t lastSaveAttemptMs_ = 0;
    uint32_t lastInjuryCheckpointMs_ = 0;
    uint32_t lastTickMs_ = 0;
    uint32_t deferredCareMs_ = 0;
    uint32_t lastInteractionMs_ = 0;
    uint32_t lastRenderMs_ = 0;
    uint32_t eggStartedMs_ = 0;
};

}  // namespace vpet
