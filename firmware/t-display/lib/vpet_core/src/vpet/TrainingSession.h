#pragma once

#include <stdint.h>

#include "vpet/Input.h"
#include "vpet/PetState.h"

namespace vpet {

// ---------------------------------------------------------------------------
// Batched training session (parity with src/core/training.py).
// The dumbbell path now supports a draft-then-confirm flow: a session
// accumulates reps in memory, reserves energy without debiting, and only
// applies the batched EV + cost + secondary effects when the player
// explicitly finalises. The legacy Action::Training single-rep path is
// preserved unchanged for backward compatibility.
// ---------------------------------------------------------------------------

constexpr uint8_t kTrainingEnergyCost = 8;
constexpr uint8_t kTrainingEvGain = 6;
constexpr uint8_t kTrainingEvMax = 252;
constexpr uint8_t kTrainingStatCount = 6;
constexpr uint32_t kTrainingDurationMs = 10000;

// TrainingStat reuses the CombatStat enum ordering (Hp, Mp, Off, Def, Spd,
// Brn) so we can address ev_[] and combatStat() without translation.
struct TrainingType {
    CombatStat stat;
    const char* path;        // asset path used by the renderer
    const char* esName;      // Spanish label (full word, not acronym)
    const char* enName;      // English label
};

constexpr TrainingType kTrainingTypes[kTrainingStatCount] = {
    {CombatStat::Off, "/ui/icons/battle.vpa",   "ATAQUE",   "ATTACK"},
    {CombatStat::Def, "/ui/icons/versus.vpa",   "DEFENSA",  "DEFENSE"},
    {CombatStat::Spd, "/ui/icons/training.vpa", "VELOCIDAD","SPEED"},
    {CombatStat::Hp,  "/ui/icons/heart.vpa",    "VIDA",     "HP"},
    {CombatStat::Mp,  "/ui/icons/energy.vpa",   "MP",       "MP"},
    {CombatStat::Brn, "/ui/icons/brain.vpa",    "MENTE",    "MIND"},
};

// Block reasons (mirrors src/core/training.py:batch_block_reason).
// Note: the EV cap constant is kTrainingEvMax (uint8_t=252). The reason
// strings must use distinct names to avoid colliding with the cap.
constexpr const char* kTrainingOk               = "";
constexpr const char* kTrainingTypeInvalid      = "TIPO INVALIDO";
constexpr const char* kTrainingNotFit           = "PET NO APTO";
constexpr const char* kTrainingEvMaxReason      = "EV AL MAXIMO";
constexpr const char* kTrainingNoEnergy         = "FALTA ENERGIA";

// Return the reason a batched session for `stat` is blocked; empty if OK.
inline const char* trainingBlockReason(const PetState& pet, CombatStat stat) {
    bool found = false;
    for (uint8_t i = 0; i < kTrainingStatCount; ++i) {
        if (kTrainingTypes[i].stat == stat) { found = true; break; }
    }
    if (!found) return kTrainingTypeInvalid;
    if (pet.species() == SpeciesId::Egg || pet.species() == SpeciesId::Baby) return kTrainingNotFit;
    if (pet.dead() || pet.injured() || pet.cold()) return kTrainingNotFit;
    if (pet.exploration.away()) return kTrainingNotFit;
    if (pet.evAt(stat) >= pet.evLimit()) return kTrainingEvMaxReason;
    if (pet.energy() < kTrainingEnergyCost) return kTrainingNoEnergy;
    return kTrainingOk;
}

// Returns the index of `stat` in kTrainingTypes, or 255 if not found.
inline uint8_t trainingIndexFor(CombatStat stat) {
    for (uint8_t i = 0; i < kTrainingStatCount; ++i) {
        if (kTrainingTypes[i].stat == stat) return i;
    }
    return 255;
}

inline const TrainingType& trainingTypeAt(uint8_t index) {
    return kTrainingTypes[index < kTrainingStatCount ? index : 0];
}

// Return (maxReps, reason). reason is empty when maxReps > 0.
inline uint8_t trainingMaxReps(const PetState& pet, CombatStat stat, const char** reason) {
    const char* block = trainingBlockReason(pet, stat);
    if (block != kTrainingOk) { *reason = block; return 0; }
    const uint8_t energyReps = pet.energy() / kTrainingEnergyCost;
    const int headroom = static_cast<int>(pet.evLimit()) - pet.evAt(stat);
    uint8_t evReps = 0;
    if (headroom > 0) {
        // Ceiling: a partial last rep is still included when headroom < 6.
        evReps = static_cast<uint8_t>((headroom + kTrainingEvGain - 1) / kTrainingEvGain);
    }
    const uint8_t reps = energyReps < evReps ? energyReps : evReps;
    if (reps == 0) {
        *reason = (energyReps == 0) ? kTrainingNoEnergy : kTrainingEvMaxReason;
        return 0;
    }
    *reason = kTrainingOk;
    return reps;
}

// Preview the next rep without mutating the pet.
//   can           - true if a rep is doable
//   evAdded       - how much EV the rep would add (may be partial)
//   energyCost    - always 8 when can, else 0
//   happinessAdd  - secondary (+3 per rep)
//   effortAdd     - secondary (+8 per rep)
//   weightDelta   - secondary (-1 per rep)
//   reason        - empty when can, else the block reason
struct TrainingPlan {
    bool can;
    uint8_t evAdded;
    uint8_t energyCost;
    uint8_t happinessAdd;
    uint8_t effortAdd;
    int8_t weightDelta;
    const char* reason;
};

inline TrainingPlan trainingPlanOneRep(const PetState& pet, CombatStat stat) {
    TrainingPlan plan = {false, 0, 0, 0, 0, 0, kTrainingOk};
    const char* block = trainingBlockReason(pet, stat);
    if (block != kTrainingOk) {
        plan.reason = block;
        return plan;
    }
    const int headroom = static_cast<int>(pet.evLimit()) - pet.evAt(stat);
    plan.can = true;
    plan.evAdded = static_cast<uint8_t>(headroom < static_cast<int>(kTrainingEvGain) ? headroom : kTrainingEvGain);
    plan.energyCost = kTrainingEnergyCost;
    plan.happinessAdd = 3;
    plan.effortAdd = 8;
    plan.weightDelta = (pet.trainingWeightRemainder() + 1 >= 4 && pet.weight() > 1) ? -1 : 0;
    plan.reason = kTrainingOk;
    return plan;
}

inline uint8_t trainingPreviewEv(const PetState& pet, CombatStat stat, uint8_t baseEv) {
    const int headroom=pet.evLimit()-pet.evAt(stat);
    if (headroom <= 0) return 0;
    const int gain=baseEv<headroom ? baseEv : headroom;
    const bool bonus=gain>0 && gain<headroom &&
        (pet.exploration.guide || pet.adoptedStock.count(adopted::indexOf("training_manual")));
    return gain+(bonus ? 1 : 0);
}

inline uint8_t consumeTrainingBonus(PetState& pet, CombatStat stat) {
    if (pet.exploration.away() || pet.evAt(stat) >= pet.evLimit()) return 0;
    const int manual = adopted::indexOf("training_manual");
    if (pet.exploration.guide) {
        pet.exploration.guide = pet.exploration.guidePending;
        pet.exploration.guidePending = false;
    } else if (pet.adoptedStock.count(manual)) {
        pet.adoptedStock.set(manual, 0);
    } else return 0;
    pet.addEv(stat, 1);
    return 1;
}

// Project the combat_stat value (or HP/MP pool) after adding `evDelta` EV
// to `stat`, without mutating the pet. The formula mirrors
// PetState::combatStat exactly:
//
// Adult values use the stage/IV growth profile; stored legacy EV is retained.
//
// HP and MP use the project's pool conversions (40 + hp*2 / 10 + mp),
// matching src/core/training.py:batch_projected_stat.
inline int projectedStatValue(
    const PetState& pet,
    CombatStat stat,
    uint8_t evDelta,
    int hpPoolBase = 40,
    int mpPoolBase = 10
) {
    const int currentEv = pet.evAt(stat);
    int projectedEv = currentEv + static_cast<int>(evDelta);
    if (projectedEv > pet.evLimit()) projectedEv = pet.evLimit();
    if (projectedEv < currentEv) projectedEv = currentEv;
    if (projectedEv < 0) projectedEv = 0;
    const int value = pet.combatStatAt(stat,static_cast<uint8_t>(projectedEv));
    if (stat == CombatStat::Hp) {
        return hpPoolBase + value * 2;
    }
    if (stat == CombatStat::Mp) {
        return mpPoolBase + value;
    }
    return value;
}

// Apply `reps` training sessions to `pet` in one call. The cost/EV/
// secondary effects are computed once and charged once. The last rep may
// be partial (less than kTrainingEvGain if the stat would exceed 252);
// any further reps in the queue are no-ops (headroom=0) and the
// corresponding ENE / secondary effects are NOT charged. The function
// does NOT persist; the caller is responsible for the atomic save and
// rollback on failure.
struct TrainingApplySummary {
    uint8_t reps;
    uint8_t evAdded;
    uint8_t energyCharged;
    uint8_t effortAdded;
    uint8_t happinessAdded;
    int8_t weightDelta;
};

inline TrainingApplySummary trainingApply(PetState& pet, CombatStat stat, uint8_t reps) {
    TrainingApplySummary summary = {0, 0, 0, 0, 0, 0};
    if (reps == 0) return summary;
    TrainingPlan plan = trainingPlanOneRep(pet, stat);
    if (!plan.can) return summary;
    // Clamp `reps` to BOTH the energy budget AND the EV headroom BEFORE
    // any charge. A rep that doesn't add EV (headroom=0) is a no-op and
    // must not be billed in energy/secondaries. Matches the spirit of
    // src/core/training.py:batch_apply and the user contract: no
    // extra reps for partial-final-EV situations.
    const uint8_t energyReps = pet.energy() / kTrainingEnergyCost;
    if (reps > energyReps) reps = energyReps;
    const int headroomTotal = static_cast<int>(pet.evLimit()) - pet.evAt(stat);
    if (headroomTotal <= 0) return summary;
    // Ceiling so a partial last rep is counted: at headroom=4 we still
    // get 1 rep with +4 EV.
    const uint8_t evReps = static_cast<uint8_t>((headroomTotal + kTrainingEvGain - 1) / kTrainingEvGain);
    if (reps > evReps) reps = evReps;
    uint8_t repsDone = 0;
    uint8_t evAdded = 0;
    for (uint8_t i = 0; i < reps; ++i) {
        const int headroom = static_cast<int>(pet.evLimit()) - pet.evAt(stat);
        if (headroom <= 0) break;
        const uint8_t gain = static_cast<uint8_t>(headroom < static_cast<int>(kTrainingEvGain) ? headroom : kTrainingEvGain);
        pet.addEv(stat, gain);
        evAdded = static_cast<uint8_t>(evAdded + gain);
        ++repsDone;
    }
    if (repsDone == 0) return summary;
    const uint8_t energyCharged = static_cast<uint8_t>(repsDone * kTrainingEnergyCost);
    const int newEnergy = pet.energy() - energyCharged;
    pet.setEnergy(newEnergy < 0 ? 0 : newEnergy);
    pet.setHappiness(pet.happiness() + repsDone * plan.happinessAdd);
    pet.setEffort(pet.effort() + repsDone * plan.effortAdd);
    const int8_t weightDelta = static_cast<int8_t>(pet.completeTrainingWeight(repsDone));
    pet.setTrainingSessions(pet.trainingSessions() + repsDone);
    summary.reps = repsDone;
    summary.evAdded = evAdded;
    summary.energyCharged = energyCharged;
    summary.effortAdded = static_cast<uint8_t>(repsDone * plan.effortAdd);
    summary.happinessAdded = static_cast<uint8_t>(repsDone * plan.happinessAdd);
    summary.weightDelta = weightDelta;
    return summary;
}

class BatchSaveError {
public:
    explicit BatchSaveError(const char* msg) : message_(msg) {}
    const char* what() const { return message_; }
private:
    const char* message_;
};

// Atomic transaction: apply `reps` training sessions to `pet` and persist
// through `save` in one step. If `save` returns false, the pet is
// restored from a snapshot taken before the apply and BatchSaveError is
// returned. The caller can safely retry by calling trainingCommit again:
// the second call observes the rolled-back state.
//
// The save callback is expected to take a PetState& and return true on
// success. Returns the apply summary on success.
typedef bool (*TrainingSaveFn)(PetState&);

inline TrainingApplySummary trainingCommit(
    PetState& pet,
    CombatStat stat,
    uint8_t reps,
    TrainingSaveFn save
) {
    // Snapshot the mutable fields we are about to change.
    const uint8_t snapEv[6] = {
        pet.evAt(CombatStat::Hp),  pet.evAt(CombatStat::Mp),
        pet.evAt(CombatStat::Off), pet.evAt(CombatStat::Def),
        pet.evAt(CombatStat::Spd), pet.evAt(CombatStat::Brn),
    };
    const int snapEnergy = pet.energy();
    const int snapHappiness = pet.happiness();
    const int snapEffort = pet.effort();
    const uint8_t snapWeight = pet.weight();
    const uint8_t snapWeightRemainder = pet.trainingWeightRemainder();
    const int snapTraining = pet.trainingSessions();
    const Exploration snapExploration = pet.exploration;
    const AdoptedInventory snapStock = pet.adoptedStock;

    TrainingApplySummary summary = trainingApply(pet, stat, reps);
    if (summary.reps == 0) return summary;
    summary.evAdded += consumeTrainingBonus(pet, stat);
    if (save != nullptr && !save(pet)) {
        // Rollback
        pet.exploration = snapExploration;
        pet.adoptedStock = snapStock;
        for (uint8_t i = 0; i < 6; ++i) {
            pet.setEvAt(static_cast<CombatStat>(i), snapEv[i]);
        }
        pet.setEnergy(snapEnergy);
        pet.setHappiness(snapHappiness);
        pet.setEffort(snapEffort);
        pet.setWeight(snapWeight);
        pet.setNutritionState(pet.hungerCycleRemainder(), snapWeightRemainder, pet.proteinFedThisCycle());
        pet.setTrainingSessions(snapTraining);
        throw BatchSaveError("save failed; pet rolled back from in-memory snapshot");
    }
    return summary;
}

// ---------------------------------------------------------------------------
// Draft-based training flow. The visible choices are shared with the simulator.
// State machine:
//   Select  -> choose stat (NEXT cycles, ACTION confirms)
//   Prepare -> preview the max reps and projected stat value
//   Session -> queue reps or focus Finalize; BACK asks before discarding
//   Confirm -> commit or continue editing the draft
//   Result  -> summary/stats pages; ACTION returns to Select
//   Error   -> retry the save or discard; Cancel -> continue or discard
// ---------------------------------------------------------------------------
class TrainingSession {
public:
    enum class State : uint8_t {
        Select = 0,
        Prepare = 1,
        Session = 2,
        Confirm = 3,
        Result = 4,
        Error = 5,
        Cancel = 6
    };

