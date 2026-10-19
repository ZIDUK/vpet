#include "vpet/App.h"
#include "vpet/Nutrition.h"
#include "vpet/Strings.h"

#include <Arduino.h>
#include <sys/time.h>
#include <time.h>

namespace vpet {

App::App(Renderer& renderer, Panels& panels, SettingsStore& settingsStore, BleService& bluetooth, WallClock wallClock)
    : renderer_(renderer),
      panels_(panels),
      settingsStore_(settingsStore),
      bluetooth_(bluetooth),
      wallClock_(wallClock),
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
    lastExplorationCheckpointMs_ = nowMs;
    explorationClock_.begin(calendarNow(),pet_.exploration.clockCheckpoint);
    if(pet_.exploration.away()) pet_.rebaseCareClock(nowMs);
    motion_.setSpecies(pet_.species());
    motion_.alignClock(nowMs);
    if (pet_.sleep.asleep && !pet_.dead() && !pet_.exploration.away()) motion_.startAction(Action::Rest,nowMs);
    eggStartedMs_ = nowMs;
}

bool App::saveState() {
    lastSaveAttemptMs_ = lastTickMs_;
    if (explorationClock_.trusted(calendarNow())) pet_.exploration.clockCheckpoint=calendarNow();
    if (settingsStore_.save(pet_, settings_)) return settleStorage();
    savePending_ = true;
    Serial.println("VPET_SAVE_PENDING");
    panels_.drawStorageError(settings_.language.c_str());
    return false;
}

uint64_t App::calendarNow() const {
    if (wallClock_) return wallClock_();
    const time_t now=time(nullptr);
    return now<0 ? 0 : static_cast<uint64_t>(now);
}

void App::openExploration() {
    navigation_.setMenuIndex(3);
    navigation_.setPanel(PanelId::Exploration);
    exploration_.open(pet_,explorationClock_.trusted(calendarNow()));
    panels_.invalidate();
}

void App::explorationInput(InputEvent event) {
    const uint64_t now=calendarNow();
    if (pet_.exploration.away() && !explorationClock_.trusted(now) && exploration_.page!=ExplorationSession::Page::Clock)
        exploration_.open(pet_,false);
    const auto op=exploration_.input(pet_,event,now);
    using Operation=ExplorationSession::Operation;
    if(op==Operation::Close) { navigation_.setPanel(PanelId::Home); return; }
    if(op==Operation::SetClock) { explorationClockStep_=1; beginDateTime(true); return; }
    if(op==Operation::None) return;
    if(!explorationClock_.trusted(now)) {
        exploration_.page=ExplorationSession::Page::Clock;
        exploration_.cursor=0;
        return;
    }
    const PetState before=pet_;
    bool applied=true;
    if(op==Operation::Start) applied=pet_.exploration.start(pet_,exploration_.route,exploration_.stat,now);
    else if(op==Operation::Claim) applied=pet_.exploration.claim(pet_,now);
    else if(op==Operation::Acknowledge) pet_.exploration.acknowledge();
    if(!applied) return;
    pet_.exploration.clockCheckpoint=now;
    if(!settingsStore_.save(pet_,settings_)) {
        pet_=before;
        exploration_.saveFailed=true;
        Serial.println("VPET_EXPLORE_SAVE_REJECTED");
        return;
    }
    exploration_.open(pet_,true);
    Serial.printf("VPET_EXPLORE away=%u receipt=%u route=%u\n",
        pet_.exploration.away(),pet_.exploration.hasReceipt(),static_cast<unsigned>(pet_.exploration.route));
    settleStorage();
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
    if (explorationClockStep_!=1) {
        explorationClock_.adjusted(calendarNow());
        if(explorationClock_.trusted(calendarNow())) pet_.exploration.clockCheckpoint=calendarNow();
        saveState();
    }
}

