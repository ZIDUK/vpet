#include "vpet/App.h"
#include "vpet/Nutrition.h"
#include "vpet/Strings.h"

#include <Arduino.h>
#include <sys/time.h>
#include <time.h>

namespace vpet {

App::App(Renderer& renderer, Panels& panels, SettingsStore& settingsStore, BleService& bluetooth)
    : renderer_(renderer),
      panels_(panels),
      settingsStore_(settingsStore),
      bluetooth_(bluetooth),
      motion_(240, 135, 24, 88) {}

void App::begin(uint32_t nowMs) {
    savePending_ = false;
    lastInteractionMs_ = nowMs;
    lastTickMs_ = nowMs;
    lastRenderMs_ = nowMs - 50;
    storageReady_=settingsStore_.load(pet_, settings_) != LoadResult::Unsupported;
    if (!storageReady_) {
        Serial.println("VPET_STORAGE_RECOVERY_BLOCKED");
        panels_.drawStorageError(settings_.language.c_str());
        return;
    }
    if ((settingsStore_.needsLifeRestart() && !settingsStore_.restartLifeIfNeeded(pet_, settings_)) ||
        (settingsStore_.migratedDna() && !settingsStore_.save(pet_, settings_)) ||
        !settingsStore_.recoverPending()) {
        storageReady_ = false;
        Serial.println("VPET_STORAGE_RECOVERY_BLOCKED");
        panels_.drawStorageError(settings_.language.c_str());
        return;
    }
    if (!bluetooth_.setEnabled(settings_.bluetoothEnabled)) {
        storageReady_ = false;
        Serial.println("VPET_INIT_BLOCKED reason=BLE");
        return;
    }
    lastInjuryCheckpointMs_ = nowMs;
    motion_.setSpecies(pet_.species());
    motion_.alignClock(nowMs);
    eggStartedMs_ = nowMs;
}

bool App::saveState() {
    lastSaveAttemptMs_ = lastTickMs_;
    if (settingsStore_.save(pet_, settings_)) return settleStorage();
    savePending_ = true;
    Serial.println("VPET_SAVE_PENDING");
    panels_.drawStorageError(settings_.language.c_str());
    return false;
}

bool App::settleStorage() {
    lastSaveAttemptMs_ = lastTickMs_;
    savePending_ = !settingsStore_.recoverPending();
    if (savePending_) {
        Serial.println("VPET_SAVE_PENDING");
        panels_.drawStorageError(settings_.language.c_str());
    } else {
        panels_.invalidate();
    }
    return !savePending_;
}

void App::beginDateTime(bool date) {
    int values[5] = {2026, 1, 1, 0, 0};
    const time_t now = time(nullptr);
    struct tm value {};
    localtime_r(&now, &value);
    if (value.tm_year + 1900 >= 2024) {
        values[0] = value.tm_year + 1900;
        values[1] = value.tm_mon + 1;
        values[2] = value.tm_mday;
        values[3] = value.tm_hour;
        values[4] = value.tm_min;
    }
    dateMenu_.begin(date, values, languageIsSpanish(settings_.language.c_str()));
    navigation_.setPanel(PanelId::DateTime);
}

void App::applyDateTime() {
    const int* values = dateMenu_.values();
    struct tm value {};
    value.tm_year = values[0] - 1900;
    value.tm_mon = values[1] - 1;
    value.tm_mday = values[2];
    value.tm_hour = values[3];
    value.tm_min = values[4];
    const time_t epoch = mktime(&value);
    const timeval clock = {epoch, 0};
    settimeofday(&clock, nullptr);
}

void App::handlePanelInput(uint32_t nowMs, InputEvent event) {
    const PanelId panel = navigation_.panel();
    if (panel == PanelId::Options) {
        if (event == InputEvent::Next || event == InputEvent::Back) {
            navigation_.dispatch(event);
            return;
        }
        if (event != InputEvent::Action) return;
        switch (navigation_.panelIndex()) {
            case 0:
                settings_.bluetoothEnabled = !settings_.bluetoothEnabled;
                if (!bluetooth_.setEnabled(settings_.bluetoothEnabled)) {
                    settings_.bluetoothEnabled = false;
                }
                saveState();
                break;
            case 1:
                settings_.language = settings_.language == "ES" ? "EN" : "ES";
                break;
            case 2:
                settings_.soundEnabled = !settings_.soundEnabled;
                break;
            case 3:
                saveState();
                break;
            case 4:
                if (settingsStore_.load(pet_, settings_) != LoadResult::Loaded) {
                    storageReady_ = false;
                    Serial.println("VPET_STORAGE_RECOVERY_BLOCKED");
                    panels_.drawStorageError(settings_.language.c_str());
                    return;
                }
                motion_.setSpecies(pet_.species());
                bluetooth_.setEnabled(settings_.bluetoothEnabled);
                break;
            case 5: beginDateTime(true); break;
            case 6: beginDateTime(false); break;
            case 7: {
                const bool fromEgg = pet_.species() == SpeciesId::Egg;
                if (evolution_.force(pet_)) {
                    if (fromEgg && !pet_.hasDna()) pet_.rollDna(esp_random() ^ nowMs);
                    motion_.setSpecies(pet_.species());
                    motion_.alignClock(nowMs);
                    if (pet_.species() == SpeciesId::Egg) {
                        eggStartedMs_ = nowMs;
                    } else {
                        motion_.startEvolution(nowMs);
                    }
                    saveState();
                    navigation_.setPanel(PanelId::Home);
                }
                break;
            }
            case 8: navigation_.setPanel(PanelId::Home); break;
        }
        return;
    }
    if (panel == PanelId::Inventory) {
        navigation_.setPanelIndex(pet_.clampVisibleInventoryIndex(navigation_.panelIndex()));
        if (event == InputEvent::Back) {
            navigation_.dispatch(event);
            return;
        }
        if (event == InputEvent::Next) {
            navigation_.setPanelIndex(pet_.nextVisibleInventoryIndex(navigation_.panelIndex()));
            return;
        }
        if (event != InputEvent::Action) return;
        const uint8_t selected=navigation_.panelIndex();
        if (selected>=8 && selected<8+adopted::kCount &&
            !strcmp(adopted::kItems[selected-8].id,"training_manual")) {
            if (pet_.canOpenTrainingManual(selected)) {
                training_.reset(); trainingActive_=true;
            }
            return;
        }
        const PetState before=pet_;
        const ItemUseResult result = pet_.useItem(navigation_.panelIndex());
        if (result == ItemUseResult::Used) {
            if (selected>=8) {
                if (!settingsStore_.commitConsumables(pet_)) {
                    pet_=before;
                    Serial.println("VPET_ITEM_SAVE_FAILED");
                } else settleStorage();
            } else saveState();
            navigation_.setPanelIndex(pet_.clampVisibleInventoryIndex(navigation_.panelIndex()));
        }
        if (result == ItemUseResult::Back) navigation_.setPanel(PanelId::Home);
        return;
    }
    if (panel == PanelId::Feeding) {
        if (event == InputEvent::Back) {
            navigation_.setPanel(PanelId::Home);
            return;
        }
        if (event == InputEvent::Next) {
            navigation_.setPanelIndex((navigation_.panelIndex() + 1) % Navigation::kFeedingCount);
            return;
        }
        if (event != InputEvent::Action) return;
        if (navigation_.panelIndex() == 2) {
            navigation_.setPanel(PanelId::Home);
            return;
        }
        const PetState before = pet_;
        const FoodId food = navigation_.panelIndex() == 0 ? FoodId::Meat : FoodId::Protein;
        if (applyFood(pet_, food) == FoodResult::Applied) {
            if (settingsStore_.commitFood(pet_)) {
                motion_.startAction(Action::Feed, nowMs);
                navigation_.setPanel(PanelId::Home);
                settleStorage();
            } else {
                pet_ = before;
            }
        }
        return;
    }
    if (panel == PanelId::Rest) {
        if (event == InputEvent::Next || event == InputEvent::Back) {
            navigation_.dispatch(event);
            return;
        }
        if (event != InputEvent::Action) return;
        switch (navigation_.panelIndex()) {
            case 0:
                if (pet_.beginAction(Action::Rest)) {
                    motion_.startAction(Action::Rest, nowMs);
                    navigation_.setPanel(PanelId::Home);
                }
                break;
            case 1:
                pet_.setCold(!pet_.cold());
                saveState();
                break;
            case 2:
                if (settingsStore_.swapOrPark(pet_, settings_)) {
                    motion_.setSpecies(pet_.species());
                    motion_.alignClock(nowMs);
                    if (pet_.species() == SpeciesId::Egg) eggStartedMs_ = nowMs;
                    navigation_.setPanel(PanelId::Home);
                    settleStorage();
                }
                break;
            case 3:
                navigation_.setPanel(PanelId::Home);
                break;
        }
        return;
    }
    if (panel == PanelId::DateTime) {
        if (event == InputEvent::Next) {
            dateMenu_.next();
        } else if (event == InputEvent::Action) {
            const DateTimeAction result = dateMenu_.activate();
            if (result == DateTimeAction::Saved) applyDateTime();
            if (result != DateTimeAction::None) {
                navigation_.setPanel(PanelId::Options, dateMenu_.editingDate() ? 5 : 6);
            }
        }
        return;
    }
    navigation_.dispatch(event);
}

uint8_t App::clockHour() const {
    uint8_t hour = 12;
    const time_t wall = time(nullptr);
    struct tm local {};
    if (localtime_r(&wall, &local) != nullptr && local.tm_year + 1900 >= 2024) {
        hour = static_cast<uint8_t>(local.tm_hour);
    }
    return hour;
}

void App::activate(uint32_t nowMs) {
    if (pet_.dead()) {
        pet_.resetToEgg();
        motion_.setSpecies(SpeciesId::Egg);
        motion_.alignClock(nowMs);
        eggStartedMs_ = nowMs;
        saveState();
        return;
    }
    if (motion_.state() == MotionState::Sleep) {
        if (navigation_.menuIndex() == 4) {
            motion_.wake(nowMs);
            pet_.noteWake(clockHour());
            saveState();
        }
        return;
    }
    Action action = Action::None;
    switch (navigation_.menuIndex()) {
        case 1:
            navigation_.setPanel(PanelId::Feeding);
            return;
        case 2:
            // Timed training owns its clock and saves once at completion.
            training_.reset();
            trainingActive_ = true;
            return;
        case 3:
            if (pet_.species() != SpeciesId::Egg && pet_.species() != SpeciesId::Baby &&
                !pet_.dead() && !pet_.cold()) {
                practice_ = PracticeSession();
                practicing_ = true;
                return;
            }
            action = Action::Battle; break;
        case 4:
            navigation_.setPanel(PanelId::Rest);
            return;
        default: return;
    }
    if (pet_.beginAction(action)) {
        motion_.startAction(action, nowMs);
    }
}

void App::tick(uint32_t nowMs, InputEvent event) {
    if (!storageReady_) {
        if (nowMs-lastRenderMs_>=1000) begin(nowMs);
        return;
    }
    if (savePending_) {
        lastTickMs_ = nowMs;
        motion_.alignClock(nowMs);
        if (nowMs - lastSaveAttemptMs_ >= 1000) saveState();
        return;
    }
    const uint32_t elapsed = nowMs - lastTickMs_;
    lastTickMs_ = nowMs;
    const bool busy = (trainingActive_ && training_.state == TrainingSession::State::Session)
        || (practicing_ && (practice_.page == PracticeSession::Page::Arena ||
            practice_.page == PracticeSession::Page::Bag) &&
            (!practice_.battle.result || practice_.pendingAward));
    if (event != InputEvent::None || busy) lastInteractionMs_ = nowMs;
    if (!busy && nowMs - lastInteractionMs_ >= 10000
        && (trainingActive_ || practicing_ || navigation_.panel() != PanelId::Home)) {
        trainingActive_ = false;
        practicing_ = false;
        training_ = TrainingSession();
        navigation_.setPanel(PanelId::Home);
        panels_.invalidate();
        motion_.alignClock(nowMs);
    }
    if (practicing_) {
        const PetState beforePet=pet_;
        const PracticeSession beforeSession=practice_;
        practice_.tick(pet_, nowMs);
        if (!practice_.battle.result || beforeSession.battle.result)
            practicing_ = practice_.input(pet_, event, nowMs);
        if (practice_.dirty) {
            const bool committed=settingsStore_.commitConsumables(pet_);
            practice_.finishSave(pet_,beforePet,beforeSession,committed);
            if (!committed) practicing_=true;
            else if (!settleStorage()) return;
        }
        if (!practicing_) { panels_.invalidate(); motion_.alignClock(nowMs); }
        else if (event != InputEvent::None || nowMs - lastRenderMs_ >= 50) {
            lastRenderMs_ = nowMs;
            panels_.drawPractice(practice_, pet_, nowMs,settings_.language.c_str());
        }
        return;
    }
    if (trainingActive_) {
        const bool stillActive = training_.input(pet_, event, nowMs);
        if (training_.techniquesRequested) {
            training_.techniquesRequested = false;
            practice_ = PracticeSession();
            practice_.page = PracticeSession::Page::Tech;
            practicing_ = true;
            return;
        }
        if (training_.dirty && training_.needsRollback) {
            if (!settingsStore_.commitConsumables(pet_)) {
                training_.rollbackFromSnapshot(pet_);
            } else settleStorage();
            training_.dirty = false;
            training_.needsRollback = false;
        }
        if (savePending_) return;
        if (!stillActive) {
            trainingActive_ = false;
            panels_.invalidate();
            motion_.alignClock(nowMs);
        } else if (event != InputEvent::None || nowMs - lastRenderMs_ >= 33) {
            lastRenderMs_ = nowMs;
            panels_.drawTraining(training_, pet_, nowMs, settings_.language.c_str());
        }
        return;
    }
    const bool wasDead = pet_.dead();
    pet_.tick(elapsed);
    if (pet_.dead() != wasDead || (pet_.injured() && !pet_.cold() && nowMs - lastInjuryCheckpointMs_ >= 60000)) {
        lastInjuryCheckpointMs_ = nowMs;
        if (!saveState()) return;
    }
    const uint8_t hour = clockHour();
    const CallUpdate call = pet_.updateCall(
        nowMs,
        kCareTimeScale,
        hour,
        motion_.state() == MotionState::Sleep
    );
    if (call == CallUpdate::Started && settings_.soundEnabled) {
        const char* reason = "HUNGER";
        if (pet_.callReason() == CallReason::Strength) reason = "STRENGTH";
        if (pet_.callReason() == CallReason::Lights) reason = "LIGHTS";
        Serial.printf("VPET_CALL reason=%s\n", reason);
    }
    if (call == CallUpdate::Missed) {
        if (!saveState()) return;
    }
    if (pet_.species() == SpeciesId::Egg && !pet_.cold()) {
        constexpr uint32_t kEggLifeMs = 2000;
        constexpr uint32_t kEggHatchMs = 800;
        if (motion_.state() != MotionState::Hatch && nowMs - eggStartedMs_ >= kEggLifeMs - kEggHatchMs) {
            motion_.startHatch(nowMs);
        }
        if (nowMs - eggStartedMs_ >= kEggLifeMs) {
            pet_.evolveTo(SpeciesId::Baby);
            if (!pet_.hasDna()) pet_.rollDna(esp_random() ^ nowMs);
            motion_.setSpecies(SpeciesId::Baby);
            motion_.alignClock(nowMs);
            if (!saveState()) return;
        }
    } else if (!pet_.cold() && !pet_.dead() && motion_.state() != MotionState::Evolution && evolution_.evolve(pet_, kCareTimeScale)) {
        motion_.setSpecies(pet_.species());
        motion_.startEvolution(nowMs);
        if (!saveState()) return;
    }
    motion_.tick(nowMs);
    if (motion_.consumeActionCompleted()) {
        const Action finished = pet_.pendingAction();
        pet_.completeAction();
        if (finished == Action::Battle) {
            Serial.printf(
                "VPET_BATTLE won=%u injured=%u\n",
                pet_.lastBattleWon() ? 1U : 0U,
                pet_.injured() ? 1U : 0U
            );
            if (!saveState()) return;
            if (!pet_.dead()) {
                motion_.startReaction(pet_.lastBattleWon(), pet_.injured(), nowMs);
            }
        }
        if (pet_.dead()) Serial.printf("VPET_DEAD\n");
    }

    const bool acceptsInput =
        navigation_.panel() != PanelId::Home ||
        pet_.pendingAction() == Action::None ||
        motion_.state() == MotionState::Sleep;
    if (acceptsInput && event != InputEvent::None) {
        if (navigation_.panel() == PanelId::Home && event == InputEvent::Action &&
            (pet_.dead() || (navigation_.menuIndex() >= 1 && navigation_.menuIndex() <= 4))) {
            activate(nowMs);
        } else if (navigation_.panel() == PanelId::Home && event == InputEvent::Action &&
                   navigation_.menuIndex() == 6) {
            navigation_.dispatch(event);
            navigation_.setCurrentSpecies(pet_.species());
            navigation_.openEvolutionTree(pet_.species());
        } else if (navigation_.panel() == PanelId::Home) {
            navigation_.dispatch(event);
        } else {
            handlePanelInput(nowMs, event);
        }
    }

    if (savePending_ || !storageReady_) return;
    navigation_.setCurrentSpecies(pet_.species());

    const PanelId panel = navigation_.panel();
    uint32_t intervalMs = 33;
    if (panel == PanelId::Status || panel == PanelId::Inventory || panel == PanelId::Feeding || panel == PanelId::EvolutionTree ||
        panel == PanelId::EvolutionDetail || panel == PanelId::Rest ||
        panel == PanelId::Options) {
        intervalMs = panel == PanelId::Status ? 100 : 1000;
    }
    if (event != InputEvent::None || nowMs - lastRenderMs_ >= intervalMs) {
        lastRenderMs_ = nowMs;
        if (navigation_.panel() == PanelId::Home) {
            panels_.invalidate();
            renderer_.draw({
                pet_,
                motion_,
                navigation_.menuIndex(),
                nowMs,
                languageIsSpanish(settings_.language.c_str())
            });
        } else {
            panels_.draw(
                navigation_,
                pet_,
                bluetooth_.status(),
                dateMenu_,
                settings_.language.c_str(),
                settings_.soundEnabled,
                settingsStore_.hasBackup(),
                settingsStore_.backupSpecies(),
                nowMs
            );
        }
    }
}

}  // namespace vpet
