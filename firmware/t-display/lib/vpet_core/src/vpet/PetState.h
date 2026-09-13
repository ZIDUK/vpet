#pragma once

#include <stdint.h>

namespace vpet {

// Keep the original numeric values stable because they are persisted in NVS.
enum class SpeciesId : uint8_t { Rookie = 0, Champion = 1, Ultimate = 2, Egg = 3, Baby = 4 };
enum class Action : uint8_t { None, Feed, Training, Battle, Rest };
enum class ItemUseResult : uint8_t { Used, Empty, Blocked, Back };
enum class CallReason : uint8_t { None = 0, Hunger = 1, Strength = 2, Lights = 3 };
enum class CallUpdate : uint8_t { None, Started, Missed };
enum class CombatStat : uint8_t { Hp, Mp, Off, Def, Spd, Brn };
enum class CareEventType : uint8_t {
    Feed = 1,
    Train = 2,
    Battle = 3,
    CallStart = 4,
    CallMiss = 5,
    Sleep = 6,
    Wake = 7,
    Evo = 8,
    DecayZero = 9
};

struct CareEvent {
    uint16_t tRelMin = 0;
    uint8_t type = 0;
    uint8_t value = 0;
};

struct CareSnapshot {
    uint8_t schema;
    uint8_t species;
    uint16_t stageAgeMin;
    uint8_t hunger;
    uint8_t energy;
    uint8_t happiness;
    uint8_t health;
    uint8_t careMistakes;
    uint8_t effort;
    uint8_t meals;
    uint8_t training;
    uint8_t battlesThisForm;
    uint8_t wins;
    uint8_t losses;
    uint8_t callReason;
    uint8_t flags;
    uint8_t reserved[3];
} __attribute__((packed));

class PetState {
public:
    void tick(uint32_t elapsedMs);
    bool beginAction(Action action);
    bool completeAction();
    void evolveTo(SpeciesId species);
    bool forceNextForm();
    void resetToEgg();
    void resetAfterEvolution();
    void restore(SpeciesId species, int hunger, int energy, int happiness, int effort, int health, uint32_t ageSeconds);
    void restoreItems(
        uint8_t meat,
        uint8_t energyItem,
        uint8_t expItem,
        uint8_t ring,
        uint8_t proteinItem = 0,
        uint8_t medkit = 0
    );
    void restoreCare(
        uint32_t stageAgeSeconds,
        uint8_t careMistakes,
        CallReason call,
        int meals,
        int training,
        int battles,
        uint8_t wins,
        uint8_t losses,
        uint8_t weight,
        uint8_t dp,
        uint8_t protein
    );
    ItemUseResult useItem(uint8_t index);
    uint8_t itemCount(uint8_t index) const;
    bool itemVisible(uint8_t index) const;
    uint8_t visibleInventoryCount() const;
    uint8_t inventoryIndexAt(uint8_t visibleSlot) const;
    uint8_t nextVisibleInventoryIndex(uint8_t index) const;
    uint8_t clampVisibleInventoryIndex(uint8_t index) const;
    bool hasDiscovered(SpeciesId species) const;
    CallUpdate updateCall(uint32_t nowMs, uint32_t scale, uint8_t hour = 12, bool asleep = false);
    void noteWake(uint8_t hour);
    void restoreOverfeed(bool usedThisCycle, uint8_t count);
    void restoreInjury(bool injured, uint8_t injuries, bool dead);
    void record(CareEventType type, uint8_t value);
    CareSnapshot snapshot() const;
    void rollDna(uint32_t entropy);
    void restoreDna(const uint8_t dna[4]);
    void restoreEv(const uint8_t ev[6]);
    const uint8_t* dna() const { return dna_; }
    bool hasDna() const;
    uint8_t ivAt(CombatStat stat) const;
    uint8_t evAt(CombatStat stat) const;
    uint8_t combatStat(CombatStat stat) const;

    void setStageAgeSeconds(uint32_t seconds);
    void setCareMistakes(uint8_t value);
    void setBattles(int value);
    void setWins(uint8_t value);
    void setLosses(uint8_t value);
    void setDp(uint8_t value);
    void setBattleRoll(uint8_t roll);
    void setInjured(bool value);
    void setInjuries(uint8_t value);
    void setHealth(int value);
    void setCold(bool value) { cold_ = value; }