void App::handlePanelInput(uint32_t nowMs, InputEvent event) {
    const PanelId panel = navigation_.panel();
    if (pet_.sleep.asleep && event==InputEvent::Action &&
        (panel==PanelId::Inventory || panel==PanelId::Feeding || panel==PanelId::Exploration)) return;
    if (panel == PanelId::Exploration) { explorationInput(event); return; }
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
                motion_.alignClock(nowMs);
                motion_.wake(nowMs);
                if (pet_.sleep.asleep) motion_.startAction(Action::Rest,nowMs);
                bluetooth_.setEnabled(settings_.bluetoothEnabled);
                explorationClock_.begin(calendarNow(),pet_.exploration.clockCheckpoint);
                if(pet_.exploration.away()) pet_.rebaseCareClock(nowMs);
                break;
            case 5: beginDateTime(true); break;
            case 6: beginDateTime(false); break;
            case 7: {
                if (pet_.sleep.asleep) return;
                if(pet_.exploration.away()) { openExploration(); return; }
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
        if(selected==7 && pet_.exploration.guide) {
            if(!pet_.dead() && !pet_.cold() && !pet_.injured() && !pet_.exploration.away()) {
                training_.reset(); trainingActive_=true;
            }
            return;
        }
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
                toggleSleep(nowMs);
                navigation_.setPanel(PanelId::Home);
                break;
            case 1:
                pet_.setCold(!pet_.cold());
                saveState();
                break;
            case 2:
                if (settingsStore_.swapOrPark(pet_, settings_)) {
                    explorationClock_.begin(calendarNow(),pet_.exploration.clockCheckpoint);
                    if(pet_.exploration.away()) pet_.rebaseCareClock(nowMs);
                    motion_.setSpecies(pet_.species());
                    motion_.alignClock(nowMs);
                    if (pet_.sleep.asleep) motion_.startAction(Action::Rest,nowMs);
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
            if (explorationClockStep_ && result != DateTimeAction::None) {
                if(result==DateTimeAction::Saved && explorationClockStep_==1) {
                    explorationClockStep_=2; beginDateTime(false);
                } else {
                    explorationClockStep_=0;
                    openExploration();
                }
                return;
            }
            if (result != DateTimeAction::None) {
                navigation_.setPanel(PanelId::Options, dateMenu_.editingDate() ? 5 : 6);
            }
        }
        return;
    }
    navigation_.dispatch(event);
}

uint8_t App::clockHour() const {
    return minuteOfDay()/60;
}

int App::minuteOfDay() const {
    return explorationClock_.trusted(calendarNow()) ? calendarNow()%86400/60 : 720;
}

void App::toggleSleep(uint32_t nowMs) {
    if (pet_.dead() || pet_.species()==SpeciesId::Egg || pet_.cold() || pet_.exploration.away()) return;
    const PetState before=pet_;
    if (pet_.sleep.asleep) pet_.sleep.stop();
    else pet_.sleep.start(explorationClock_.trusted(calendarNow()) ? calendarNow() : 0,pet_.dna()[3]);
    if (!settingsStore_.save(pet_,settings_)) { pet_=before; return; }
    if (pet_.sleep.asleep) motion_.startAction(Action::Rest,nowMs);
    else motion_.wake(nowMs);
    settleStorage();
}

