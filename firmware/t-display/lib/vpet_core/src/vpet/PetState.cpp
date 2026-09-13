#include "vpet/PetState.h"

namespace vpet {

int PetState::clampStat(int value) {
    return value < 0 ? 0 : (value > 100 ? 100 : value);
}

uint8_t PetState::clampByte(int value, uint8_t maxValue) {
    if (value < 0) return 0;
    if (value > maxValue) return maxValue;
    return static_cast<uint8_t>(value);
}

namespace {
uint8_t clampItem(int value) {
    if (value < 0) return 0;
    if (value > 99) return 99;
    return static_cast<uint8_t>(value);
}
}

void PetState::record(CareEventType type, uint8_t value) {
    const uint32_t minutes = ageSeconds() / 60U;
    CareEvent event;
    event.tRelMin = static_cast<uint16_t>(minutes > 65535U ? 65535U : minutes);
    event.type = static_cast<uint8_t>(type);
    event.value = value;
    events_[eventIndex_] = event;
    eventIndex_ = static_cast<uint8_t>((eventIndex_ + 1) % 32);
    if (eventCount_ < 32) ++eventCount_;
}

CareEvent PetState::careEventAt(uint8_t index) const {
    return index < 32 ? events_[index] : CareEvent{};
}

void PetState::resetToEgg() {
    *this = PetState();
}

void PetState::rollDna(uint32_t entropy) {
    uint32_t mix = entropy * 1664525U + 1013904223U;
    dna_[0] = static_cast<uint8_t>(mix);
    dna_[1] = static_cast<uint8_t>(mix >> 8);
    dna_[2] = static_cast<uint8_t>(mix >> 16);
    dna_[3] = static_cast<uint8_t>(mix >> 24);
    if (!hasDna()) dna_[0] = 1;
}

void PetState::restoreDna(const uint8_t dna[4]) {
    if (dna == nullptr) return;
    dna_[0] = dna[0];
    dna_[1] = dna[1];
    dna_[2] = dna[2];
    dna_[3] = dna[3];
}

void PetState::restoreEv(const uint8_t ev[6]) {
    if (ev == nullptr) return;
    for (uint8_t i = 0; i < 6; ++i) {
        ev_[i] = ev[i] > 252 ? 252 : ev[i];
    }
}

bool PetState::hasDna() const {
    return (dna_[0] | dna_[1] | dna_[2] | dna_[3]) != 0;
}

uint8_t PetState::ivAt(CombatStat stat) const {
    const uint8_t index = static_cast<uint8_t>(stat);
    if (index > 5) return 0;
    const uint8_t packed = dna_[index / 2];
    return (index % 2 == 0) ? static_cast<uint8_t>(packed & 0x0F) : static_cast<uint8_t>(packed >> 4);
}

uint8_t PetState::evAt(CombatStat stat) const {
    const uint8_t index = static_cast<uint8_t>(stat);
    return index < 6 ? ev_[index] : 0;
}

uint8_t PetState::combatStat(CombatStat stat) const {
    int value = 10 + static_cast<int>(ivAt(stat)) * 3 + static_cast<int>(evAt(stat)) / 6;
    if (value < 1) return 1;
    if (value > 99) return 99;
    return static_cast<uint8_t>(value);
}

void PetState::gainEv(CombatStat stat, uint8_t amount) {
    const uint8_t index = static_cast<uint8_t>(stat);
    if (index > 5) return;
    const int next = static_cast<int>(ev_[index]) + amount;
    ev_[index] = next > 252 ? 252 : static_cast<uint8_t>(next);
}

void PetState::resetAfterEvolution() {
    careMistakes_ = 0;
    callReason_ = CallReason::None;
    callStartedMs_ = 0;
    lightsHandledTonight_ = false;
    trainingSessions_ = 0;
    battles_ = 0;
    meals_ = 0;
    stageAgeMs_ = 0;
    protein_ = 0;
    proteinUses_ = 0;
    overfeeds_ = 0;
    overfedThisCycle_ = false;
    injured_ = false;
    injuries_ = 0;
    injuredMs_ = 0;
    dead_ = false;
    lastBattleWon_ = false;
    battleRoll_ = -1;
    dp_ = 1;
}

void PetState::setStageAgeSeconds(uint32_t seconds) {
    stageAgeMs_ = seconds * 1000U;
}

void PetState::setCareMistakes(uint8_t value) {
    careMistakes_ = value > 99 ? 99 : value;
}

void PetState::setBattles(int value) {
    battles_ = value < 0 ? 0 : value;
}

void PetState::setWins(uint8_t value) {
    wins_ = value;
}

void PetState::setLosses(uint8_t value) {
    losses_ = value;
}

void PetState::setDp(uint8_t value) {
    dp_ = value > 3 ? 3 : value;
}

void PetState::setBattleRoll(uint8_t roll) {
    battleRoll_ = static_cast<int16_t>(roll > 99 ? 99 : roll);
}

void PetState::setInjured(bool value) {
    injured_ = value;
    if (!value) injuredMs_ = 0;
}

void PetState::setInjuries(uint8_t value) {
    injuries_ = value > 99 ? 99 : value;
    checkDeath();
}

void PetState::setHealth(int value) {
    health_ = clampStat(value);
}

void PetState::restoreInjury(bool injured, uint8_t injuries, bool dead) {
    injured_ = injured;
    injuries_ = injuries > 99 ? 99 : injuries;
    dead_ = dead;
    if (!injured_) injuredMs_ = 0;
}

uint8_t PetState::effortHearts() const {
    const int hearts = trainingSessions_ / 4;
    return hearts > 4 ? 4 : static_cast<uint8_t>(hearts);
}

namespace {
uint8_t barHearts(int value) {
    const int hearts = (value + 24) / 25;
    if (hearts < 0) return 0;
    return hearts > 4 ? 4 : static_cast<uint8_t>(hearts);
}
}

uint8_t PetState::hungerHearts() const {
    return barHearts(hunger_);
}

uint8_t PetState::strengthHearts() const {
    return barHearts(energy_);
}

bool PetState::hasWinRatio() const {
    return (static_cast<int>(wins_) + static_cast<int>(losses_)) > 0;
}

uint8_t PetState::winRatioPercent() const {
    const int played = static_cast<int>(wins_) + static_cast<int>(losses_);
    if (played == 0) return 0;
    return static_cast<uint8_t>((wins_ * 100) / played);
}

bool PetState::canBattle() const {
    if (dead_ || injured_ || dp_ == 0) return false;
    if (species_ == SpeciesId::Egg || species_ == SpeciesId::Baby) return false;
    return true;
}

void PetState::applyProtein() {
    energy_ = clampStat(energy_ + 20);
    if (proteinUses_ < 99) ++proteinUses_;
    if (proteinUses_ % 4 == 0) {
        if (protein_ < 7) ++protein_;
        if (dp_ < 3) ++dp_;
    }
    refreshCallAfterCare();
}

void PetState::injure() {
    if (!injured_) injuredMs_ = 0;
    injured_ = true;
    if (injuries_ < 99) ++injuries_;
    checkDeath();
}

void PetState::checkDeath() {
    if (species_ == SpeciesId::Egg) return;
    if (injuries_ >= 15 || (injured_ && injuredMs_ >= 21600000U)) {
        dead_ = true;
    }
}

void PetState::resolveBattle() {
    if (dp_ > 0) --dp_;
    energy_ = clampStat(energy_ - 12);
    effort_ = clampStat(effort_ + 4);
    ++battles_;
    const int roll = battleRoll_ >= 0 ? battleRoll_ : static_cast<int>((ageMs_ / 1000U + static_cast<uint32_t>(battles_) * 17U) % 100U);
    int chance = 50 + static_cast<int>(effortHearts()) * 8 + energy_ / 20 - static_cast<int>(protein_) * 4;
    if (chance < 15) chance = 15;
    if (chance > 90) chance = 90;
    lastBattleWon_ = roll < chance;
    if (lastBattleWon_) {
        if (wins_ < 255) ++wins_;
        if (protein_ >= 4) injure();
    } else {
        if (losses_ < 255) ++losses_;
        injure();
    }
    record(CareEventType::Battle, lastBattleWon_ ? 1 : 0);
}

CallUpdate PetState::startCall(CallReason reason, uint32_t nowMs) {
    callReason_ = reason;
    callStartedMs_ = nowMs;
    record(CareEventType::CallStart, static_cast<uint8_t>(reason));
    return CallUpdate::Started;
}

void PetState::refreshCallAfterCare() {
    if (callReason_ == CallReason::Hunger && hunger_ > 0) {
        callReason_ = CallReason::None;
        callStartedMs_ = 0;
    }
    if (callReason_ == CallReason::Strength && energy_ > 0) {
        callReason_ = CallReason::None;
        callStartedMs_ = 0;
    }
}

CallUpdate PetState::updateCall(uint32_t nowMs, uint32_t scale, uint8_t hour, bool asleep) {
    if (cold_ || species_ == SpeciesId::Egg || scale == 0) return CallUpdate::None;
    refreshCallAfterCare();
    const bool night = hour >= 21 || hour < 8;
    if (!night) lightsHandledTonight_ = false;
    const uint32_t margin = callReason_ == CallReason::Lights
        ? 3600000U / scale
        : 600000U / scale;
    if (callReason_ != CallReason::None && nowMs - callStartedMs_ >= margin) {
        if (careMistakes_ < 99) ++careMistakes_;
        record(CareEventType::CallMiss, careMistakes_);
        const bool startStrength = callReason_ == CallReason::Hunger && energy_ == 0;
        if (callReason_ == CallReason::Lights) lightsHandledTonight_ = true;
        callReason_ = CallReason::None;
        callStartedMs_ = 0;
        if (startStrength) startCall(CallReason::Strength, nowMs);
        return CallUpdate::Missed;
    }
    if (callReason_ != CallReason::None) return CallUpdate::None;
    if (hunger_ == 0) return startCall(CallReason::Hunger, nowMs);
    if (energy_ == 0) return startCall(CallReason::Strength, nowMs);
    if (night && !asleep && !lightsHandledTonight_) {
        lightsHandledTonight_ = true;
        return startCall(CallReason::Lights, nowMs);
    }
    return CallUpdate::None;
}

void PetState::noteWake(uint8_t hour) {
    if (species_ == SpeciesId::Egg) return;
    if (hour < 8 || hour >= 21) {
        if (careMistakes_ < 99) ++careMistakes_;
        record(CareEventType::Wake, careMistakes_);
    }
}

void PetState::restoreOverfeed(bool usedThisCycle, uint8_t count) {
    overfedThisCycle_ = usedThisCycle;
    overfeeds_ = count > 99 ? 99 : count;
}

bool PetState::canFeed() const {
    if (species_ == SpeciesId::Egg) return false;
    return !(hunger_ >= 100 && overfedThisCycle_);
}

void PetState::applyFeed(bool fromItem) {
    if (hunger_ >= 100) {
        overfedThisCycle_ = true;
        if (overfeeds_ < 99) ++overfeeds_;
        if (weight_ < 99) ++weight_;
    } else {
        hunger_ = clampStat(hunger_ + 20);
        if (fromItem && weight_ < 99) ++weight_;
    }
    if (!fromItem) {
        energy_ = clampStat(energy_ + 5);
        ++meals_;
        record(CareEventType::Feed, overfedThisCycle_ ? 1 : 0);
    }
    refreshCallAfterCare();
}

CareSnapshot PetState::snapshot() const {
    CareSnapshot snap{};
    snap.schema = 1;
    snap.species = static_cast<uint8_t>(species_);
    const uint32_t minutes = stageAgeSeconds() / 60U;
    snap.stageAgeMin = static_cast<uint16_t>(minutes > 65535U ? 65535U : minutes);
    snap.hunger = static_cast<uint8_t>(hunger_);
    snap.energy = static_cast<uint8_t>(energy_);
    snap.happiness = static_cast<uint8_t>(happiness_);
    snap.health = static_cast<uint8_t>(health_);
    snap.careMistakes = careMistakes_;
    snap.effort = static_cast<uint8_t>(effort_);
    snap.meals = clampByte(meals_, 255);
    snap.training = clampByte(trainingSessions_, 255);
    snap.battlesThisForm = clampByte(battles_, 255);
    snap.wins = wins_;
    snap.losses = losses_;
    snap.callReason = static_cast<uint8_t>(callReason_);
    snap.flags = 0;
    return snap;
}

void PetState::tick(uint32_t elapsedMs) {
    if (cold_) return;
    ageMs_ += elapsedMs;
    if (species_ == SpeciesId::Egg) return;
    stageAgeMs_ += elapsedMs;
    if (injured_ && !dead_) {
        injuredMs_ += elapsedMs;
        checkDeath();
    }
    if (dead_) return;
    decayMs_ += elapsedMs;
    while (decayMs_ >= 30000) {
        decayMs_ -= 30000;
        const int hungerBefore = hunger_;
        const int energyBefore = energy_;
        hunger_ = clampStat(hunger_ - 1);
        energy_ = clampStat(energy_ - 1);
        happiness_ = clampStat(happiness_ - 1);
        if ((hungerBefore > 0 && hunger_ == 0) || (energyBefore > 0 && energy_ == 0)) {
            record(CareEventType::DecayZero, hunger_ == 0 ? 1 : 2);
        }
        if (hunger_ < 100) overfedThisCycle_ = false;
    }
}

bool PetState::beginAction(Action action) {
    if (action == Action::None || pendingAction_ != Action::None) {
        return false;
    }
    if (dead_ || species_ == SpeciesId::Egg) return false;
    if (cold_ && action != Action::Rest) return false;
    if (action == Action::Feed && !canFeed()) return false;
    if (action == Action::Battle && !canBattle()) return false;
    if (species_ == SpeciesId::Baby && (action == Action::Training || action == Action::Battle)) {
        return false;
    }
    pendingAction_ = action;
    return true;
}

bool PetState::completeAction() {
    const Action action = pendingAction_;
    pendingAction_ = Action::None;
    switch (action) {
        case Action::Feed: {
            const bool trained = hunger_ < 100;
            applyFeed(false);
            if (trained) gainEv(CombatStat::Hp, 2);
            return true;
        }
        case Action::Training:
            effort_ = clampStat(effort_ + 8);
            energy_ = clampStat(energy_ - 8);
            happiness_ = clampStat(happiness_ + 3);
            ++trainingSessions_;
            if (weight_ > 0) --weight_;
            record(CareEventType::Train, 0);
            gainEv(CombatStat::Off, 2);
            gainEv(CombatStat::Spd, 1);
            return true;
        case Action::Battle:
            resolveBattle();
            gainEv(CombatStat::Off, 1);
            gainEv(CombatStat::Brn, 1);
            return true;
        case Action::Rest:
            energy_ = clampStat(energy_ + 25);
            health_ = clampStat(health_ + 5);
            if (dp_ < 3) ++dp_;
            gainEv(CombatStat::Mp, 2);
            gainEv(CombatStat::Def, 1);
            refreshCallAfterCare();
            if (callReason_ == CallReason::Lights) {
                callReason_ = CallReason::None;
                callStartedMs_ = 0;
                lightsHandledTonight_ = true;
            }
            return true;
        case Action::None:
            return false;
    }
    return false;
}

bool PetState::forceNextForm() {
    switch (species_) {
        case SpeciesId::Egg: evolveTo(SpeciesId::Baby); return true;
        case SpeciesId::Baby: evolveTo(SpeciesId::Rookie); return true;
        case SpeciesId::Rookie: evolveTo(SpeciesId::Champion); return true;
        case SpeciesId::Champion: evolveTo(SpeciesId::Ultimate); return true;
        case SpeciesId::Ultimate: resetToEgg(); return true;
    }
    return false;
}

void PetState::evolveTo(SpeciesId species) {
    species_ = species;
    if (species == SpeciesId::Rookie) rookieDiscovered_ = true;
    if (species == SpeciesId::Champion) championDiscovered_ = true;
    if (species == SpeciesId::Ultimate) {
        rookieDiscovered_ = true;
        championDiscovered_ = true;
        ultimateDiscovered_ = true;
    }
}

void PetState::restore(
    SpeciesId species,
    int hunger,
    int energy,
    int happiness,
    int effort,
    int health,
    uint32_t ageSeconds
) {
    evolveTo(species);
    hunger_ = clampStat(hunger);
    energy_ = clampStat(energy);
    happiness_ = clampStat(happiness);
    effort_ = clampStat(effort);
    health_ = clampStat(health);
    ageMs_ = ageSeconds * 1000U;
}

void PetState::restoreItems(
    uint8_t meat,
    uint8_t energyItem,
    uint8_t expItem,
    uint8_t ring,
    uint8_t proteinItem,
    uint8_t medkit
) {
    meat_ = clampItem(meat);
    energyItem_ = clampItem(energyItem);
    expItem_ = clampItem(expItem);
    ring_ = clampItem(ring);
    proteinItem_ = clampItem(proteinItem);
    medkit_ = clampItem(medkit);
}

void PetState::restoreCare(
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
) {
    stageAgeMs_ = stageAgeSeconds * 1000U;
    careMistakes_ = careMistakes > 99 ? 99 : careMistakes;
    callReason_ = call;
    meals_ = meals < 0 ? 0 : meals;
    trainingSessions_ = training < 0 ? 0 : training;
    battles_ = battles < 0 ? 0 : battles;
    wins_ = wins;
    losses_ = losses;
    weight_ = weight;
    dp_ = dp;
    protein_ = protein > 7 ? 7 : protein;
}

uint8_t PetState::itemCount(uint8_t index) const {
    switch (index) {
        case 0: return meat_;
        case 1: return energyItem_;
        case 2: return expItem_;
        case 3: return ring_;
        case 4: return proteinItem_;
        case 5: return medkit_;
        default: return 0;
    }
}

ItemUseResult PetState::useItem(uint8_t index) {
    if (index == 6) return ItemUseResult::Back;
    if (index > 5) return ItemUseResult::Empty;
    if (dead_ || cold_ || species_ == SpeciesId::Egg) return ItemUseResult::Blocked;
    if (index == 0 && !canFeed()) return ItemUseResult::Blocked;
    if (index == 5 && !injured_) return ItemUseResult::Blocked;
    uint8_t* stock = nullptr;
    switch (index) {
        case 0: stock = &meat_; break;
        case 1: stock = &energyItem_; break;
        case 2: stock = &expItem_; break;
        case 3: stock = &ring_; break;
        case 4: stock = &proteinItem_; break;
        case 5: stock = &medkit_; break;
    }
    if (stock == nullptr || *stock == 0) return ItemUseResult::Empty;
    --(*stock);
    switch (index) {
        case 0: {
            const bool trained = hunger_ < 100;
            applyFeed(true);
            if (trained) gainEv(CombatStat::Hp, 2);
            break;
        }
        case 1:
            energy_ = clampStat(energy_ + 25);
            refreshCallAfterCare();
            gainEv(CombatStat::Mp, 2);
            break;
        case 2:
            effort_ = clampStat(effort_ + 8);
            gainEv(CombatStat::Brn, 2);
            break;
        case 3: happiness_ = clampStat(happiness_ + 15); break;
        case 4:
            applyProtein();
            gainEv(CombatStat::Off, 2);
            break;
        case 5:
            injured_ = false;
            injuredMs_ = 0;
            health_ = clampStat(health_ + 20);
            break;
    }
    return ItemUseResult::Used;
}

bool PetState::itemVisible(uint8_t index) const {
    if (index == 6) return true;
    return index < 6 && itemCount(index) > 0;
}

uint8_t PetState::visibleInventoryCount() const {
    uint8_t count = 1;
    for (uint8_t index = 0; index < 6; ++index) {
        if (itemVisible(index)) ++count;
    }
    return count;
}

uint8_t PetState::inventoryIndexAt(uint8_t visibleSlot) const {
    uint8_t slot = 0;
    for (uint8_t index = 0; index < 7; ++index) {
        if (!itemVisible(index)) continue;
        if (slot == visibleSlot) return index;
        ++slot;
    }
    return 6;
}

uint8_t PetState::nextVisibleInventoryIndex(uint8_t index) const {
    for (uint8_t step = 1; step <= 7; ++step) {
        const uint8_t candidate = static_cast<uint8_t>((index + step) % 7);
        if (itemVisible(candidate)) return candidate;
    }
    return 6;
}

uint8_t PetState::clampVisibleInventoryIndex(uint8_t index) const {
    return itemVisible(index) ? index : nextVisibleInventoryIndex(index);
}

bool PetState::hasDiscovered(SpeciesId species) const {
    if (species == SpeciesId::Egg || species == SpeciesId::Baby) return true;
    if (species == SpeciesId::Rookie) return rookieDiscovered_;
    if (species == SpeciesId::Champion) return championDiscovered_;
    return ultimateDiscovered_;
}

}  // namespace vpet