    State state = State::Select;
    enum class Focus : uint8_t { Train = 0, Finalize = 1 };
    Focus focus = Focus::Train;     // Session-state focus: TRAIN adds a rep, FINALIZE commits
    bool secondary = false;
    bool resultStats = false;
    uint8_t resultChoice = 0; // repeat, back, stats
    bool techniquesRequested = false;
    bool animating = false;
    uint32_t animationStartedMs = 0;
    uint32_t pausedAtMs = 0;
    uint8_t cursor = 0;             // current stat selection in State::Select
    uint8_t repsCompleted = 0;      // accumulated reps in State::Session
    uint8_t energyReserved = 0;     // reserved ENE during Session (not yet debited)
    uint8_t pendingEv = 0;          // accumulated EV delta during Session
    CombatStat chosenStat = CombatStat::Off;
    bool chosenStatValid = false;
    TrainingApplySummary lastSummary = {0, 0, 0, 0, 0, 0};
    const char* message = "";
    bool dirty = false;             // set on commit (single NVS write at end)
    bool needsRollback = false;     // set when apply was performed but save is required
    // Snapshot taken before the apply at commit time. Used to restore the
    // pet if the caller's save callback returns false. All fields are
    // copied verbatim; restoring uses the public PetState setters.
    struct Rollback {
        uint8_t ev[6];
        int energy;
        int happiness;
        int effort;
        uint8_t weight;
        uint8_t weightRemainder;
        int training;
    } rollback = {{0,0,0,0,0,0}, 0, 0, 0, 0, 0, 0};

