"""Hatch genome helpers shared by Pet and the T-Display simulator."""
import math

COMBAT_STATS = ("hp", "mp", "off", "def", "spd", "brn")
SPECIES_ID = {
    "rookie": 0,
    "champion": 1,
    "ultimate": 2,
    "egg": 3,
    "baby": 4,
}
STATUS_PAGE_COUNT = 4


def mix_entropy(entropy):
    mix = (int(entropy) * 1664525 + 1013904223) & 0xFFFFFFFF
    dna = [mix & 0xFF, (mix >> 8) & 0xFF, (mix >> 16) & 0xFF, (mix >> 24) & 0xFF]
    if not any(dna):
        dna[0] = 1
    return dna


def iv_at(dna, stat):
    index = COMBAT_STATS.index(stat)
    packed = dna[index // 2]
    return packed & 0x0F if index % 2 == 0 else packed >> 4


def combat_stat(dna, ev, stat):
    value = 10 + iv_at(dna, stat) * 3 + int(ev.get(stat, 0)) // 6
    return max(1, min(99, value))


def format_dna_id(dna):
    if not dna or not any(dna):
        return "DNA: -- -- -- --"
    return "DNA: %02X-%02X-%02X-%02X" % tuple(int(byte) & 0xFF for byte in dna[:4])


def helix_color565(dna, strand):
    if not dna or not any(dna):
        return 0x7BEF
    if strand == 0:
        return ((dna[0] << 8) | dna[1]) & 0xFFFF
    return ((dna[2] << 8) | dna[3]) & 0xFFFF


def helix_x(strand, step, width=28):
    phase = ((-1, 0, 1, 0, -1), (1, 0, -1, 0, 1))
    mid = width // 2
    amp = width // 2 - 2
    return mid + amp * phase[strand & 1][step % 5]


HELIX_SPIN_MS = 2400
HELIX_TURNS = 1.0


def helix_spin(now_ms, period_ms=HELIX_SPIN_MS):
    if period_ms <= 0:
        return 0.0
    return ((int(now_ms) % int(period_ms)) / float(period_ms)) * 2.0 * math.pi


def helix_pose(dna=None):
    """Textbook open-top pose. Not tied to the clock, so Status 4/4 stays stable."""
    return math.pi / 2


def helix_sample(strand, t, width=32, turns=2.0, spin=0.0):
    mid = width / 2.0
    amp = width / 2.0 - 3
    angle = float(t) * turns * 2.0 * math.pi + float(spin)
    phase = 0.0 if (strand & 1) == 0 else math.pi
    return int(round(mid + amp * math.sin(angle + phase)))


def helix_depth(strand, t, turns=2.0, spin=0.0):
    angle = float(t) * turns * 2.0 * math.pi + float(spin)
    phase = 0.0 if (strand & 1) == 0 else math.pi
    return math.cos(angle + phase)


def rgb565_to_rgb(value):
    red = ((value >> 11) & 0x1F) * 255 // 31
    green = ((value >> 5) & 0x3F) * 255 // 63
    blue = (value & 0x1F) * 255 // 31
    return (red, green, blue)
