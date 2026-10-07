"""Dumbbell menu: targeted attributes and technique lessons, simulator only."""
from core.training import TRAINING_TYPES, train_attribute, training_block_reason, training_values
from scripts.practice_session import PracticeSession

TRAINING_ANIMATION_MS = 1500


class TrainingSession:
    def __init__(self, pet, save):
        self.pet, self.save = pet, save
        self.index = 0
        self.techniques = None
        self.message = ""
        self.updated_at = None
        self.gain = None

    def busy(self, now_ms):
        return self.updated_at is not None and now_ms - self.updated_at < TRAINING_ANIMATION_MS

    def input(self, event, now_ms):
        if self.techniques is not None:
            if not self.techniques.input(event, now_ms):
                self.techniques = None
            return True
        if event == "back":
            return False
        if self.busy(now_ms):
            return True
        if event == "next":
            self.index = (self.index + 1) % (len(TRAINING_TYPES) + 2)
            self.message, self.gain = "", None
        elif event == "action":
            if self.index == len(TRAINING_TYPES) + 1:
                return False
            if self.index == len(TRAINING_TYPES):
                self.techniques = PracticeSession(self.pet, self.save, training=True)
                return True
            self.message = training_block_reason(self.pet, self.index)
            if self.message:
                return True
            self.gain = training_values(self.pet, self.index)
            if train_attribute(self.pet, self.index):
                self.updated_at = now_ms
                self.message = "%s +%d" % (TRAINING_TYPES[self.index]["name"], self.gain[1] - self.gain[0])
                if not self.save(self.pet):
                    self.message = "ERROR AL GUARDAR"
        return True