    // Drive the session from an input event. The save callback is the
    // caller's persistence path. Returns true if the session is still
    // active, false when the player has closed it.
    //
    // The state machine itself never invokes save. On commit the apply
    // is performed and a rollback snapshot is captured. The caller
    // detects `dirty && needsRollback` and persists; if the persist
    // fails the caller must invoke `rollbackFromSnapshot(pet)` to
    // restore the pre-apply state.
    bool input(PetState& pet, InputEvent event, uint32_t nowMs) {
        if (event != InputEvent::None) message = "";
        switch (state) {
            case State::Select: return inputSelect(pet, event);
            case State::Prepare: {
                const bool active = inputPrepare(pet, event);
                if (state == State::Session) {
                    const auto plan = trainingPlanOneRep(pet, chosenStat);
                    repsCompleted = 1;
                    pendingEv = plan.evAdded;
                    energyReserved = plan.energyCost;
                    animating = true;
                    animationStartedMs = nowMs;
                }
                return active;
            }
            case State::Session: {
                if (nowMs-animationStartedMs >= kTrainingDurationMs) {
                    animating = false;
                    secondary = false;
                    return inputConfirm(pet, InputEvent::Action);
                }
                if (event == InputEvent::Back || event == InputEvent::Action) {
                    pausedAtMs = nowMs;
                    state = State::Cancel;
                    secondary = false;
                }
                return true;
            }
            case State::Confirm: return inputConfirm(pet, event);
            case State::Result: return inputResult(pet, event);
            case State::Error:  return inputError(pet, event);
            case State::Cancel:
                if (event == InputEvent::Next) secondary = !secondary;
                if (event == InputEvent::Back || (event == InputEvent::Action && !secondary)) {
                    animationStartedMs += nowMs-pausedAtMs;
                    state = State::Session;
                } else if (event == InputEvent::Action) {
                    reset();
                }
                return true;
        }
        return true;
    }

