#pragma once

#include <stdint.h>

#include "vpet/PetState.h"

namespace vpet {

enum class MotionState : uint8_t {
    Idle,
    Walk,
    Eat,
    Punch,
    Cast,
    Sleep,
    Evolution,
    Hatch,
    Hit,
    Hurt,
    Dodge,
    Block,
};
enum class AnimationId : uint8_t {
    FiremonIdle,
    FiremonWalk,
    FlamemonIdle,
    FlamemonWalk,
    DragfiremonIdle,
    DragfiremonFly,
    Eat,
    Punch,
    Cast,
    Sleep,
    Evolution,
};

class Motion {
public:
    Motion(int displayWidth, int displayHeight, int menuHeight, int frameSize);
    void setSpecies(SpeciesId species) { species_ = species; }
    void alignClock(uint32_t nowMs);
    void startWalking(uint32_t nowMs);
    void startAction(Action action, uint32_t nowMs);
    void startReaction(bool won, bool injured, uint32_t nowMs);
    void startEvolution(uint32_t nowMs);
    void startHatch(uint32_t nowMs);
    void wake(uint32_t nowMs);
    void tick(uint32_t nowMs);
    bool consumeActionCompleted();

    MotionState state() const { return state_; }
    AnimationId animation() const;
    int x() const { return x_; }
    int y() const { return y_; }
    int direction() const { return direction_; }
    uint16_t frame() const { return frame_; }

private:
    void enterIdle(uint32_t nowMs);
    uint16_t frameCount() const;
    uint16_t frameInterval() const;
    uint16_t sleepLoopStart() const;
    uint16_t sleepLoopEnd() const;

    int maxX_;
    int y_;
    SpeciesId species_ = SpeciesId::Egg;
    MotionState state_ = MotionState::Idle;
    int x_;
    int32_t xMilli_;
    int direction_ = 1;
    uint16_t frame_ = 0;
    uint32_t lastTickMs_ = 0;
    uint32_t lastFrameMs_ = 0;
    uint32_t stateUntilMs_ = 0;
    bool actionCompleted_ = false;
};

}  // namespace vpet
