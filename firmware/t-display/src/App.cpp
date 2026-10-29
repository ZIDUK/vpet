#include "vpet/App.h"
#include "vpet/Nutrition.h"
#include "vpet/EvolutionProgress.h"
#include "vpet/Strings.h"

#include <Arduino.h>
#include <sys/time.h>
#include <time.h>
#include <algorithm>
#include <cerrno>
#include <new>
#ifdef ARDUINO
#include "vpet/FreeRtosSaveTask.h"
#endif

namespace vpet {
namespace {
#ifndef ARDUINO
// Host harnesses can inject deferred execution; the default preserves their
// synchronous storage fixtures without introducing threads into portable tests.
class HostSaveTask final : public SaveTask {
public:
    bool start(Work work, void* context) override { work(context); done_ = true; return true; }
    bool finished() const override { return done_; }
    void reset() override { done_ = false; }
    void wait() override {}
private:
    bool done_ = false;
};
#endif
}

App::App(Renderer& renderer, Panels& panels, SettingsStore& settingsStore, BleService& bluetooth, WallClock wallClock,
         CollectionPanel* collection, SaveTask* saveTask)
    : renderer_(renderer),
      panels_(panels),
      settingsStore_(settingsStore),
      bluetooth_(bluetooth),
      collection_(collection),
      saveTask_(saveTask),
      wallClock_(wallClock),
      motion_(240, 135, 24, 88) {
    if (!saveTask_) {
#ifdef ARDUINO
        ownedSaveTask_.reset(new (std::nothrow) FreeRtosSaveTask);
#else
        ownedSaveTask_.reset(new (std::nothrow) HostSaveTask);
#endif
        saveTask_ = ownedSaveTask_.get();
    }
}

App::~App() {
    if (progressSave_ && progressSave_->started) saveTask_->wait();
    if (progressMode_) collection_->setInterrupt(nullptr,nullptr);
    if ((careSave_ && careSave_->started) || (trainingSave_ && trainingSave_->started)) saveTask_->wait();
}

void App::begin(uint32_t nowMs) {
    if (careSave_ || trainingSave_ || (progressSave_ && progressSave_->kind!=ProgressKind::None)) return;
    savePending_ = false;
    rejectedExperienceRecovery_ = false;
    savePendingHome_ = false;
    careRecovery_ = false;
    deferredCareMs_ = 0;
    navigation_.setPanel(PanelId::Home);
    navigation_.setMenuIndex(0);
    practicing_=trainingActive_=false;
    lastInteractionMs_ = nowMs;
    lastTickMs_ = nowMs;
    lastRenderMs_ = nowMs - 50;
    const auto collectionLoad=collection_ ? collection_->load(pet_,settings_) : CollectionLoad::Missing;
    const bool useLegacy=collectionLoad==CollectionLoad::Missing;
    storageReady_=useLegacy ? settingsStore_.load(pet_, settings_) != LoadResult::Unsupported :
        collectionLoad==CollectionLoad::Loaded;
    if (!storageReady_) {
        Serial.println("VPET_STORAGE_RECOVERY_BLOCKED");
        panels_.drawStorageError(settings_.language.c_str());
        return;
    }
    if (useLegacy && ((settingsStore_.needsLifeRestart() && !settingsStore_.restartLifeIfNeeded(pet_, settings_)) ||
        (settingsStore_.migratedDna() && !settingsStore_.save(pet_, settings_)) ||
        !settingsStore_.recoverPending())) {
        storageReady_ = false;
        Serial.println("VPET_STORAGE_RECOVERY_BLOCKED");
        panels_.drawStorageError(settings_.language.c_str());
        return;
    }
    progressMode_=collection_ && collection_->enabled() && collection_->progressEnabled();
    if (progressMode_) {
        if (!progressSave_) progressSave_.reset(new (std::nothrow) ProgressSave);
        if (!progressSave_ || !saveTask_) {
            storageReady_=false; panels_.drawStorageError(settings_.language.c_str()); return;
        }
        progressInputHead_=progressInputCount_=0;
        progressInputOverflow_=sleepCheckpoint_=progressSettlement_=progressWarning_=false;
        progressInterrupt_.store(false,std::memory_order_release);
        collection_->setInterrupt(interruptProgress,this);
        lastProgressCheckpointMs_=nowMs;
        progressMaxQueueDelayMs_=progressMaxDrawLatencyMs_=0;
        progressVisibleInput_=progressSafeHome_=false;
        Serial.printf("VPET_PROGRESS_MEMORY job_bytes=%u pet_bytes=%u view_bytes=%u queue_bytes=%u\n",
            unsigned(sizeof(ProgressSave)),unsigned(sizeof(PetState)),unsigned(sizeof(ProgressView)),
            unsigned(sizeof(progressInputs_)));
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
    if (progressMode_) return persistActive();
    lastSaveAttemptMs_ = lastTickMs_;
    if (explorationClock_.trusted(calendarNow())) pet_.exploration.clockCheckpoint=calendarNow();
    if (persistActive()) return settleStorage();
    savePending_ = true;
    Serial.println("VPET_SAVE_PENDING");
    if (!savePendingHome_) panels_.drawStorageError(settings_.language.c_str());
    return false;
}

uint64_t App::calendarNow() const {
    if (wallClock_) return wallClock_();
    const time_t now=time(nullptr);
    return now<0 ? 0 : static_cast<uint64_t>(now);
}

bool App::persistActive() {
    if (progressMode_) {
        if (progressSave_->kind==ProgressKind::None) progressSave_->kind=ProgressKind::Receipt;
        return progressSave_->kind==ProgressKind::Receipt;
    }
    if (collection_ && collection_->enabled()) {
        const bool committed=collection_->save(pet_,settings_);
        if (!committed) savePending_=true;
        return committed;
    }
    if (collection_ && collection_->failed()) { savePending_=true; return false; }
    return settingsStore_.save(pet_,settings_);
}
bool App::persistExperience(const RuntimeExperience* events, size_t count) {
    if (progressMode_) {
        if (!persistActive() || count>8-progressSave_->eventCount || (count && !events)) return false;
        for (size_t i=0;i<count;++i) progressSave_->events[progressSave_->eventCount++]=events[i];
        return true;
    }
    if (collection_ && collection_->enabled() && count) {
        const bool committed=collection_->saveExperience(pet_,settings_,events,count);
        if (!committed) savePending_=true;
        return committed;
    }
    return persistActive();
}
bool App::recoverRejectedExperience(const char* context) {
    const int systemError=errno;
    const char* stage=collection_ && collection_->enabled()?collection_->saveFailure():"legacy";
    const bool recovered=collection_ && collection_->enabled() && collection_->recoverRejectedSave();
    rejectedExperienceRecovery_=!recovered;
    if (recovered) savePending_=savePendingHome_=false;
    Serial.printf("VPET_EXPERIENCE_SAVE_REJECTED context=%s stage=%s errno=%d recovered=%u\n",
        context,stage,systemError,recovered?1U:0U);
    return recovered;
}
int App::autoChoice(void* context, const practice::Fighter& fighter, int fallback) {
    auto* app=static_cast<App*>(context);
    if (app && app->progressMode_ && app->progressSave_->started) return fallback;
    if (!app || !app->collection_ || !app->collection_->enabled()) return fallback;
    uint8_t learned=0;
    for (int i=0;i<techniques::kCount;++i)
        if (app->pet_.practice.learned(i,app->pet_.techniqueStage())) learned|=1u<<i;
    return app->collection_->chooseAuto(fighter,learned);
}

CollectionSwitchGuard App::collectionGuard() const {
    CollectionSwitchGuard guard;
    guard.training=trainingActive_; guard.arena=practicing_ || pet_.pendingAction()!=Action::None;
    guard.journey=pet_.exploration.away(); guard.sleeping=pet_.sleep.asleep; guard.paused=pet_.cold();
    guard.pendingJournal=savePending_; guard.storageError=!storageReady_;
    return guard;
}

void App::activeChanged(uint32_t nowMs) {
    trainingActive_=practicing_=false;
    training_=TrainingSession(); practice_=PracticeSession();
    lastInjuryCheckpointMs_=lastExplorationCheckpointMs_=nowMs;
    eggStartedMs_=nowMs;
    explorationClock_.begin(calendarNow(),pet_.exploration.clockCheckpoint);
    pet_.rebaseCareClock(nowMs);
    motion_.setSpecies(pet_.species()); motion_.alignClock(nowMs);
    motion_.wake(nowMs);
    if (pet_.sleep.asleep) motion_.startAction(Action::Rest,nowMs);
    navigation_.setCurrentSpecies(pet_.species());
    panels_.invalidate(); renderer_.invalidate();
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
    RuntimeExperience experience{2,0,0,0};
    if (op==Operation::Claim) {
        const auto& reward=pet_.exploration.receipt;
        experience.action=static_cast<uint8_t>(reward.route);
        experience.reward=(reward.good?50:-50)+std::min(30,int(reward.ev)*10+int(reward.mastery)*5);
    }
    if(!persistExperience(&experience,op==Operation::Claim?1:0)) {
        pet_=before;
        exploration_.saveFailed=true;
        if (op==Operation::Claim) recoverRejectedExperience("exploration_claim");
        Serial.println("VPET_EXPLORE_SAVE_REJECTED");
        return;
    }
    if (progressMode_) progressSave_->origin=ProgressOrigin::Exploration;
    exploration_.open(pet_,true);
    Serial.printf("VPET_EXPLORE away=%u receipt=%u route=%u\n",
        pet_.exploration.away(),pet_.exploration.hasReceipt(),static_cast<unsigned>(pet_.exploration.route));
    settleStorage();
}

bool App::settleStorage() {
    if (progressMode_) return !savePending_;
    lastSaveAttemptMs_ = lastTickMs_;
    savePending_ = collection_ && collection_->enabled() ? collection_->failed() : !settingsStore_.recoverPending();
    if (savePending_) {
        Serial.println("VPET_SAVE_PENDING");
        if (!savePendingHome_) panels_.drawStorageError(settings_.language.c_str());
    } else {
        savePendingHome_ = false;
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
    if (progressMode_) {
        if (epoch<0 || !persistActive()) return;
        progressSave_->setClock=true;
        progressSave_->epoch=static_cast<uint64_t>(epoch);
        pet_.exploration.clockCheckpoint=static_cast<uint64_t>(epoch);
        return;
    }
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
    if (panel==PanelId::Collection) {
        if (!collection_) { navigation_.setPanel(PanelId::Options,option_menu::collection); return; }
        if (progressMode_) {
            const auto page=collection_->page();
            const bool navigationOnly=event==InputEvent::Next || event==InputEvent::None ||
                (event==InputEvent::Back && page!=CollectionPanel::Page::Parents) ||
                (event==InputEvent::Action && (page==CollectionPanel::Page::Preferences ||
                    page==CollectionPanel::Page::Migration || page==CollectionPanel::Page::Error));
            if (navigationOnly) {
                if (collection_->input(event,pet_,settings_,collectionGuard()))
                    navigation_.setPanel(PanelId::Options,option_menu::collection);
                return;
            }
            progressSave_->kind=ProgressKind::CollectionInput;
            progressSave_->input=event;
            progressSave_->guard=collectionGuard();
            return;
        }
        const bool close=collection_->input(event,pet_,settings_,collectionGuard());
        if (collection_->changedActive()) activeChanged(nowMs);
        if (collection_->failed()) { storageReady_=false; panels_.drawStorageError(settings_.language.c_str()); return; }
        if (close) { navigation_.setPanel(PanelId::Options,option_menu::collection); panels_.invalidate(); }
        return;
    }
    if (panel == PanelId::EvolutionDetail && event == InputEvent::Next) {
        const auto progress = evolution_progress::forPet(pet_, navigation_.panelIndex());
        navigation_.setEvolutionDetailPage((navigation_.evolutionDetailPage() + 1) % progress.pages());
        return;
    }
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
                if (progressMode_) saveState();
                break;
            case 2:
                settings_.soundEnabled = !settings_.soundEnabled;
                if (progressMode_) saveState();
                break;
            case 3:
                saveState();
                break;
            case 4:
                if (progressMode_) { progressSave_->kind=ProgressKind::Reload; break; }
                if ((collection_ && collection_->enabled() ?
                     collection_->load(pet_,settings_)!=CollectionLoad::Loaded :
                     settingsStore_.load(pet_, settings_) != LoadResult::Loaded)) {
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
                if (collection_ && collection_->enabled()) return;
                if (pet_.sleep.asleep) return;
                if(pet_.exploration.away()) { openExploration(); return; }
                const bool fromEgg = pet_.species() == SpeciesId::Egg;
                if (evolution_.force(pet_)) {
                    if (fromEgg && !pet_.hasDna() && !(collection_ && collection_->enabled()))
                        pet_.rollDna(esp_random() ^ nowMs);
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
            case option_menu::pause: {
                const PetState before=pet_;
                pet_.setCold(!pet_.cold());
                if(!persistActive()) pet_=before;
                else settleStorage();
                break;
            }
            case option_menu::collection:
                if (collection_) { collection_->setPreview(pet_); collection_->open(); navigation_.setPanel(PanelId::Collection); }
                else panels_.drawStorageError(settings_.language.c_str());
                break;
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
        if (selected==6) { navigation_.setPanel(PanelId::Home); return; }
        auto request=prepareSave(CareKind::Item,panel,selected);
        if (!request) return;
        const ItemUseResult result = pet_.useItem(navigation_.panelIndex());
        if (result == ItemUseResult::Used) {
            request->snapshot=pet_;
            careSave_=std::move(request);
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
        auto request=prepareSave(CareKind::Food,panel,navigation_.panelIndex());
        if (!request) return;
        const FoodId food = navigation_.panelIndex() == 0 ? FoodId::Meat : FoodId::Protein;
        const FoodResult result=applyFood(pet_,food);
        if (result == FoodResult::Applied) {
            request->snapshot = pet_;
            careSave_ = std::move(request);
            motion_.startAction(Action::Feed, nowMs);
            navigation_.setPanel(PanelId::Home);
            panels_.invalidate();
            Serial.println("VPET_FEED queued=1 committed=0");
            return;
        }
        Serial.printf("VPET_FEED result=%u committed=%u hunger=%d energy=%d mood=%d\n",
            static_cast<unsigned>(result),0U,pet_.hunger(),pet_.energy(),pet_.happiness());
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
    auto request=prepareSave(CareKind::Light,PanelId::Rest,0);
    if (!request) return;
    if (pet_.sleep.asleep) pet_.sleep.stop();
    else pet_.sleep.start(explorationClock_.trusted(calendarNow()) ? calendarNow() : 0,pet_.dna()[3]);
    request->snapshot=pet_;
    careSave_=std::move(request);
    if (pet_.sleep.asleep) motion_.startAction(Action::Rest,nowMs);
    else motion_.wake(nowMs);
}

void App::activate(uint32_t nowMs) {
    if (pet_.sleep.asleep) {
        if (navigation_.menuIndex()==5) navigation_.setPanel(PanelId::Rest);
        return;
    }
    if(navigation_.menuIndex()==3 || pet_.exploration.away()) {
        openExploration();
        return;
    }
    if (pet_.dead()) {
        if (collection_ && collection_->enabled()) {
            collection_->setPreview(pet_); collection_->open(); navigation_.setPanel(PanelId::Collection); return;
        }
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

void App::drawHome(uint32_t nowMs) {
    panels_.invalidate();
    renderer_.draw({pet_,motion_,navigation_.menuIndex(),nowMs,
        languageIsSpanish(settings_.language.c_str()),minuteOfDay(),
        !pet_.dead() && !pet_.injured() && !pet_.cold() && pet_.sleep.tired(pet_.energy(),pet_.dna()[3],
            explorationClock_.trusted(calendarNow()) ? minuteOfDay() : -1)});
}

std::unique_ptr<App::CareSave> App::prepareSave(CareKind kind, PanelId origin, uint8_t index) {
    std::unique_ptr<CareSave> request(new (std::nothrow) CareSave);
    if (!request || !saveTask_) {
        Serial.println("VPET_CARE_QUEUE rejected=memory");
        panels_.drawStorageError(settings_.language.c_str());
        return nullptr;
    }
    request->before=pet_;
    request->settings=settings_;
    request->collection=collection_ && collection_->enabled();
    request->kind=kind; request->origin=origin; request->originIndex=index;
    return request;
}

void App::drawPendingCare(uint32_t nowMs) {
    if (navigation_.panel()==PanelId::Home) drawHome(nowMs);
    else {
        // Do not query backup/Collection storage while the writer owns it.
        panels_.draw(navigation_,pet_,bluetooth_.status(),dateMenu_,settings_.language.c_str(),
            settings_.soundEnabled,false,SpeciesId::Egg,nowMs);
    }
}

void App::rollbackCare(uint32_t nowMs) {
    pet_=careSave_->before;
    motion_.cancelAction(nowMs);
    if (pet_.sleep.asleep) motion_.startAction(Action::Rest,nowMs);
    navigation_.setPanel(careSave_->origin,careSave_->originIndex);
    panels_.invalidate(); renderer_.invalidate();
}

bool App::prepareCare(uint32_t nowMs, bool& needsSave) {
    const uint32_t rawElapsed=nowMs-lastTickMs_;
    if (rawElapsed>UINT32_MAX-deferredCareMs_) {
        storageReady_=false; panels_.drawStorageError(settings_.language.c_str()); return false;
    }
    if (collection_ && !collection_->accumulate(rawElapsed,pet_.cold())) {
        savePending_=true;
        panels_.drawStorageError(settings_.language.c_str());
        return false;
    }
    const uint32_t elapsed=rawElapsed+deferredCareMs_;
    deferredCareMs_=0;
    lastTickMs_=nowMs;
    if (pet_.cold() || pet_.exploration.away()) {
        pet_.pauseCareClock(elapsed);
        motion_.alignClock(nowMs);
        if (pet_.cold()) eggStartedMs_+=elapsed;
        return true;
    }
    const bool wasDead=pet_.dead(), sleeping=pet_.sleep.asleep;
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
            needsSave=complete || pet_.sleep.elapsed/300!=checkpoint;
        }
    }
    needsSave=needsSave || pet_.dead()!=wasDead;
    if (!pet_.sleep.asleep) {
        const auto call=pet_.updateCall(nowMs,kCareTimeScale,clockHour(),false,false);
        needsSave=needsSave || call==CallUpdate::Missed;
        if (!pet_.dead() && motion_.state()!=MotionState::Evolution && evolution_.evolve(pet_,kCareTimeScale)) {
            motion_.setSpecies(pet_.species()); motion_.startEvolution(nowMs);
            needsSave=true;
        }
    }
    return true;
}

void App::writeCare(void* context) {
    auto& app = *static_cast<App*>(context);
    auto& job = *app.careSave_;
    const uint32_t started = millis();
    // Only this task may access persistence until the completion barrier.
    job.committed = job.collection ? app.collection_->saveCare(job.snapshot,job.settings)
        : app.settingsStore_.save(static_cast<const PetState&>(job.snapshot),job.settings);
    job.settled = job.committed && (job.collection ? app.collection_->settleCare()
        : app.settingsStore_.recoverPending());
    job.durationMs = millis()-started;
#ifdef ARDUINO
    job.stackFreeBytes = uxTaskGetStackHighWaterMark(nullptr);
    job.heapMin = ESP.getMinFreeHeap();
#endif
}

void App::submitCare(uint32_t nowMs) {
    if (!careSave_ || careSave_->started) return;
    if (progressMode_) {
        progressSave_->before=careSave_->before;
        progressSave_->origin=ProgressOrigin::Care;
        persistActive();
        careSave_.reset();
        return;
    }
    careSave_->started = true;
    if (!saveTask_->start(writeCare,this)) {
        const bool checkpoint=careSave_->careCheckpoint;
        rollbackCare(nowMs);
        careSave_.reset();
        if (checkpoint) {
            savePending_=careRecovery_=true;
            lastSaveAttemptMs_=nowMs;
        }
        Serial.println("VPET_CARE_QUEUE rejected=executor");
        panels_.drawStorageError(settings_.language.c_str());
        return;
    }
    // Also handles an executor that completes before start() returns.
    if (saveTask_->finished()) pollCare(nowMs,InputEvent::None);
}

void App::pollCare(uint32_t nowMs, InputEvent event) {
    if (event==InputEvent::Back || (event==InputEvent::Action &&
        navigation_.panel()==PanelId::Inventory && navigation_.panelIndex()==6)) {
        navigation_.setPanel(PanelId::Home);
        careSave_->origin=PanelId::Home;
        careSave_->originIndex=0;
        panels_.invalidate();
        drawHome(nowMs);
    }
    if (saveTask_->finished()) {
        const bool committed = careSave_->committed;
        const bool settled = careSave_->settled;
        const uint32_t duration = careSave_->durationMs;
        const uint32_t stack = careSave_->stackFreeBytes, heap = careSave_->heapMin;
        const auto kind=careSave_->kind;
        if (!committed) {
            rollbackCare(nowMs);
        }
        saveTask_->reset();
        careSave_.reset();
        savePending_ = !settled;
        careRecovery_ = !settled;
        lastSaveAttemptMs_ = nowMs;
        Serial.printf(kind==CareKind::Food ? "VPET_FEED result=0 committed=%u hunger=%d energy=%d mood=%d\n" :
            "VPET_CARE result=0 committed=%u hunger=%d energy=%d mood=%d\n",
            committed?1U:0U,pet_.hunger(),pet_.energy(),pet_.happiness());
        Serial.printf(kind==CareKind::Food ? "VPET_FEED_SAVE duration_ms=%u settled=%u stack_free_bytes=%u heap_min=%u\n" :
            "VPET_CARE_SAVE duration_ms=%u settled=%u stack_free_bytes=%u heap_min=%u\n",
            duration,settled?1U:0U,stack,heap);
        if (!settled) panels_.drawStorageError(settings_.language.c_str());
        return; // Never reinterpret an input pressed while saving as a new action.
    }
    if (event != InputEvent::None) lastInteractionMs_ = nowMs;
    if (event == InputEvent::Next) {
        if (navigation_.panel()==PanelId::Inventory)
            navigation_.setPanelIndex(pet_.nextVisibleInventoryIndex(navigation_.panelIndex()));
        else navigation_.dispatch(event);
    }
    motion_.tick(nowMs);
    motion_.consumeActionCompleted(); // Nutrition was applied once before queuing.
    if (event != InputEvent::None || (navigation_.panel()==PanelId::Home && nowMs-lastRenderMs_ >= 33)) {
        lastRenderMs_ = nowMs;
        drawPendingCare(nowMs);
    }
}

void App::writeTraining(void* context) {
    auto& app = *static_cast<App*>(context);
    auto& job = *app.trainingSave_;
    const uint32_t started = millis();
    // Persistence is exclusively owned by this writer until finished().
    job.committed = job.collection ? app.collection_->saveExperience(job.snapshot,job.settings,&job.experience,1)
        : app.settingsStore_.save(static_cast<const PetState&>(job.snapshot),job.settings);
    job.settled = job.committed && (job.collection ? !app.collection_->failed()
        : app.settingsStore_.recoverPending());
    job.durationMs = millis()-started;
#ifdef ARDUINO
    job.stackFreeBytes = uxTaskGetStackHighWaterMark(nullptr);
    job.heapMin = ESP.getMinFreeHeap();
#endif
}

void App::submitTraining(uint32_t nowMs, const RuntimeExperience& experience) {
    if (progressMode_) {
        progressSave_->origin=ProgressOrigin::Training;
        persistExperience(&experience,1);
        training_.dirty=false;
        training_.saving=false;
        renderer_.invalidate();
        panels_.drawTraining(training_,pet_,nowMs,settings_.language.c_str());
        lastRenderMs_=nowMs;
        return;
    }
    std::unique_ptr<TrainingSave> job(new (std::nothrow) TrainingSave);
    training_.dirty = false;
    if (job) {
        job->snapshot = pet_;
        job->settings = settings_;
        job->experience = experience;
        job->collection = collection_ && collection_->enabled();
        trainingSave_ = std::move(job);
        training_.saving = true;
        renderer_.invalidate();
        panels_.drawTraining(training_,pet_,nowMs,settings_.language.c_str());
        lastRenderMs_ = nowMs;
        trainingSave_->started = saveTask_->start(writeTraining,this);
        if (trainingSave_->started) {
            if (saveTask_->finished()) pollTraining(nowMs);
            return;
        }
        trainingSave_.reset();
    }
    training_.rollbackFromSnapshot(pet_);
    Serial.println("VPET_TRAINING_QUEUE rejected=resources");
    panels_.drawTraining(training_,pet_,nowMs,settings_.language.c_str());
}

void App::pollTraining(uint32_t nowMs) {
    lastInteractionMs_ = nowMs;
    if (!saveTask_->finished()) {
        if (nowMs-lastRenderMs_ >= 33) {
            trainingSave_->maxFrameGapMs = std::max(trainingSave_->maxFrameGapMs,nowMs-lastRenderMs_);
            ++trainingSave_->frames;
            lastRenderMs_ = nowMs;
            renderer_.invalidate();
            panels_.drawTraining(training_,pet_,nowMs,settings_.language.c_str());
        }
        return;
    }
    // finished() is the acquire barrier for every field written by the worker.
    const bool committed = trainingSave_->committed, settled = trainingSave_->settled;
    const uint32_t duration = trainingSave_->durationMs;
    const uint32_t stack = trainingSave_->stackFreeBytes, heap = trainingSave_->heapMin;
    const uint32_t frames = trainingSave_->frames;
    const uint32_t gap = std::max(trainingSave_->maxFrameGapMs,nowMs-lastRenderMs_);
    saveTask_->reset();
    trainingSave_.reset();
    training_.saving = false;
    savePending_ = !settled;
    if (!committed) {
        training_.rollbackFromSnapshot(pet_);
        recoverRejectedExperience("training");
    } else training_.needsRollback = false;
    lastSaveAttemptMs_ = nowMs;
    motion_.alignClock(nowMs);
    renderer_.invalidate();
    panels_.invalidate();
    lastRenderMs_ = nowMs;
    if (savePending_) panels_.drawStorageError(settings_.language.c_str());
    else panels_.drawTraining(training_,pet_,nowMs,settings_.language.c_str());
    Serial.printf("VPET_TRAINING_SAVE duration_ms=%u committed=%u pending=%u stack_free_bytes=%u heap_min=%u frames=%u max_frame_gap_ms=%u\n",
        duration,committed?1U:0U,savePending_?1U:0U,stack,heap,frames,gap);
}

App::ProgressView App::progressView() const {
    ProgressView view;
    view.navigation=navigation_; view.date=dateMenu_; view.training=training_;
    view.practice=practice_; view.exploration=exploration_;
    view.trainingActive=trainingActive_; view.practicing=practicing_;
    view.clockStep=explorationClockStep_;
    return view;
}

void App::restoreProgressView(const ProgressView& view) {
    navigation_=view.navigation; dateMenu_=view.date; training_=view.training;
    practice_=view.practice; exploration_=view.exploration;
    trainingActive_=view.trainingActive; practicing_=view.practicing;
    explorationClockStep_=view.clockStep;
}

void App::prepareProgress() {
    auto& job=*progressSave_;
    job.kind=ProgressKind::None; job.origin=ProgressOrigin::State;
    job.before=pet_; job.beforeSettings=settings_; job.beforeView=progressView();
    job.eventCount=0;
    job.started=false; job.committed=false; job.recovered=true; job.cancelled=false;
    job.close=false; job.changedActive=false; job.setClock=false; job.clockApplied=true;
    job.dirty=false;
    job.durationMs=job.stackFreeBytes=job.heapMin=0;
}

bool App::interruptProgress(void* context) {
    return static_cast<App*>(context)->progressInterrupt_.load(std::memory_order_acquire);
}

void App::writeProgress(void* context) {
    auto& app=*static_cast<App*>(context);
    auto& job=*app.progressSave_;
    const uint32_t started=millis();
    // The worker owns CollectionPanel and LearningRuntime until finished().
    switch (job.kind) {
        case ProgressKind::Receipt:
            job.committed=job.eventCount ?
                app.collection_->saveExperience(job.snapshot,job.settings,job.events,job.eventCount) :
                app.collection_->saveProgress(job.snapshot,job.settings);
            job.recovered=job.committed ? app.collection_->settleCare() : app.collection_->recoverRejectedSave();
            break;
        case ProgressKind::Checkpoint:
            job.committed=app.collection_->checkpoint(job.snapshot,job.settings);
            job.cancelled=!job.committed && app.collection_->interrupted();
            if (!job.committed && !job.cancelled) job.recovered=app.collection_->recoverRejectedSave();
            break;
        case ProgressKind::CollectionInput:
            job.close=app.collection_->input(job.input,job.snapshot,job.settings,job.guard);
            job.changedActive=app.collection_->changedActive();
            job.committed=!app.collection_->failed();
            if (!job.committed) job.recovered=app.collection_->recoverRejectedSave();
            break;
        case ProgressKind::Reload:
            job.committed=app.collection_->load(job.snapshot,job.settings)==CollectionLoad::Loaded;
            job.changedActive=job.committed;
            job.recovered=job.committed;
            break;
        case ProgressKind::Recovery:
            job.committed=app.collection_->recoverRejectedSave();
            job.recovered=job.committed;
            break;
        case ProgressKind::Settlement:
            // The receipt was accepted already. Resolve it without applying or
            // submitting its effects/events again, even across repeated failures.
            job.committed=true;
            job.recovered=app.collection_->settleCare();
            break;
        case ProgressKind::None: break;
    }
    if (job.committed && job.setClock) {
        const timeval clock={static_cast<time_t>(job.epoch),0};
        job.clockApplied=settimeofday(&clock,nullptr)==0;
    }
    job.dirty=app.collection_->dirty();
    job.durationMs=millis()-started;
#ifdef ARDUINO
    job.stackFreeBytes=uxTaskGetStackHighWaterMark(nullptr);
    job.heapMin=ESP.getMinFreeHeap();
#endif
}

void App::startProgress(uint32_t nowMs) {
    auto& job=*progressSave_;
    job.snapshot=pet_; job.settings=settings_; job.view=progressView();
    if (progressSafeHome_) {
        lastRenderMs_=nowMs-33;
        drawProgress(nowMs);
    } else if (progressWarning_ && nowMs-progressWarningStartedMs_<2000)
        panels_.drawStorageError(settings_.language.c_str());
    progressInterrupt_.store(false,std::memory_order_release);
    job.started=true;
    if (!saveTask_->start(writeProgress,this)) {
        job.started=false;
        finishProgress(nowMs);
        Serial.println("VPET_PROGRESS_QUEUE rejected=executor");
    }
}

void App::finishProgress(uint32_t nowMs) {
    auto& job=*progressSave_;
    // Only the acquire barrier permits reading worker output or Collection again.
    if (job.started) saveTask_->reset();
    restoreProgressView(job.view);
    if (!job.committed && !job.cancelled && job.kind==ProgressKind::Receipt) {
        pet_=job.before;
        settings_=job.beforeSettings;
        bluetooth_.setEnabled(settings_.bluetoothEnabled);
        motion_.cancelAction(nowMs);
        if (pet_.sleep.asleep) motion_.startAction(Action::Rest,nowMs);
        if (job.origin==ProgressOrigin::Training) {
            training_.rollbackFromSnapshot(pet_);
            trainingActive_=true;
        } else if (job.origin==ProgressOrigin::Practice) {
            practice_.finishSave(pet_,job.before,job.beforeView.practice,false);
            practicing_=true;
        } else if (job.origin==ProgressOrigin::Exploration) {
            exploration_=job.beforeView.exploration;
            exploration_.saveFailed=true;
        } else if (job.origin==ProgressOrigin::Care) {
            navigation_=job.beforeView.navigation;
        }
        warnProgress(nowMs);
    }
    if (job.committed) {
        if (job.kind==ProgressKind::Receipt) {
            if (job.origin==ProgressOrigin::Training) training_.needsRollback=false;
            if (!job.before.sleep.asleep && pet_.sleep.asleep) sleepCheckpoint_=true;
        }
        if (job.kind==ProgressKind::CollectionInput || job.kind==ProgressKind::Reload) {
            pet_=job.snapshot; settings_=job.settings;
            if (job.changedActive) activeChanged(nowMs);
            if (job.close) navigation_.setPanel(PanelId::Options,option_menu::collection);
            bluetooth_.setEnabled(settings_.bluetoothEnabled);
        }
        if (job.setClock) {
            if (job.clockApplied) explorationClock_.adjusted(job.epoch);
            else warnProgress(nowMs);
        }
    }
    progressSettlement_=job.committed && !job.recovered;
    savePending_=!job.recovered;
    if (job.kind==ProgressKind::Checkpoint) lastProgressCheckpointMs_=nowMs;
    lastSaveAttemptMs_=nowMs;
    const bool failed=!job.committed && !job.cancelled;
    Serial.printf("VPET_PROGRESS_SAVE kind=%u duration_ms=%u committed=%u settled=%u cancelled=%u dirty=%u stack_free_bytes=%u heap_min=%u queue=%u max_queue_delay_ms=%u max_input_to_draw_ms=%u\n",
        unsigned(job.kind),job.durationMs,job.committed?1U:0U,job.recovered?1U:0U,
        job.cancelled?1U:0U,job.dirty?1U:0U,job.stackFreeBytes,job.heapMin,
        unsigned(progressInputCount_),progressMaxQueueDelayMs_,progressMaxDrawLatencyMs_);
    job.started=false; job.kind=ProgressKind::None;
    progressInterrupt_.store(false,std::memory_order_release);
    if (failed) {
        Serial.println("VPET_PROGRESS_REJECTED");
        warnProgress(nowMs);
    }
    if (savePending_) warnProgress(nowMs);
    panels_.invalidate(); renderer_.invalidate();
    lastRenderMs_=nowMs-1000;
}

bool App::queueProgressInput(InputEvent event, uint32_t nowMs, bool home) {
    if (event==InputEvent::None) return true;
    if (progressInputCount_==kProgressInputCapacity) {
        progressInputOverflow_=true;
        Serial.println("VPET_PROGRESS_INPUT rejected=capacity");
        return false;
    }
    progressInputs_[(progressInputHead_+progressInputCount_)%kProgressInputCapacity]={event,home,nowMs};
    ++progressInputCount_;
    return true;
}

void App::previewProgressInput(InputEvent event, uint32_t nowMs) {
    // Presentation is speculative. Restore job.view before ordered replay; these
    // paths neither mutate PetState nor call Collection/LearningRuntime.
    if (trainingActive_) {
        if (training_.state==TrainingSession::State::Result)
            training_.input(pet_,event,nowMs);
        return;
    }
    if (practicing_) {
        if (event==InputEvent::Next) practice_.cursor=(practice_.cursor+1)%practice_.count(pet_);
        return;
    }
    if (event==InputEvent::Next) {
        if (navigation_.panel()==PanelId::Inventory)
            navigation_.setPanelIndex(pet_.nextVisibleInventoryIndex(navigation_.panelIndex()));
        else if (navigation_.panel()==PanelId::DateTime) dateMenu_.next();
        else if (navigation_.panel()!=PanelId::Collection) navigation_.dispatch(event);
    } else if (event==InputEvent::Back && navigation_.panel()!=PanelId::Collection) {
        navigation_.setPanel(PanelId::Home);
    }
}

void App::drawProgress(uint32_t nowMs) {
    const auto kind=progressSave_->kind;
    const bool filesystemWork=kind==ProgressKind::Checkpoint || kind==ProgressKind::CollectionInput ||
        kind==ProgressKind::Reload || kind==ProgressKind::Recovery;
    if (progressSave_->started && filesystemWork) return;
    if (progressSafeHome_) {
        progressWarning_=false;
        if (nowMs-lastRenderMs_>=33) {
            lastRenderMs_=nowMs;
            drawHome(nowMs);
            progressPresented();
        }
        return;
    }
    if (progressWarning_ && nowMs-progressWarningStartedMs_<2000) {
        panels_.drawStorageError(settings_.language.c_str());
        progressPresented();
        return;
    }
    progressWarning_=false;
    // Full filesystem work reuses the already-presented framebuffer. Even a
    // redraw of the same screen could otherwise read LittleFS assets.
    if (filesystemWork) return;
    if (nowMs-lastRenderMs_<33) return;
    lastRenderMs_=nowMs;
    if (trainingActive_) panels_.drawTraining(training_,pet_,nowMs,settings_.language.c_str());
    else if (practicing_) panels_.drawPractice(practice_,pet_,nowMs,settings_.language.c_str());
    else if (navigation_.panel()==PanelId::Exploration)
        panels_.drawExploration(exploration_,pet_,calendarNow(),nowMs,settings_.language.c_str());
    else if (navigation_.panel()==PanelId::Home) drawHome(nowMs);
    else if (navigation_.panel()!=PanelId::Collection)
        panels_.draw(navigation_,pet_,bluetooth_.status(),dateMenu_,settings_.language.c_str(),
            settings_.soundEnabled,false,SpeciesId::Egg,nowMs);
    else return;
    progressPresented();
}

void App::progressPresented() {
    if (!progressVisibleInput_) return;
    const uint32_t latency=millis()-progressVisibleInputMs_;
    progressMaxDrawLatencyMs_=std::max(progressMaxDrawLatencyMs_,latency);
    progressVisibleInput_=false;
    Serial.printf("VPET_PROGRESS_PRESENT input_to_draw_ms=%u queued=%u\n",
        latency,unsigned(progressInputCount_));
}

void App::warnProgress(uint32_t nowMs) {
    if (progressSafeHome_) return;
    progressWarning_=true;
    progressWarningStartedMs_=nowMs;
    panels_.drawStorageError(settings_.language.c_str());
}

void App::closeProgressToHome() {
    trainingActive_=practicing_=false;
    explorationClockStep_=0;
    navigation_.setPanel(PanelId::Home);
    panels_.invalidate(); renderer_.invalidate();
    progressSafeHome_=false;
}

void App::tickProgress(uint32_t nowMs, InputEvent event) {
    auto& job=*progressSave_;
    if (event!=InputEvent::None) {
        lastInteractionMs_=nowMs;
        sleepCheckpoint_=false;
        if (job.started && job.kind==ProgressKind::Checkpoint)
            progressInterrupt_.store(true,std::memory_order_release);
        const bool home=savePending_ && event==InputEvent::Back;
        if (home) {
            progressSafeHome_=true;
            progressWarning_=false;
            lastRenderMs_=nowMs-33;
        }
        if (queueProgressInput(event,nowMs,home)) {
            if (!progressVisibleInput_) { progressVisibleInput_=true; progressVisibleInputMs_=nowMs; }
            if (job.started) previewProgressInput(event,nowMs);
        }
    }
    if (job.started) {
        if (!saveTask_->finished()) {
            motion_.tick(nowMs);
            drawProgress(nowMs);
            return;
        }
        finishProgress(nowMs);
        if (savePending_ && event==InputEvent::Back) {
            progressSafeHome_=true;
            progressWarning_=false;
            if (progressInputCount_) {
                auto& queued=progressInputs_[(progressInputHead_+progressInputCount_-1)%kProgressInputCapacity];
                if (queued.event==InputEvent::Back && queued.queuedAtMs==nowMs) queued.home=true;
            }
        }
    }
    if (progressSafeHome_ && !progressInputCount_) closeProgressToHome();
    if (savePending_) {
        if (nowMs-lastSaveAttemptMs_>=1000) {
            prepareProgress();
            job.kind=progressSettlement_ ? ProgressKind::Settlement : ProgressKind::Recovery;
            startProgress(nowMs);
        }
        drawProgress(nowMs);
        return;
    }
    // Reserve the worst-case eight learning events before any new mutation.
    // Capacity pressure runs maintenance on the same worker, never on tick().
    if (collection_->progressCount()>64-8) {
        prepareProgress(); job.kind=ProgressKind::Checkpoint; startProgress(nowMs);
        return;
    }
    bool processed=false;
    do {
        InputEvent next=InputEvent::None;
        if (progressInputCount_) {
            const auto queued=progressInputs_[progressInputHead_];
            if (queued.home) closeProgressToHome();
            else next=queued.event;
            progressMaxQueueDelayMs_=std::max(progressMaxQueueDelayMs_,nowMs-queued.queuedAtMs);
            progressInputHead_=(progressInputHead_+1)%kProgressInputCapacity;
            --progressInputCount_;
        } else if (processed) break;
        prepareProgress();
        const uint32_t previousRender=lastRenderMs_;
        tickGameplay(nowMs,next);
        if (lastRenderMs_!=previousRender && lastRenderMs_==nowMs) progressPresented();
        processed=true;
        if (job.kind!=ProgressKind::None) {
            startProgress(nowMs);
            if (job.started) {
                for (uint8_t i=0;i<progressInputCount_;++i)
                    previewProgressInput(progressInputs_[(progressInputHead_+i)%kProgressInputCapacity].event,nowMs);
            }
            return;
        }
    } while (progressInputCount_);
    if (progressInputOverflow_) {
        warnProgress(nowMs);
        progressInputOverflow_=false;
    }
    if (progressWarning_) drawProgress(nowMs);
    if (collection_->dirty() && (sleepCheckpoint_ ||
        (nowMs-lastInteractionMs_>=5000 && nowMs-lastProgressCheckpointMs_>=5000))) {
        prepareProgress(); job.kind=ProgressKind::Checkpoint;
        sleepCheckpoint_=false;
        startProgress(nowMs);
    }
}

void App::tick(uint32_t nowMs, InputEvent event) {
    if (progressMode_) tickProgress(nowMs,event);
    else tickGameplay(nowMs,event);
}

void App::tickGameplay(uint32_t nowMs, InputEvent event) {
    if (trainingSave_) {
        pollTraining(nowMs);
        return; // Inputs received during a save cannot become a second action.
    }
    if (careSave_) {
        pollCare(nowMs,event);
        return;
    }
    if (event==InputEvent::Action && navigation_.panel()==PanelId::Inventory &&
        navigation_.panelIndex()==6) {
        navigation_.setPanel(PanelId::Home);
        if (savePending_) savePendingHome_=true;
        lastInteractionMs_=nowMs;
        drawHome(nowMs);
        return;
    }
    if (event==InputEvent::Action && navigation_.panel()==PanelId::Feeding) {
        Serial.printf("VPET_FEED input index=%u hunger=%d energy=%d mood=%d paused=%u asleep=%u dead=%u away=%u pending=%u storage=%u saving=%u training=%u practice=%u\n",
            static_cast<unsigned>(navigation_.panelIndex()),pet_.hunger(),pet_.energy(),pet_.happiness(),
            pet_.cold()?1U:0U,pet_.sleep.asleep?1U:0U,pet_.dead()?1U:0U,pet_.exploration.away()?1U:0U,
            static_cast<unsigned>(pet_.pendingAction()),storageReady_?1U:0U,savePending_?1U:0U,
            trainingActive_?1U:0U,practicing_?1U:0U);
    }
    if (!storageReady_) {
        if (nowMs-lastRenderMs_>=1000) begin(nowMs);
        return;
    }
    if (savePending_ && rejectedExperienceRecovery_ && collection_ && collection_->enabled() &&
        nowMs-lastSaveAttemptMs_>=1000 && collection_->recoverRejectedSave()) {
        savePending_=false;
        rejectedExperienceRecovery_=false;
        savePendingHome_=false;
        panels_.invalidate();
    }
    if (savePending_) {
        if (event==InputEvent::Back) {
            navigation_.setPanel(PanelId::Home);
            savePendingHome_=true;
            panels_.invalidate();
        }
        if (careRecovery_) {
            motion_.alignClock(nowMs);
            if (nowMs-lastSaveAttemptMs_>=1000) {
                const bool compact=collection_ && collection_->enabled() && collection_->compactCare();
                const bool recovered=compact ? collection_->recoverCare(pet_,settings_) : saveState();
                if (recovered) { careRecovery_=false; savePending_=false; savePendingHome_=false; }
                lastSaveAttemptMs_=nowMs;
            }
            if (savePendingHome_ && (event!=InputEvent::None || nowMs-lastRenderMs_>=33)) {
                lastRenderMs_=nowMs; drawHome(nowMs);
            }
            return; // Keep lastTickMs_: catch up the pending interval after recovery.
        }
        if(pet_.exploration.away() || pet_.sleep.asleep) pet_.pauseCareClock(nowMs-lastTickMs_);
        lastTickMs_ = nowMs;
        motion_.alignClock(nowMs);
        if (nowMs - lastSaveAttemptMs_ >= 1000) saveState();
        if (savePendingHome_ && (event!=InputEvent::None || nowMs-lastRenderMs_>=33)) {
            lastRenderMs_=nowMs; drawHome(nowMs);
        }
        return;
    }
    // Present care inputs before any due storage checkpoint. Do not interrupt
    // training/practice or allow a second transaction while the writer is active.
    const auto inputPanel=navigation_.panel();
    const bool careInput=!trainingActive_ && !practicing_ && event==InputEvent::Action &&
        ((inputPanel==PanelId::Feeding && navigation_.panelIndex()<2) ||
         inputPanel==PanelId::Inventory || (inputPanel==PanelId::Rest && navigation_.panelIndex()==0));
    if (careInput) {
        lastInteractionMs_=nowMs;
        const uint32_t presentationStarted=millis();
        bool needsCareSave=false;
        if (!prepareCare(nowMs,needsCareSave)) return;
        handlePanelInput(nowMs,event);
        if (careSave_) {
            careSave_->careCheckpoint=needsCareSave;
            if (explorationClock_.trusted(calendarNow())) pet_.exploration.clockCheckpoint=calendarNow();
            careSave_->snapshot=pet_;
            if (careSave_->kind!=CareKind::Food)
                Serial.printf("VPET_CARE queued=1 kind=%u index=%u committed=0\n",
                    static_cast<unsigned>(careSave_->kind),static_cast<unsigned>(careSave_->originIndex));
            lastRenderMs_=nowMs;
            drawPendingCare(nowMs);
            Serial.printf(careSave_->kind==CareKind::Food ? "VPET_FEED_PRESENT handler_to_frame_ms=%u\n" :
                "VPET_CARE_PRESENT handler_to_frame_ms=%u\n",millis()-presentationStarted);
            submitCare(nowMs);
        } else if (needsCareSave) saveState();
        return;
    }
    const uint32_t rawElapsed = nowMs - lastTickMs_;
    if (rawElapsed>UINT32_MAX-deferredCareMs_) {
        storageReady_=false; panels_.drawStorageError(settings_.language.c_str()); return;
    }
    const uint32_t elapsed=rawElapsed+deferredCareMs_;
    lastTickMs_ = nowMs;
    if (collection_ && !collection_->advance(rawElapsed,pet_.cold())) {
        // Collection already owns this delta, but pet/sleep processing has not
        // run. Catch it up once, without crediting Collection elapsed again.
        deferredCareMs_=elapsed;
        savePending_=true;
        careRecovery_=collection_->enabled() && collection_->compactCare();
        lastSaveAttemptMs_=nowMs;
        panels_.drawStorageError(settings_.language.c_str());
        return;
    }
    deferredCareMs_=0;
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
        practice_.battle.player.autoSelector=autoChoice;
        practice_.battle.player.autoContext=this;
        practice_.tick(pet_, nowMs);
        if (!practice_.battle.result || beforeSession.battle.result)
            practicing_ = practice_.input(pet_, event, nowMs);
        if (practice_.dirty) {
            RuntimeExperience experiences[techniques::kCount]; size_t count=0;
            if (practice_.awarded && !beforeSession.awarded) {
                const int survival=100*practice_.battle.player.hp/std::max(1,practice_.battle.player.maxHp);
                const int outcome=practice_.battle.result==1?50:-50;
                for (int i=0;i<techniques::kCount;++i) if (practice_.battle.uses[i]) {
                    const int score=outcome+survival/4-practice_.battle.uses[i]*(i==2?4:1);
                    experiences[count++]={1,0,static_cast<uint8_t>(i),std::max(-100,std::min(100,score))};
                }
            } else if (beforeSession.page==PracticeSession::Page::Detail && beforeSession.cursor==0 &&
                       beforeSession.technique<techniques::kCount) {
                const auto technique=beforeSession.technique;
                const int delta=int(pet_.practice.mastery[technique])-beforePet.practice.mastery[technique];
                experiences[count++]={1,1,technique,std::max(-100,std::min(100,10+delta*10))};
            }
            const bool committed=persistExperience(experiences,count);
            if (progressMode_) progressSave_->origin=ProgressOrigin::Practice;
            practice_.finishSave(pet_,beforePet,beforeSession,committed);
            if (!committed) {
                practicing_=true;
                const bool recovered=recoverRejectedExperience("battle");
                Serial.printf("VPET_BATTLE_SAVE_REJECTED recovered=%u result=%d retry=%u\n",
                    recovered?1U:0U,practice_.battle.result,practice_.pendingAward?1U:0U);
            }
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
            const int score=int(training_.lastSummary.evAdded)*10-training_.lastSummary.energyCharged;
            const RuntimeExperience experience{0,0,trainingIndexFor(training_.chosenStat),std::max(-100,std::min(100,score))};
            submitTraining(nowMs,experience);
            return;
        }
        if (savePending_) return;
        if (!stillActive) {
            trainingActive_ = false;
            panels_.invalidate();
            motion_.alignClock(nowMs);
        } else if (event != InputEvent::None || nowMs - lastRenderMs_ >= 33) {
            lastRenderMs_ = nowMs;
            renderer_.invalidate();
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
    } else if (pet_.cold()) {
        pet_.pauseCareClock(elapsed);
        motion_.alignClock(nowMs);
        eggStartedMs_ += elapsed;
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
    if (pet_.dead() != wasDead || (!pet_.cold() &&
        (pet_.injured() || (!pet_.sleep.asleep &&
         (pet_.hungerCriticalMs() || pet_.energyCriticalMs()))) &&
        nowMs - lastInjuryCheckpointMs_ >= 60000)) {
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
        const bool collectionEgg=collection_ && collection_->enabled() && collection_->timedEgg();
        const bool readyToHatch=collectionEgg ? collection_->hatchReady() : nowMs-eggStartedMs_>=kEggLifeMs;
        if (!collectionEgg && motion_.state() != MotionState::Hatch && nowMs - eggStartedMs_ >= kEggLifeMs - kEggHatchMs) {
            motion_.startHatch(nowMs);
        }
        if (readyToHatch) {
            pet_.evolveTo(SpeciesId::Baby);
            if (!(collection_ && collection_->enabled()) && !pet_.hasDna()) pet_.rollDna(esp_random() ^ nowMs);
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

    navigation_.setCurrentSpecies(pet_.species());
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
        panel == PanelId::Options || panel == PanelId::Collection) {
        intervalMs = panel == PanelId::Status ? 100 : 1000;
    }
    if (event != InputEvent::None || nowMs - lastRenderMs_ >= intervalMs) {
        lastRenderMs_ = nowMs;
        if (navigation_.panel()==PanelId::Collection && collection_) {
            renderer_.invalidate(); panels_.invalidate(); collection_->draw(settings_.language.c_str());
        } else if (navigation_.panel() == PanelId::Exploration) {
            renderer_.invalidate();
            panels_.drawExploration(exploration_,pet_,calendarNow(),nowMs,settings_.language.c_str());
        } else if (navigation_.panel() == PanelId::Home && pet_.exploration.away()) {
            renderer_.invalidate();
            ExplorationSession home;
            home.open(pet_,explorationClock_.trusted(calendarNow()));
            panels_.drawExploration(home,pet_,calendarNow(),nowMs,settings_.language.c_str(),true,navigation_.menuIndex());
        } else if (navigation_.panel() == PanelId::Home) {
            drawHome(nowMs);
        } else {
            panels_.draw(
                navigation_,
                pet_,
                bluetooth_.status(),
                dateMenu_,
                settings_.language.c_str(),
                settings_.soundEnabled,
                collection_ && collection_->enabled() ? false : settingsStore_.hasBackup(),
                collection_ && collection_->enabled() ? SpeciesId::Egg : settingsStore_.backupSpecies(),
                nowMs
            );
        }
    }
    // Present the first frame before waking the writer, which may contend with
    // LittleFS reads or briefly stall both cores during flash operations.
    submitCare(nowMs);
}

}  // namespace vpet
