"""Bounded, deterministic per-individual learning; no runtime/save side effects.

Contract v1: domains 0..2 (training, combat, exploration), contexts 0..31,
actions 0..7, rewards -100..100. Adapters define contexts and legal masks.
Only the contiguous next uint64 receipt learns; replay/gaps/invalid inputs
return False without mutation. next_sequence is 0 after uint64 exhaustion.

An estimate is (signed mean, uint16 count, inherited bias). On each sample,
move mean toward reward by abs(delta)//min(new_count, 8), at least one unit
when delta != 0. Count saturates at 65535; adaptation continues. Scores are
mean+bias+5 for a legal fallback, otherwise mean+bias. Ties prefer fallback,
then the lowest action. Invalid choose inputs or an empty mask return -1.
Inheritance centers the parents' combined mean+bias per eight-action row,
scales the largest absolute deviation to 25, and truncates toward zero.
Only bias is inherited: counts, means, receipts and history start at zero.

Codec: ASCII base64 of little-endian VPL1, uint64 last, uint16 history size,
768 domain/context/action ordered (int16 mean, uint16 count, int8 bias) cells,
oldest-first (uint64 sequence, uint8 domain/context/action, int8 reward) events,
then IEEE CRC32 of all preceding bytes. Exact size is 3858+12*n bytes before
base64 (max 6930), 5144+16*n ASCII chars (max 9240). Empty state has a real
encoding; missing/corrupt/future records raise ValueError, never reset state.
"""
import base64
import binascii
from collections import namedtuple
import struct
import zlib

LearningEstimate = namedtuple("LearningEstimate", "mean count bias")
LearningEvent = namedtuple("LearningEvent", "sequence domain context action reward")

DOMAINS, CONTEXTS, ACTIONS = 3, 32, 8
HISTORY_CAPACITY = 256
MAX_SEQUENCE = (1 << 64) - 1
MAX_ENCODED_SIZE = 9240
_CELLS = DOMAINS * CONTEXTS * ACTIONS
_HEADER = struct.Struct("<4sQH")
_CELL = struct.Struct("<hHb")
_EVENT = struct.Struct("<QBBBb")
_BASE_SIZE = _HEADER.size + _CELLS * _CELL.size + 4


def _integer(value, low, high):
    return type(value) is int and low <= value <= high


def _index(domain, context, action):
    if not (_integer(domain, 0, 2) and _integer(context, 0, 31) and _integer(action, 0, 7)):
        return None
    return (domain * CONTEXTS + context) * ACTIONS + action


