"""Portable policy contract, bounded persistence and independent C++ parity."""
import base64
import random
from pathlib import Path
import struct
import subprocess
import zlib

import pytest

ROOT = Path(__file__).resolve().parents[1]
HEADER_SIZE = 14
TABLE_END = HEADER_SIZE + 3 * 32 * 8 * 5
MAX_SEQUENCE = (1 << 64) - 1


def test_portable_implementations_exist():
    import importlib.util
    assert importlib.util.find_spec("core.learning") is not None, "portable learning is absent"
    assert (ROOT / "firmware/t-display/lib/vpet_core/src/vpet/Learning.h").is_file()


@pytest.fixture
def learning_type():
    from core.learning import LearningState
    return LearningState


@pytest.fixture(scope="module")
def learning_cpp(tmp_path_factory):
    header = ROOT / "firmware/t-display/lib/vpet_core/src/vpet/Learning.h"
    assert header.exists(), "portable C++ learning is absent"
    binary = tmp_path_factory.mktemp("learning") / "trace"
    result = subprocess.run([
        "c++", "-std=c++17", "-O2", "-Wall", "-Wextra", "-Werror", "-pedantic",
        "-I", str(header.parents[1]), str(ROOT / "tests/learning_trace.cpp"),
        "-o", str(binary),
    ], capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr
    return binary


def test_contiguous_sequence_replay_and_atomic_rejection(learning_type):
    state = learning_type()
    assert state.last_sequence == 0 and state.next_sequence == 1
    assert state.record(1, 0, 0, 0, 100)
    before = state.encode()
    assert not state.record(1, 0, 0, 0, 100)
    assert not state.record(0, 0, 0, 0, 100)
    assert not state.record(3, 0, 0, 0, 100)
    assert state.encode() == before
    assert state.last_sequence == 1 and state.next_sequence == 2
    assert state.record(2, 2, 31, 7, -100)
    assert state.estimate(0, 0, 0) == (100, 1, 0)
    assert state.estimate(2, 31, 7) == (-100, 1, 0)


@pytest.mark.parametrize("index,value", [
    (0, -1), (0, MAX_SEQUENCE + 1), (0, True), (0, 1.0),
    (1, -1), (1, 3), (1, False), (1, "0"),
    (2, -1), (2, 32), (2, 0.5), (3, -1), (3, 8), (3, True),
    (4, -101), (4, 101), (4, False), (4, 50.0), (4, None),
])
def test_record_rejects_bad_numbers_without_mutation(learning_type, index, value):
    state = learning_type()
    before = state.encode()
    args = [1, 0, 0, 0, 0]
    args[index] = value
    assert state.record(*args) is False
    assert state.encode() == before


def test_mask_fallback_ties_and_learned_reward(learning_type):
    state = learning_type()
    assert state.choose(0, 0, 0, 0) == -1
    assert state.choose(0, 0, 0b1010, 3) == 3
    assert state.choose(0, 0, 0b1010, 0) == 1
    assert state.choose(0, 0, 0b1010, -1) == 1
    assert state.record(1, 0, 0, 1, 6)
    assert state.choose(0, 0, 0b1010, 3) == 1
    assert state.choose(0, 1, 0b1010, 3) == 3
    assert state.choose(1, 0, 0b1010, 3) == 3
    assert state.choose(0, 0, 0b1000, 3) == 3
    for mask in range(256):
        for fallback in range(-1, 8):
            choice = state.choose(0, 0, mask, fallback)
            assert (choice == -1 and mask == 0) or (0 <= choice < 8 and mask & (1 << choice))


@pytest.mark.parametrize("args", [
    (-1, 0, 255, 0), (3, 0, 255, 0), (0, 32, 255, 0), (0, -1, 255, 0),
    (True, 0, 255, 0), (0, 0.0, 255, 0), (0, 0, -1, 0), (0, 0, 256, 0),
    (0, 0, True, 0), (0, 0, 1.0, 0), (0, 0, 255, -2), (0, 0, 255, 8),
    (0, 0, 255, False), (0, 0, 255, 1.0),
])
def test_choose_rejects_invalid_numbers(learning_type, args):
    state = learning_type()
    before = state.encode()
    assert state.choose(*args) == -1
    assert state.encode() == before


def test_saturated_counts_remain_adaptive_and_history_is_bounded(learning_type):
    state = learning_type()
    for sequence in range(1, 65541):
        assert state.record(sequence, 1, 3, 2, 100)
    assert state.estimate(1, 3, 2) == (100, 65535, 0)
    assert state.choose(1, 3, 0b1100, 3) == 2
    old = state.encode()
    assert not state.record(1, 1, 3, 2, -100)
    assert state.encode() == old
    for _ in range(64):
        assert state.record(state.next_sequence, 1, 3, 2, -100)
    mean, count, _ = state.estimate(1, 3, 2)
    assert mean == -100 and count == 65535
    assert state.choose(1, 3, 0b1100, 3) == 3
    assert len(state.history) == 256
    assert state.history[0].sequence == state.last_sequence - 255
    assert state.history[-1].sequence == state.last_sequence
    assert len(base64.b64decode(state.encode())) == 6930
    assert len(state.encode()) == 9240 <= 12 * 1024
    restored = learning_type.decode(state.encode())
    assert restored.encode() == state.encode()
    assert restored.record(restored.next_sequence, 0, 0, 0, -1)


def test_inheritance_normalizes_bias_and_does_not_copy_experience(learning_type):
    a, b = learning_type(), learning_type()
    for parent in (a, b):
        assert parent.record(1, 0, 0, 0, 100)
        assert parent.record(2, 0, 0, 1, -100)
    snapshots = a.encode(), b.encode()
    child = learning_type.inherited(a, b)
    assert (a.encode(), b.encode()) == snapshots
    assert child.last_sequence == 0 and child.next_sequence == 1 and child.history == ()
    assert child.estimate(0, 0, 0) == (0, 0, 25)
    assert child.estimate(0, 0, 1) == (0, 0, -25)
    assert child.choose(0, 0, 0b11, 1) == 0
    for _ in range(24):
        assert child.record(child.next_sequence, 0, 0, 0, -100)
        assert child.record(child.next_sequence, 0, 0, 1, 100)
    assert child.choose(0, 0, 0b11, 0) == 1
    for _ in range(64):
        assert child.record(child.next_sequence, 0, 0, 0, 100)
        assert child.record(child.next_sequence, 0, 0, 1, -100)
    assert child.choose(0, 0, 0b11, 1) == 0
    for _ in range(20):
        child = learning_type.inherited(child, child)
        assert all(abs(child.estimate(0, 0, action).bias) <= 25 for action in range(8))
        assert child.last_sequence == 0 and child.history == ()
    # A common reward offset is not a preference, and an unvisited row is neutral.
    flat = learning_type()
    for action in range(8):
        assert flat.record(action + 1, 2, 31, action, 80)
    neutral = learning_type.inherited(flat, flat)
    assert all(neutral.estimate(2, 31, action) == (0, 0, 0) for action in range(8))


def checksum(data):
    return bytes(data[:-4]) + struct.pack("<I", zlib.crc32(data[:-4]))


def malformed_records(state):
    good = base64.b64decode(state.encode())
    records = [b"", good[:-1], good + b"\0", good[:4], b"x" * 12289]
    for offset in range(len(good)):
        mutated = bytearray(good)
        mutated[offset] ^= 1
        records.append(bytes(mutated))  # Every byte is covered by CRC.
    for offset, value, fmt in [
        (0, ord("X"), "B"), (3, ord("2"), "B"),
        (12, 257, "H"), (12, 0, "H"),
        (HEADER_SIZE, 101, "h"), (HEADER_SIZE, -101, "h"),
        (HEADER_SIZE + 2, 0, "H"), (HEADER_SIZE + 4, 26, "b"),
        (HEADER_SIZE + 5 + 4, -26, "b"),
        (TABLE_END, 0, "Q"), (TABLE_END, 3, "Q"),
        (TABLE_END + 8, 3, "B"), (TABLE_END + 9, 32, "B"),
        (TABLE_END + 10, 8, "B"), (TABLE_END + 11, 101, "b"),
        (TABLE_END + 12, 1, "Q"),
    ]:
        mutated = bytearray(good)
        struct.pack_into("<" + fmt, mutated, offset, value)
        records.append(checksum(mutated))  # Semantic faults even with a fresh CRC.
    return [base64.b64encode(record).decode("ascii") for record in records]


def test_codec_is_canonical_strict_and_round_trips(learning_type):
    state = learning_type()
    empty = b"VPL1" + struct.pack("<QH", 0, 0) + bytes(3840)
    empty += struct.pack("<I", zlib.crc32(empty))
    assert state.encode() == base64.b64encode(empty).decode("ascii")
    assert state.record(1, 0, 0, 0, 100)
    assert state.record(2, 2, 31, 7, -100)
    good = state.encode()
    assert learning_type.decode(good).encode() == good
    assert learning_type.decode(good).history == state.history
    for malformed in malformed_records(state):
        with pytest.raises(ValueError):
            learning_type.decode(malformed)
        assert state.encode() == good
    for bad in (None, "", True, 123, good.encode(), bytearray(good.encode()),
                memoryview(good.encode()), good + "\n", " " + good, good[:-1],
                good + "=", good.replace("A", "!", 1), "\u00e9" + good[1:]):
        with pytest.raises(ValueError):
            learning_type.decode(bad)
    with pytest.raises(ValueError):
        state.estimate(3, 0, 0)


def test_sequence_exhaustion_does_not_wrap(learning_type):
    state = learning_type()
    for _ in range(256):
        assert state.record(state.next_sequence, 0, 0, 0, 100)
    wire = bytearray(base64.b64decode(state.encode()))
    struct.pack_into("<Q", wire, 4, MAX_SEQUENCE - 1)
    struct.pack_into("<H", wire, HEADER_SIZE + 2, 65535)
    for index in range(256):
        struct.pack_into("<Q", wire, TABLE_END + index * 12, MAX_SEQUENCE - 256 + index)
    state = learning_type.decode(base64.b64encode(checksum(wire)).decode("ascii"))
    assert state.next_sequence == MAX_SEQUENCE
    assert state.record(MAX_SEQUENCE, 0, 0, 0, -100)
    assert state.last_sequence == MAX_SEQUENCE and state.next_sequence == 0
    before = state.encode()
    assert not state.record(0, 0, 0, 0, 0)
    assert not state.record(MAX_SEQUENCE, 0, 0, 0, 0)
    assert state.encode() == before


def run_cpp(binary, commands):
    result = subprocess.run([str(binary)], input="\n".join(commands) + "\n",
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    return result.stdout.splitlines()


def test_cpp_self_checks(learning_cpp):
    line, = run_cpp(learning_cpp, ["selftest"])
    status, event, state = line.split("; ")
    assert status == "selftest ok"
    assert int(event.split("=")[1]) <= 32
    assert int(state.split("=")[1]) <= 8192


def test_seeded_python_cpp_decisions_and_exact_wire_parity(learning_type, learning_cpp):
    state = learning_type()
    commands, expected = [], []
    rng = random.Random(0x25C011EC)
    for index in range(1600):
        sequence = state.next_sequence
        domain, context, action = rng.randrange(3), rng.randrange(32), rng.randrange(8)
        reward = rng.randint(-100, 100)
        if index % 17 == 0:
            sequence += 1  # Gap must not consume the next receipt.
        elif index % 19 == 0:
            sequence = max(0, sequence - 1)
        args = sequence, domain, context, action, reward
        commands.append("record " + " ".join(map(str, args)))
        expected.append(str(int(state.record(*args))))
        mask, fallback = rng.randrange(256), rng.randrange(-1, 8)
        commands.append(f"choose {domain} {context} {mask} {fallback}")
        expected.append(str(state.choose(domain, context, mask, fallback)))
        if index % 200 == 0:
            commands += ["encode", "inherit", "encode"]
            expected += [state.encode(), "1"]
            state = learning_type.inherited(state, state)
            expected.append(state.encode())
    commands += ["encode", "sequence"]
    expected += [state.encode(), f"{state.last_sequence} {state.next_sequence}"]
    assert run_cpp(learning_cpp, commands) == expected
    assert run_cpp(learning_cpp, ["decode " + state.encode(), "encode"]) == ["1", state.encode()]


def test_cpp_saturation_and_exhaustion_match_python(learning_type, learning_cpp):
    state = learning_type()
    for _ in range(65540):
        assert state.record(state.next_sequence, 1, 3, 2, 100)
    for _ in range(64):
        assert state.record(state.next_sequence, 1, 3, 2, -100)
    assert run_cpp(learning_cpp, ["saturate", "encode"]) == ["1", state.encode()]
    wire = bytearray(base64.b64decode(state.encode()))
    struct.pack_into("<Q", wire, 4, MAX_SEQUENCE - 1)
    for index in range(256):
        struct.pack_into("<Q", wire, TABLE_END + index * 12, MAX_SEQUENCE - 256 + index)
    wire = base64.b64encode(checksum(wire)).decode("ascii")
    state = learning_type.decode(wire)
    assert state.record(MAX_SEQUENCE, 0, 0, 0, -100)
    assert run_cpp(learning_cpp, [
        "decode " + wire, f"record {MAX_SEQUENCE} 0 0 0 -100", "sequence", "encode",
    ]) == ["1", "1", f"{MAX_SEQUENCE} 0", state.encode()]


def test_cpp_decode_rejects_corruption_atomically(learning_type, learning_cpp):
    state = learning_type()
    assert state.record(1, 0, 0, 0, 100)
    assert state.record(2, 2, 31, 7, -100)
    good = state.encode()
    commands, expected = ["decode " + good], ["1"]
    for bad in malformed_records(state):
        commands += ["decode " + (bad or "-"), "encode"]
        expected += ["0", good]
    assert run_cpp(learning_cpp, commands) == expected