void App::activate(uint32_t nowMs) {
    if (pet_.sleep.asleep) {
        if (navigation_.menuIndex()==5) toggleSleep(nowMs);
        return;
    }
    if(navigation_.menuIndex()==3 || pet_.exploration.away()) {
        openExploration();
        return;
    }
    if (pet_.dead()) {
        pet_.resetToEgg();
        motion_.setSpecies(SpeciesId::Egg);
        motion_.alignClock(nowMs);
        eggStartedMs_ = nowMs;
        saveState();
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
        case 4:
            if (pet_.species() != SpeciesId::Egg && pet_.species() != SpeciesId::Baby &&
                !pet_.dead() && !pet_.cold()) {
                practice_ = PracticeSession();
                practicing_ = true;
                return;
            }
            action = Action::Battle; break;
        case 5:
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
        if(pet_.exploration.away() || pet_.sleep.asleep) pet_.pauseCareClock(nowMs-lastTickMs_);
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
        explorationClockStep_ = 0;
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
            const bool committed=settingsStore_.save(pet_,settings_);
            practice_.finishSave(pet_,beforePet,beforeSession,committed);
            if (!committed) practicing_=true;
            else if (!settleStorage()) return;
        }
        if (!practicing_) { panels_.invalidate(); motion_.alignClock(nowMs); }
        else if (event != InputEvent::None || nowMs - lastRenderMs_ >= 50) {
            lastRenderMs_ = nowMs;
            renderer_.invalidate();
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
            if (!settingsStore_.save(pet_,settings_)) {
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
    if(pet_.exploration.away()) {
        pet_.pauseCareClock(elapsed);
        motion_.alignClock(nowMs);
        if(explorationClock_.trusted(calendarNow()) && nowMs-lastExplorationCheckpointMs_>=60000) {
            lastExplorationCheckpointMs_=nowMs;
            if(!saveState()) return;
        }
    } else {
    const bool wasDead = pet_.dead();
    const bool sleeping=pet_.sleep.asleep;
    pet_.tick(elapsed,sleeping);
    if (sleeping) {
        pet_.pauseCareClock(elapsed);
        if (pet_.dead()) { pet_.sleep.stop(); motion_.wake(nowMs); }
        else {
            const int checkpoint=pet_.sleep.elapsed/300;
            int energy=pet_.energy(); bool reward=false;
            const bool complete=pet_.sleep.advanceMs(elapsed,energy,reward);
            pet_.setEnergy(energy);
            if (reward) pet_.finishSleepNight();
            if (complete) motion_.wake(nowMs);
            if ((complete || pet_.sleep.elapsed/300!=checkpoint) && !saveState()) return;
        }
    }
    if (pet_.dead() != wasDead || (pet_.injured() && !pet_.cold() && nowMs - lastInjuryCheckpointMs_ >= 60000)) {
        lastInjuryCheckpointMs_ = nowMs;
        if (!saveState()) return;
    }
    const uint8_t hour = clockHour();
    const CallUpdate call = pet_.sleep.asleep ? CallUpdate::None : pet_.updateCall(
        nowMs,
        kCareTimeScale,
        hour,
        motion_.state() == MotionState::Sleep,
        false
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
    } else if (!pet_.sleep.asleep && !pet_.cold() && !pet_.dead() && motion_.state() != MotionState::Evolution && evolution_.evolve(pet_, kCareTimeScale)) {
        motion_.setSpecies(pet_.species());
        motion_.startEvolution(nowMs);
        if (!saveState()) return;
    }
    motion_.setTired(!pet_.dead() && !pet_.injured() && !pet_.cold() &&
        pet_.sleep.tired(pet_.energy(),pet_.dna()[3],explorationClock_.trusted(calendarNow()) ? minuteOfDay() : -1),nowMs);
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

    }

    const bool acceptsInput =
        navigation_.panel() != PanelId::Home ||
        pet_.pendingAction() == Action::None ||
        motion_.state() == MotionState::Sleep;
    if (acceptsInput && event != InputEvent::None) {
        if (navigation_.panel() == PanelId::Home && event == InputEvent::Action &&
            (pet_.dead() || (navigation_.menuIndex() >= 1 && navigation_.menuIndex() <= 5) ||
             (pet_.exploration.away() && navigation_.menuIndex()==6))) {
            activate(nowMs);
        } else if (navigation_.panel() == PanelId::Home && event == InputEvent::Action &&
                   navigation_.menuIndex() == 7) {
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
    if (panel == PanelId::Exploration) {
        const auto page = exploration_.page;
        intervalMs = page == ExplorationSession::Page::Routes || page == ExplorationSession::Page::Stats ? 1000 : 70;
    } else if (panel == PanelId::Home && pet_.exploration.away()) intervalMs = 70;
    if (panel == PanelId::Status || panel == PanelId::Inventory || panel == PanelId::Feeding || panel == PanelId::EvolutionTree ||
        panel == PanelId::EvolutionDetail || panel == PanelId::Rest ||
        panel == PanelId::Options) {
        intervalMs = panel == PanelId::Status ? 100 : 1000;
    }
    if (event != InputEvent::None || nowMs - lastRenderMs_ >= intervalMs) {
        lastRenderMs_ = nowMs;
        if (navigation_.panel() == PanelId::Exploration) {
            renderer_.invalidate();
            panels_.drawExploration(exploration_,pet_,calendarNow(),nowMs,settings_.language.c_str());
        } else if (navigation_.panel() == PanelId::Home && pet_.exploration.away()) {
            renderer_.invalidate();
            ExplorationSession home;
            home.open(pet_,explorationClock_.trusted(calendarNow()));
            panels_.drawExploration(home,pet_,calendarNow(),nowMs,settings_.language.c_str(),true,navigation_.menuIndex());
        } else if (navigation_.panel() == PanelId::Home) {
            panels_.invalidate();
            renderer_.draw({
                pet_,
                motion_,
                navigation_.menuIndex(),
                nowMs,
                languageIsSpanish(settings_.language.c_str()),
                minuteOfDay(),
                !pet_.dead() && !pet_.injured() && !pet_.cold() && pet_.sleep.tired(pet_.energy(),pet_.dna()[3],
                    explorationClock_.trusted(calendarNow()) ? minuteOfDay() : -1)
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
