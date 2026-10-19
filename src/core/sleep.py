"""Deterministic civil-night cues and learned, explicitly started sleep."""

DAY = 86400
EARLIEST, LATEST = 18 * 60, 23 * 60


def is_night(minute):
    return minute >= EARLIEST or minute < 6 * 60


class SleepRoutine:
    FIELDS = ('bedtime', 'target', 'samples', 'learned_night', 'asleep', 'elapsed',
              'required', 'carry', 'session_night', 'session_minute', 'trait',
              'reward_night', 'sub_ms')

    def __init__(self, data=None):
        self.bedtime = self.target = self.samples = 0
        self.learned_night = self.session_night = self.reward_night = -1
        self.asleep = False
        self.elapsed = self.required = self.carry = self.session_minute = self.sub_ms = 0
        self.trait = 1
        self.physical_tired = False
        if data is not None:
            values = data if isinstance(data, dict) else {}
            if values.get('version') != 1:
                raise ValueError('Unsupported sleep routine')
            fields = [values.get(k) for k in self.FIELDS]
            if any(not isinstance(v, (int, bool)) for v in fields):
                raise ValueError('Invalid sleep fields')
            for key, value in zip(self.FIELDS, fields):
                setattr(self, key, value)
            if not self._valid():
                raise ValueError('Invalid sleep routine bounds')
            self.asleep = bool(self.asleep)

    def _valid(self):
        return (self.bedtime in (0,) or EARLIEST <= self.bedtime <= LATEST) and (
            self.target == 0 or EARLIEST <= self.target <= LATEST) and (
            0 <= self.samples <= 3 and -1 <= self.learned_night <= 100000 and
            self.asleep in (False, True) and 0 <= self.elapsed <= self.required <= 43200 and
            0 <= self.carry < 300 and -1 <= self.session_night <= 100000 and
            0 <= self.session_minute < 1440 and 0 <= self.trait <= 2 and
            -1 <= self.reward_night <= 100000 and 0 <= self.sub_ms < 1000 and
            (not self.asleep or self.required >= 1800))

    def preferred(self, trait):
        return self.bedtime or EARLIEST + (2 - trait % 3) * 15

    def tired(self, energy, trait, minute=None):
        if self.asleep:
            return False
        threshold = 20 + trait % 3 * 5
        if energy <= threshold:
            self.physical_tired = True
        elif energy >= threshold + 10:
            self.physical_tired = False
        scheduled = minute is not None and (minute >= self.preferred(trait) or minute < 360)
        return self.physical_tired or scheduled

    def start(self, civil_seconds, trait):
        if self.asleep:
            return False
        self.trait = trait % 3
        self.session_minute = civil_seconds % DAY // 60
        night = civil_seconds >= 1704067200 and is_night(self.session_minute)
        self.session_night = (civil_seconds - 21600) // DAY if night else -1
        until_dawn = (21600 - civil_seconds % DAY) % DAY
        self.required = max(28800, until_dawn) if night else 1800
        self.elapsed = self.carry = self.sub_ms = 0
        self.asleep = True
        return True

    def _learn(self):
        if self.session_night <= self.learned_night or not EARLIEST <= self.session_minute <= LATEST:
            return
        self.learned_night = self.session_night
        if self.samples and abs(self.target - self.session_minute) <= 30:
            self.samples = min(3, self.samples + 1)
            self.target = (self.target + self.session_minute) // 2
        else:
            self.target, self.samples = self.session_minute, 1
        if self.samples == 3:
            before = self.preferred(self.trait)
            self.bedtime = max(EARLIEST, min(LATEST, before + max(-15, min(15, self.target - before))))

    def stop(self):
        self.asleep = False

    def advance(self, seconds, energy):
        if not self.asleep:
            return energy, False, False
        seconds = max(0, min(int(seconds), self.required - self.elapsed))
        self.elapsed += seconds
        amount, self.carry = divmod(self.carry + seconds, 300)
        energy = min(100, energy + amount)
        complete = self.elapsed >= self.required
        reward = False
        if complete:
            self.asleep = False
            if self.session_night >= 0:
                self._learn()
                reward = self.session_night > self.reward_night
                self.reward_night = max(self.reward_night, self.session_night)
        return energy, complete, reward

    def advance_ms(self, milliseconds, energy):
        if not self.asleep:
            return energy, False, False
        seconds, self.sub_ms = divmod(self.sub_ms + max(0, int(milliseconds)), 1000)
        return self.advance(seconds, energy)

    def to_dict(self):
        return dict(version=1, **{key: getattr(self, key) for key in self.FIELDS})

    def encode(self):
        return ','.join(str(int(v)) for v in [1] + [getattr(self, k) for k in self.FIELDS])

    @classmethod
    def decode(cls, value):
        if not value:
            return cls()
        pieces = value.split(',')
        if len(pieces) != len(cls.FIELDS) + 1:
            raise ValueError('Invalid sleep record')
        numbers = [int(v) for v in pieces]
        return cls(dict(version=numbers[0], **dict(zip(cls.FIELDS, numbers[1:]))))
