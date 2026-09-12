"""Autonomous idle/walk state shared by CircuitPython and the simulator."""
import random

from config import (
    PET_CAST_FRAME_COUNT,
    PET_CAST_FRAME_INTERVAL,
    PET_EAT_FRAME_COUNT,
    PET_EAT_FRAME_INTERVAL,
    PET_EVOLUTION_FRAME_COUNT,
    PET_EVOLUTION_FRAME_INTERVAL,
    PET_IDLE_DURATION_MS,
    PET_IDLE_FRAME_COUNT,
    PET_IDLE_FRAME_INTERVAL,
    PET_MAX_X,
    PET_MIN_X,
    PET_PUNCH_FRAME_COUNT,
    PET_PUNCH_FRAME_INTERVAL,
    PET_SLEEP_FRAME_COUNT,
    PET_SLEEP_FRAME_INTERVAL,
    PET_WALK_DURATION_MS,
    PET_WALK_FRAME_COUNT,
    PET_WALK_FRAME_INTERVAL,
    PET_WALK_SPEED,
    PET_X,
)


MOTION_IDLE = "idle"
MOTION_WALK = "walk"
MOTION_EAT = "eat"
MOTION_PUNCH = "punch"
MOTION_SLEEP = "sleep"
MOTION_CAST = "cast"
MOTION_EVOLUTION = "evolution"

ACTION_ANIMATIONS = {
    MOTION_EAT: (PET_EAT_FRAME_COUNT, PET_EAT_FRAME_INTERVAL),
    MOTION_PUNCH: (PET_PUNCH_FRAME_COUNT, PET_PUNCH_FRAME_INTERVAL),
    MOTION_SLEEP: (PET_SLEEP_FRAME_COUNT, PET_SLEEP_FRAME_INTERVAL),
    MOTION_CAST: (PET_CAST_FRAME_COUNT, PET_CAST_FRAME_INTERVAL),
    MOTION_EVOLUTION: (PET_EVOLUTION_FRAME_COUNT, PET_EVOLUTION_FRAME_INTERVAL),
}


class PetMotion:
    def __init__(
        self,
        now=0,
        random_source=None,
        min_x=PET_MIN_X,
        max_x=PET_MAX_X,
        start_x=PET_X,
    ):
        self.random = random_source or random
        self.min_x = min_x
        self.max_x = max_x
        self.state = MOTION_IDLE
        self.x = float(start_x)
        self.direction = 1
        self.frame = 0
        self.last_update = now
        self.last_frame = now
        self.state_until = now + self._duration(MOTION_IDLE)
        self.action_frame_count = None

    def _duration(self, state):
        bounds = PET_IDLE_DURATION_MS if state == MOTION_IDLE else PET_WALK_DURATION_MS
        return self.random.randint(bounds[0], bounds[1]) / 1000

    def _enter(self, state, now):
        self.state = state
        self.frame = 0
        self.last_frame = now
        self.last_update = now
        self.action_frame_count = None
        self.state_until = now + self._duration(state)
        if state == MOTION_WALK:
            self.direction = self.random.choice((-1, 1))

    def start_eat(self, now):
        self._start_action(MOTION_EAT, now)

    def start_punch(self, now):
        self._start_action(MOTION_PUNCH, now)

    def start_sleep(self, now):
        self._start_action(MOTION_SLEEP, now)

    def wake(self, now):
        if self.state == MOTION_SLEEP:
            self._enter(MOTION_IDLE, now)

    def start_cast(self, now):
        self._start_action(MOTION_CAST, now)

    def start_evolution(self, now, frame_count=None):
        self._start_action(MOTION_EVOLUTION, now)
        self.action_frame_count = frame_count or PET_EVOLUTION_FRAME_COUNT

    def _start_action(self, state, now):
        self.state = state
        self.frame = 0
        self.last_frame = now
        self.last_update = now
        self.action_frame_count = None

    def update(self, now):
        elapsed = max(0, now - self.last_update)
        self.last_update = now

        if self.state == MOTION_SLEEP:
            frame_count, interval = ACTION_ANIMATIONS[MOTION_SLEEP]
            elapsed_frames = int((now - self.last_frame + 0.000001) / interval)
            if elapsed_frames:
                nxt = self.frame + elapsed_frames
                loop_start = 12 if 12 < frame_count else 0
                if nxt < frame_count:
                    self.frame = nxt
                else:
                    loop_len = frame_count - loop_start
                    self.frame = loop_start + (nxt - frame_count) % loop_len if loop_len else nxt % frame_count
                self.last_frame += elapsed_frames * interval
            return

        if self.state in ACTION_ANIMATIONS:
            frame_count, interval = ACTION_ANIMATIONS[self.state]
            if self.action_frame_count is not None:
                frame_count = self.action_frame_count
            elapsed_frames = int((now - self.last_frame + 0.000001) / interval)
            if self.frame + elapsed_frames >= frame_count:
                self._enter(MOTION_IDLE, now)
            elif elapsed_frames:
                self.frame += elapsed_frames
                self.last_frame += elapsed_frames * interval
            return

        if now >= self.state_until:
            next_state = MOTION_WALK if self.state == MOTION_IDLE else MOTION_IDLE
            self._enter(next_state, now)
            return

        if self.state == MOTION_WALK:
            self.x += self.direction * PET_WALK_SPEED * elapsed
            if self.x <= self.min_x:
                self.x = float(self.min_x)
                self.direction = 1
            elif self.x >= self.max_x:
                self.x = float(self.max_x)
                self.direction = -1

        interval = (
            PET_IDLE_FRAME_INTERVAL if self.state == MOTION_IDLE else PET_WALK_FRAME_INTERVAL
        )
        frame_count = PET_IDLE_FRAME_COUNT if self.state == MOTION_IDLE else PET_WALK_FRAME_COUNT
        elapsed_frames = int((now - self.last_frame + 0.000001) / interval)
        if elapsed_frames:
            self.frame = (self.frame + elapsed_frames) % frame_count
            self.last_frame += elapsed_frames * interval