    // Restore the pet to the pre-commit state captured at the last
    // apply. Called by the App when settingsStore_.save returns false.
    void rollbackFromSnapshot(PetState& pet) {
        if (!needsRollback) return;
        pet.adoptedStock = rollbackStock;
        pet.exploration = rollbackExploration;
        for (uint8_t i = 0; i < 6; ++i) {
            pet.setEvAt(static_cast<CombatStat>(i), rollback.ev[i]);
        }
        pet.setEnergy(rollback.energy);
        pet.setHappiness(rollback.happiness);
        pet.setEffort(rollback.effort);
        pet.setWeight(rollback.weight);
        pet.setNutritionState(pet.hungerCycleRemainder(), rollback.weightRemainder, pet.proteinFedThisCycle());
        pet.setTrainingSessions(rollback.training);
        needsRollback = false;
        lastSummary = {0, 0, 0, 0, 0, 0};
        message = "ERROR AL GUARDAR";
        state = State::Error;
        secondary = false;
    }

    // Capture a snapshot of the mutable fields into `rollback`.
    void captureSnapshot(const PetState& pet) {
        rollbackStock = pet.adoptedStock;
        rollbackExploration = pet.exploration;
        for (uint8_t i = 0; i < 6; ++i) {
            rollback.ev[i] = pet.evAt(static_cast<CombatStat>(i));
        }
        rollback.energy = pet.energy();
        rollback.happiness = pet.happiness();
        rollback.effort = pet.effort();
        rollback.weight = pet.weight();
        rollback.weightRemainder = pet.trainingWeightRemainder();
        rollback.training = pet.trainingSessions();
    }