def _trunc(numerator, denominator):
    return (1 if numerator >= 0 else -1) * (abs(numerator) // denominator)


def _update(mean, count, reward):
    count = min(count + 1, 65535)
    delta = reward - mean
    step = max(1, abs(delta) // min(count, 8)) if delta else 0
    return mean + (step if delta > 0 else -step), count


class LearningState:
    def __init__(self):
        self._means = [0] * _CELLS
        self._counts = [0] * _CELLS
        self._biases = [0] * _CELLS
        self._last_sequence = 0
        self._events = [None] * HISTORY_CAPACITY
        self._head = 0
        self._size = 0

    @property
    def last_sequence(self):
        return self._last_sequence

    @property
    def next_sequence(self):
        return self._last_sequence + 1 if self._last_sequence < MAX_SEQUENCE else 0

    @property
    def history(self):
        """Immutable oldest-first snapshot of at most 256 immutable events."""
        return tuple(self._events[(self._head + i) % HISTORY_CAPACITY] for i in range(self._size))

    def estimate(self, domain, context, action):
        index = _index(domain, context, action)
        if index is None:
            raise ValueError("Invalid learning cell")
        return LearningEstimate(self._means[index], self._counts[index], self._biases[index])

    def record(self, sequence, domain, context, action, reward):
        index = _index(domain, context, action)
        if (index is None or not _integer(sequence, 1, MAX_SEQUENCE) or
                not _integer(reward, -100, 100) or sequence != self.next_sequence):
            return False
        self._means[index], self._counts[index] = _update(self._means[index], self._counts[index], reward)
        event = LearningEvent(sequence, domain, context, action, reward)
        self._events[(self._head + self._size) % HISTORY_CAPACITY] = event
        if self._size < HISTORY_CAPACITY:
            self._size += 1
        else:
            self._head = (self._head + 1) % HISTORY_CAPACITY
        self._last_sequence = sequence
        return True

    def choose(self, domain, context, legal_mask, fallback):
        start = _index(domain, context, 0)
        if (start is None or not _integer(legal_mask, 0, 255) or
                not _integer(fallback, -1, 7)):
            return -1
        best, best_score = -1, -1000
        for action in range(ACTIONS):
            if not legal_mask & (1 << action):
                continue
            score = self._means[start + action] + self._biases[start + action] + (5 if action == fallback else 0)
            if score > best_score or (score == best_score and action == fallback):
                best, best_score = action, score
        return best

    @classmethod
    def inherited(cls, a, b):
        if not isinstance(a, cls) or not isinstance(b, cls):
            raise ValueError("Expected two learning states")
        child = cls()
        for row in range(0, _CELLS, ACTIONS):
            scores = [a._means[i] + a._biases[i] + b._means[i] + b._biases[i]
                      for i in range(row, row + ACTIONS)]
            total = sum(scores)
            centered = [ACTIONS * score - total for score in scores]
            peak = max(abs(score) for score in centered)
            if peak:
                child._biases[row:row + ACTIONS] = [_trunc(25 * score, peak) for score in centered]
        return child

    def encode(self):
        raw = bytearray(_HEADER.pack(b"VPL1", self._last_sequence, self._size))
        for cell in zip(self._means, self._counts, self._biases):
            raw.extend(_CELL.pack(*cell))
        for event in self.history:
            raw.extend(_EVENT.pack(*event))
        raw.extend(struct.pack("<I", zlib.crc32(raw)))
        return base64.b64encode(raw).decode("ascii")

    @classmethod
    def decode(cls, record):
        """Construct a validated candidate; no existing object is modified."""
        if type(record) is not str or not 5144 <= len(record) <= MAX_ENCODED_SIZE:
            raise ValueError("Invalid learning record size or type")
        try:
            raw = base64.b64decode(record, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise ValueError("Invalid learning base64") from exc
        if (base64.b64encode(raw).decode("ascii") != record or len(raw) < _BASE_SIZE or
                raw[:4] != b"VPL1" or zlib.crc32(raw[:-4]) != struct.unpack_from("<I", raw, len(raw) - 4)[0]):
            raise ValueError("Invalid learning format/version/checksum")
        _, last, size = _HEADER.unpack_from(raw)
        if size != min(last, HISTORY_CAPACITY) or len(raw) != _BASE_SIZE + size * _EVENT.size:
            raise ValueError("Invalid learning history length")
        candidate = cls()
        candidate._last_sequence, candidate._size = last, size
        offset = _HEADER.size
        for index in range(_CELLS):
            mean, count, bias = _CELL.unpack_from(raw, offset)
            offset += _CELL.size
            if not (-100 <= mean <= 100 and -25 <= bias <= 25) or (not count and mean):
                raise ValueError("Invalid learning estimate")
            candidate._means[index], candidate._counts[index], candidate._biases[index] = mean, count, bias
        total = sum(candidate._counts)
        if total > last or (65535 not in candidate._counts and total != last):
            raise ValueError("Learning counts disagree with receipts")
        tail_means, tail_counts = [0] * _CELLS, [0] * _CELLS
        for i in range(size):
            event = LearningEvent(*_EVENT.unpack_from(raw, offset))
            offset += _EVENT.size
            index = _index(event.domain, event.context, event.action)
            if (index is None or not -100 <= event.reward <= 100 or event.sequence != last - size + i + 1):
                raise ValueError("Invalid learning event")
            candidate._events[i] = event
            tail_means[index], tail_counts[index] = _update(tail_means[index], tail_counts[index], event.reward)
        for i in range(_CELLS):
            if (candidate._counts[i] < tail_counts[i] or
                    (candidate._counts[i] == tail_counts[i] and candidate._means[i] != tail_means[i])):
                raise ValueError("Learning summary disagrees with retained history")
        return candidate
