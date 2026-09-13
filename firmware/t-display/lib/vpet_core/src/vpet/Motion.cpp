#include "vpet/Motion.h"

namespace vpet {

Motion::Motion(int displayWidth, int displayHeight, int menuHeight, int frameSize)
    : maxX_(displayWidth - frameSize),
      y_(displayHeight - frameSize - 4),
      x_((displayWidth - frameSize) / 2),
      xMilli_(x_ * 1000) {
    if (y_ < menuHeight) {
        y_ = menuHeight;
    }
}

void Motion::alignClock(uint32_t nowMs) {
    lastTickMs_ = nowMs;
    lastFrameMs_ = nowMs;
    if (species_ == SpeciesId::Egg) {
        frame_ = 0;
        return;
    }
    if (state_ == MotionState::Hatch) {
        enterIdle(nowMs);
    }
}

void Motion::startWalking(uint32_t nowMs) {
    state_ = MotionState::Walk;
    frame_ = 0;
    lastTickMs_ = nowMs;
    lastFrameMs_ = nowMs;
    stateUntilMs_ = nowMs + 3000;
}

void Motion::startAction(Action action, uint32_t nowMs) {
    switch (action) {
        case Action::Feed: state_ = MotionState::Eat; break;
        case Action::Training: state_ = MotionState::Punch; break;
        case Action::Battle: state_ = MotionState::Cast; break;
        case Action::Rest: state_ = MotionState::Sleep; break;
        case Action::None: return;
    }
    frame_ = 0;
    lastTickMs_ = nowMs;
    lastFrameMs_ = nowMs;
    actionCompleted_ = false;
}

void Motion::startReaction(bool won, bool injured, uint32_t nowMs) {
    if (won) {
        state_ = injured ? MotionState::Block : MotionState::Dodge;
    } else {
        state_ = injured ? MotionState::Hurt : MotionState::Hit;
    }
    frame_ = 0;
    lastTickMs_ = nowMs;
    lastFrameMs_ = nowMs;
    actionCompleted_ = false;
}

void Motion::startEvolution(uint32_t nowMs) {
    state_ = MotionState::Evolution;
    frame_ = 0;
    lastTickMs_ = nowMs;
    lastFrameMs_ = nowMs;
}

void Motion::startHatch(uint32_t nowMs) {
    state_ = MotionState::Hatch;
    frame_ = 0;
    lastTickMs_ = nowMs;
    lastFrameMs_ = nowMs;
}

void Motion::wake(uint32_t nowMs) {
    if (state_ != MotionState::Sleep) return;
    actionCompleted_ = true;
    enterIdle(nowMs);
}

void Motion::enterIdle(uint32_t nowMs) {
    state_ = MotionState::Idle;
    frame_ = 0;
    lastTickMs_ = nowMs;
    lastFrameMs_ = nowMs;
    stateUntilMs_ = nowMs + 2500;
}

uint16_t Motion::frameCount() const {
    switch (state_) {
        case MotionState::Idle:
            if (species_ == SpeciesId::Egg) return 16;
            if (species_ == SpeciesId::Baby) return 25;
            if (species_ == SpeciesId::Rookie) return 19;
            if (species_ == SpeciesId::Champion) return 15;
            return 25;
        case MotionState::Walk:
            if (species_ == SpeciesId::Baby) return 25;
            if (species_ == SpeciesId::Rookie) return 22;
            if (species_ == SpeciesId::Champion) return 15;
            return 25;
        case MotionState::Eat: return 25;
        case MotionState::Punch: return 15;
        case MotionState::Cast:
        case MotionState::Hit:
        case MotionState::Hurt:
        case MotionState::Dodge:
        case MotionState::Block: return 15;
        case MotionState::Sleep:
            if (species_ == SpeciesId::Baby || species_ == SpeciesId::Ultimate) return 25;
            return 15;
        case MotionState::Evolution: return species_ == SpeciesId::Rookie ? 16 : 15;
        case MotionState::Hatch: return 10;
    }
    return 1;
}

uint16_t Motion::frameInterval() const {
    switch (state_) {
        case MotionState::Idle: return 85;
        case MotionState::Walk: return 65;
        case MotionState::Eat: return 75;
        case MotionState::Punch: return 65;
        case MotionState::Cast:
        case MotionState::Hit:
        case MotionState::Hurt:
        case MotionState::Dodge:
        case MotionState::Block: return 70;
        case MotionState::Sleep: return 105;
        case MotionState::Evolution: return 85;
        case MotionState::Hatch: return 80;
    }
    return 100;
}

uint16_t Motion::sleepLoopStart() const {
    constexpr uint16_t kLieDownFrame = 11;
    const uint16_t count = frameCount();
    return kLieDownFrame < count ? kLieDownFrame : 0;
}

uint16_t Motion::sleepLoopEnd() const {
    constexpr uint16_t kLastLyingFrame = 14;
    const uint16_t count = frameCount();
    return kLastLyingFrame < count ? kLastLyingFrame : static_cast<uint16_t>(count - 1);
}

void Motion::tick(uint32_t nowMs) {
    const uint32_t elapsed = nowMs - lastTickMs_;
    lastTickMs_ = nowMs;
    if (state_ == MotionState::Walk) {
        xMilli_ += direction_ * static_cast<int32_t>(13U * elapsed);
        x_ = xMilli_ / 1000;
        if (x_ <= 0) {
            x_ = 0;
            xMilli_ = 0;
            direction_ = 1;
        } else if (x_ >= maxX_) {
            x_ = maxX_;
            xMilli_ = maxX_ * 1000;
            direction_ = -1;
        }
    }

    const uint32_t frameElapsed = nowMs - lastFrameMs_;
    const uint16_t interval = frameInterval();
    if (frameElapsed >= interval) {
        const uint32_t steps = frameElapsed / interval;
        const uint32_t next = frame_ + steps;
        lastFrameMs_ += steps * interval;
        if (state_ == MotionState::Sleep) {
            const uint16_t loopStart = sleepLoopStart();
            const uint16_t loopEnd = sleepLoopEnd();
            if (next <= loopEnd) {
                frame_ = static_cast<uint16_t>(next);
            } else {
                const uint16_t loopLen = static_cast<uint16_t>(loopEnd - loopStart + 1);
                frame_ = loopLen == 0
                    ? loopStart
                    : static_cast<uint16_t>(loopStart + (next - loopEnd - 1) % loopLen);
            }
            return;
        }
        if (state_ == MotionState::Hatch) {
            const uint16_t count = frameCount();
            frame_ = next >= count ? static_cast<uint16_t>(count - 1) : static_cast<uint16_t>(next);
            return;
        }
        const bool action = state_ != MotionState::Idle && state_ != MotionState::Walk;
        if (action && next >= frameCount()) {
            actionCompleted_ = state_ != MotionState::Evolution;
            enterIdle(nowMs);
            return;
        }
        frame_ = next % frameCount();
    }

    if (species_ == SpeciesId::Egg) return;

    if ((state_ == MotionState::Idle || state_ == MotionState::Walk) && nowMs >= stateUntilMs_) {
        if (state_ == MotionState::Idle) {
            direction_ = direction_ > 0 ? -1 : 1;
            startWalking(nowMs);
        } else {
            enterIdle(nowMs);
        }
    }
}

bool Motion::consumeActionCompleted() {
    const bool completed = actionCompleted_;
    actionCompleted_ = false;
    return completed;
}

AnimationId Motion::animation() const {
    switch (state_) {
        case MotionState::Walk:
            if (species_ == SpeciesId::Ultimate) return AnimationId::DragfiremonFly;
            return species_ == SpeciesId::Champion ? AnimationId::FlamemonWalk : AnimationId::FiremonWalk;
        case MotionState::Eat: return AnimationId::Eat;
        case MotionState::Punch:
        case MotionState::Hit:
        case MotionState::Hurt: return AnimationId::Punch;
        case MotionState::Cast:
        case MotionState::Dodge:
        case MotionState::Block: return AnimationId::Cast;
        case MotionState::Sleep: return AnimationId::Sleep;
        case MotionState::Evolution: return AnimationId::Evolution;
        case MotionState::Hatch:
        case MotionState::Idle:
            if (species_ == SpeciesId::Ultimate) return AnimationId::DragfiremonIdle;
            return species_ == SpeciesId::Champion ? AnimationId::FlamemonIdle : AnimationId::FiremonIdle;
    }
    return AnimationId::FiremonIdle;
}

}  // namespace vpet