    void reset() {
        state = State::Select;
        cursor = 0;
        focus = Focus::Train;
        secondary = false;
        resultStats = false;
        resultChoice = 0;
        techniquesRequested = false;
        animating = false;
        animationStartedMs = 0;
        pausedAtMs = 0;
        repsCompleted = 0;
        energyReserved = 0;
        pendingEv = 0;
        chosenStat = CombatStat::Off;
        chosenStatValid = false;
        lastSummary = {0, 0, 0, 0, 0, 0};
        message = "";
        dirty = false;
        needsRollback = false;
        rollback = {{0,0,0,0,0,0}, 0, 0, 0, 0, 0};
    }

private:
    AdoptedInventory rollbackStock;
    Exploration rollbackExploration;
    bool inputSelect(PetState& pet, InputEvent event) {
        if (event == InputEvent::Back) {
            return false;  // exit session
        }
        if (event == InputEvent::Next) {
            cursor = static_cast<uint8_t>((cursor + 1) % (kTrainingStatCount + 2));
            message = "";
            return true;
        }
        if (event == InputEvent::Action) {
            if (cursor == kTrainingStatCount) { techniquesRequested = true; return true; }
            if (cursor > kTrainingStatCount) return false;
            CombatStat stat = kTrainingTypes[cursor].stat;
            const char* block = trainingBlockReason(pet, stat);
            if (block != kTrainingOk) {
                message = block;
                return true;
            }
            chosenStat = stat;
            chosenStatValid = true;
            repsCompleted = 0;
            energyReserved = 0;
            pendingEv = 0;
            animating = false;
            state = State::Prepare;
            secondary = false;
            return true;
        }
        return true;
    }