    SpeciesId species() const { return species_; }
    int hunger() const { return hunger_; }
    int energy() const { return energy_; }
    int happiness() const { return happiness_; }
    int effort() const { return effort_; }
    int health() const { return health_; }
    int meals() const { return meals_; }
    int trainingSessions() const { return trainingSessions_; }
    int battles() const { return battles_; }
    uint32_t ageSeconds() const { return ageMs_ / 1000; }
    uint32_t stageAgeSeconds() const { return stageAgeMs_ / 1000; }
    uint8_t careMistakes() const { return careMistakes_; }
    CallReason callReason() const { return callReason_; }
    uint8_t wins() const { return wins_; }
    uint8_t losses() const { return losses_; }
    uint8_t weight() const { return weight_; }
    uint8_t dp() const { return dp_; }
    uint8_t protein() const { return protein_; }
    uint8_t overfeeds() const { return overfeeds_; }
    bool overfedThisCycle() const { return overfedThisCycle_; }
    uint8_t effortHearts() const;
    uint8_t hungerHearts() const;
    uint8_t strengthHearts() const;
    bool hasWinRatio() const;
    uint8_t winRatioPercent() const;
    bool injured() const { return injured_; }
    uint8_t injuries() const { return injuries_; }
    bool dead() const { return dead_; }
    bool cold() const { return cold_; }
    bool lastBattleWon() const { return lastBattleWon_; }
    uint8_t careEventCount() const { return eventCount_; }
    uint8_t careEventIndex() const { return eventIndex_; }
    CareEvent careEventAt(uint8_t index) const;
    Action pendingAction() const { return pendingAction_; }

private:
    static int clampStat(int value);
    static uint8_t clampByte(int value, uint8_t maxValue);
    void refreshCallAfterCare();
    CallUpdate startCall(CallReason reason, uint32_t nowMs);
    bool canFeed() const;
    bool canBattle() const;
    void applyFeed(bool fromItem);
    void applyProtein();
    void injure();
    void checkDeath();
    void resolveBattle();
    void gainEv(CombatStat stat, uint8_t amount);

    SpeciesId species_ = SpeciesId::Egg;
    Action pendingAction_ = Action::None;
    int hunger_ = 80;
    int energy_ = 80;
    int happiness_ = 80;
    int effort_ = 0;
    int health_ = 100;
    int meals_ = 0;
    int trainingSessions_ = 0;
    int battles_ = 0;
    uint32_t ageMs_ = 0;
    uint32_t stageAgeMs_ = 0;
    uint32_t decayMs_ = 0;
    uint32_t callStartedMs_ = 0;
    uint8_t careMistakes_ = 0;
    CallReason callReason_ = CallReason::None;
    bool lightsHandledTonight_ = false;
    uint8_t wins_ = 0;
    uint8_t losses_ = 0;
    uint8_t weight_ = 5;
    uint8_t dp_ = 1;
    uint8_t protein_ = 0;
    uint8_t proteinUses_ = 0;
    uint8_t overfeeds_ = 0;
    bool overfedThisCycle_ = false;
    bool injured_ = false;
    uint8_t injuries_ = 0;
    uint32_t injuredMs_ = 0;
    bool dead_ = false;
    bool cold_ = false;
    bool lastBattleWon_ = false;
    int16_t battleRoll_ = -1;
    bool championDiscovered_ = false;
    bool ultimateDiscovered_ = false;
    bool rookieDiscovered_ = false;
    uint8_t meat_ = 3;
    uint8_t energyItem_ = 2;
    uint8_t expItem_ = 1;
    uint8_t ring_ = 1;
    uint8_t proteinItem_ = 2;
    uint8_t medkit_ = 1;
    CareEvent events_[32] = {};
    uint8_t eventIndex_ = 0;
    uint8_t eventCount_ = 0;
    uint8_t dna_[4] = {};
    uint8_t ev_[6] = {};
};

}  // namespace vpet
