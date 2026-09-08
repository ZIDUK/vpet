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

void Motion::startEvolution(uint32_t nowMs) {
    state_ = MotionState::Evolution;
    frame_ = 0;
    lastTickMs_ = nowMs;
    lastFrameMs_ = nowMs;
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
        case MotionState::Idle: return species_ == SpeciesId::Rookie ? 19 : 15;
        case MotionState::Walk: return species_ == SpeciesId::Ultimate ? 22 : (species_ == SpeciesId::Rookie ? 22 : 15);
        case MotionState::Eat: return 25;
        case MotionState::Punch: return 15;
        case MotionState::Cast: return 15;
        case MotionState::Sleep: return 15;
        case MotionState::Evolution: return 15;
    }
    return 1;
}

uint16_t Motion::frameInterval() const {
    switch (state_) {
        case MotionState::Idle: return 120;
        case MotionState::Walk: return 90;
        case MotionState::Eat: return 100;
        case MotionState::Punch: return 80;
        case MotionState::Cast: return 90;
        case MotionState::Sleep: return 140;
        case MotionState::Evolution: return 120;
    }
    return 100;
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
        const bool action = state_ != MotionState::Idle && state_ != MotionState::Walk;
        if (action && next >= frameCount()) {
            actionCompleted_ = state_ != MotionState::Evolution;
            enterIdle(nowMs);
            return;
        }
        frame_ = next % frameCount();
    }

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
        case MotionState::Punch: return AnimationId::Punch;
        case MotionState::Cast: return AnimationId::Cast;
        case MotionState::Sleep: return AnimationId::Sleep;
        case MotionState::Evolution: return AnimationId::Evolution;
        case MotionState::Idle:
            if (species_ == SpeciesId::Ultimate) return AnimationId::DragfiremonIdle;
            return species_ == SpeciesId::Champion ? AnimationId::FlamemonIdle : AnimationId::FiremonIdle;
    }
    return AnimationId::FiremonIdle;
}

}  // namespace vpet