    bool inputPrepare(PetState& pet, InputEvent event) {
        if (event == InputEvent::Next) secondary = !secondary;
        if (event == InputEvent::Back || (event == InputEvent::Action && secondary)) {
            state = State::Select;
            return true;
        }
        if (event == InputEvent::Action) {
            const char* blocked = trainingBlockReason(pet, chosenStat);
            if (*blocked) { message = blocked; return true; }
            repsCompleted = 0;
            energyReserved = 0;
            pendingEv = 0;
            focus = Focus::Train;
            state = State::Session;
            return true;
        }
        return true;
    }


    bool inputConfirm(PetState& pet, InputEvent event) {
        if (event == InputEvent::Next) secondary = !secondary;
        if (event == InputEvent::Back || (event == InputEvent::Action && secondary)) {
            state = State::Session;
            focus = Focus::Finalize;
            return true;
        }
        if (event == InputEvent::Action) {
            if (repsCompleted == 0) {
                state = State::Select;
                return true;
            }
            // Apply the queued batch with a snapshot for rollback. The
            // caller is responsible for the persist; if save returns
            // false they must invoke rollbackFromSnapshot(pet).
            captureSnapshot(pet);
            lastSummary = trainingApply(pet, chosenStat, repsCompleted);
            if (lastSummary.reps == 0) {
                message = trainingBlockReason(pet, chosenStat);
                state = State::Error;
                secondary = false;
                return true;
            }
            needsRollback = true;
            lastSummary.evAdded += consumeTrainingBonus(pet, chosenStat);
            dirty = true;
            message = "ENTRENO LISTO";
            state = State::Result;
            resultStats = false;
            resultChoice = *trainingBlockReason(pet, chosenStat) ? 1 : 0;
            return true;
        }
        return true;
    }

    bool inputResult(PetState& pet, InputEvent event) {
        const bool canRepeat = !*trainingBlockReason(pet, chosenStat);
        if (event == InputEvent::Next) {
            resultChoice = (resultChoice+1)%3;
            if (!canRepeat && resultChoice==0) resultChoice=1;
        }
        if (event == InputEvent::Back || (event == InputEvent::Action && resultChoice==1)) {
            const uint8_t selected = cursor;
            reset();
            cursor = selected;
        } else if (event == InputEvent::Action && resultChoice==0 && canRepeat) {
            repsCompleted = pendingEv = energyReserved = 0;
            state = State::Prepare;
            secondary = false;
        } else if (event == InputEvent::Action && resultChoice==2) {
            resultStats = !resultStats;
        }
        return true;
    }

    bool inputError(PetState& pet, InputEvent event) {
        if (event == InputEvent::Next) secondary = !secondary;
        if (event == InputEvent::Back || (event == InputEvent::Action && secondary)) {
            reset();
        } else if (event == InputEvent::Action) {
            return inputConfirm(pet, event);
        }
        return true;
    }
};

}  // namespace vpet
