"""Portable breeding contract: eligibility, ancestry and exact host C++ parity."""

import copy
from pathlib import Path
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]


def identity(number):
    return "%032x" % number


def parent_values(number=1, **changes):
    values = dict(pet_id=identity(number), sex="M" if number == 1 else "F",
                  line_id="vpet.builtin", adult=True, health=80, hunger=60,
                  energy=70, happiness=60, injured=False, dead=False,
                  asleep=False, away=False, paused=False, busy=False,
                  cooldown_remaining=0, parents=(), grandparents=())
    values.update(changes)
    return values


def pair_cases():
    yield "eligible", {}, {}, True
    yield "same-id", {}, {"pet_id": identity(1)}, False
    yield "same-sex", {}, {"sex": "M"}, False
    yield "different-line", {}, {"line_id": "other"}, False
    yield "maximum-care", dict.fromkeys(("health", "hunger", "energy", "happiness"), 100), {}, True
    for field, threshold in (("health", 80), ("hunger", 60), ("energy", 70), ("happiness", 60)):
        yield field + "-low", {field: threshold - 1}, {}, False
        yield field + "-negative", {field: -1}, {}, False
        yield field + "-overflow", {field: 101}, {}, False
    yield "young", {"adult": False}, {}, False
    for field in ("injured", "dead", "asleep", "away", "paused", "busy"):
        yield field, {field: True}, {}, False
    for cooldown in (-1, 1, 86400, 0xFFFFFFFF, 0x100000000):
        yield "cooldown-%s" % cooldown, {"cooldown_remaining": cooldown}, {}, False
    for index, bad in enumerate(("", "0" * 32, "A" * 32, "f" * 31, "g" * 32, "f" * 33)):
        yield "bad-id-%s" % index, {"pet_id": bad}, {}, False
        yield "bad-parent-%s" % index, {"parents": (bad,)}, {}, bad == ""
        yield "bad-grandparent-%s" % index, {"grandparents": (bad,)}, {}, bad == ""
    for index, bad in enumerate(("", "x" * 64, "bad line", "bad\nline")):
        yield "bad-line-%s" % index, {"line_id": bad}, {}, False
    yield "maximum-line", {"line_id": "x" * 63}, {"line_id": "x" * 63}, True
    yield "unknown-sex", {"sex": ""}, {}, False
    yield "other-sex", {"sex": "MF"}, {}, False
    yield "self-parent", {"parents": (identity(1),)}, {}, False
    yield "self-grandparent", {"grandparents": (identity(1),)}, {}, False
    yield "duplicate-parent", {"parents": (identity(3), identity(3))}, {}, False
    yield "parent-child", {"parents": (identity(2),)}, {}, False
    yield "grandparent-child", {"grandparents": (identity(2),)}, {}, False
    yield "half-siblings", {"parents": (identity(3),)}, {"parents": (identity(3), identity(4))}, False
    yield "siblings", {"parents": (identity(3), identity(4))}, {"parents": (identity(4), identity(3))}, False
    yield "cousins", {"grandparents": (identity(3),)}, {"grandparents": (identity(3),)}, False
    yield "aunt-nephew", {"parents": (identity(3),)}, {"grandparents": (identity(3),)}, False
    yield "unrelated", {"parents": (identity(3), identity(4)), "grandparents": tuple(identity(i) for i in range(5, 9))}, {"parents": (identity(9), identity(10)), "grandparents": tuple(identity(i) for i in range(11, 15))}, True
    yield "unknown-is-not-shared", {"parents": ("", ""), "grandparents": ("",) * 4}, {"parents": ("", ""), "grandparents": ("",) * 4}, True
    yield "pedigree-collapse", {"grandparents": (identity(3), identity(3))}, {}, True


PAIR_CASES = list(pair_cases())


@pytest.mark.parametrize("name,left,right,allowed", PAIR_CASES, ids=[c[0] for c in PAIR_CASES])
def test_pair_rules_are_symmetric_and_pure(name, left, right, allowed):
    from core.breeding import Parent, check_pair
    a, b = Parent(**parent_values(**left)), Parent(**parent_values(2, **right))
    before = copy.deepcopy((vars(a), vars(b)))
    for _ in range(2):
        assert check_pair(a, b) is allowed, name
        assert check_pair(b, a) is allowed, name
    assert (vars(a), vars(b)) == before


@pytest.mark.parametrize("changes", [
    {"pet_id": None}, {"sex": 1}, {"line_id": None},
    {"adult": 1}, {"injured": 0}, {"busy": ""},
    {"health": True}, {"hunger": 60.0}, {"energy": "70"}, {"happiness": None},
    {"cooldown_remaining": True}, {"cooldown_remaining": 0.0},
    {"parents": None}, {"parents": ""}, {"parents": (None,)},
    {"parents": (identity(3),) * 3}, {"grandparents": (identity(3),) * 5},
    {"grandparents": {identity(3)}},
])
def test_malformed_python_parent_is_ineligible(changes):
    from core.breeding import Parent, check_pair
    a = Parent(**parent_values(**changes))
    b = Parent(**parent_values(2))
    assert not check_pair(a, b)
    assert not check_pair(b, a)


def test_parent_defaults_fail_closed_and_ancestry_is_a_value_copy():
    from core.breeding import Parent, check_pair
    assert not check_pair(Parent(), Parent())
    assert not check_pair(None, Parent(**parent_values(2)))
    source = [identity(3)]
    a = Parent(**parent_values(parents=source))
    source[0] = identity(2)
    assert tuple(a.parents) == (identity(3),)
    assert check_pair(a, Parent(**parent_values(2)))


GOLDEN = [
    (0, 14, [240, 220, 84, 152]), (1, 43, [254, 210, 180, 121]),
    (2, 59, [254, 210, 186, 150]), (31, 50, [240, 50, 186, 118]),
    (32, 19, [254, 50, 90, 120]), (1024, 49, [30, 50, 186, 118]),
    (0x80000000, 42, [240, 210, 180, 120]), (0xFFFFFFFF, 3, [254, 50, 84, 118]),
]


@pytest.mark.parametrize("seed,mask,expected", GOLDEN)
def test_dna_frozen_vectors(seed, mask, expected):
    from core.breeding import iv_source_mask, offspring_dna
    assert iv_source_mask(seed) == mask
    assert offspring_dna([0x10, 0x32, 0x54, 0x76], [0xFE, 0xDC, 0xBA, 0x98], seed) == bytes(expected)


def nibbles(dna):
    return [(dna[i // 2] >> (4 * (i % 2))) & 15 for i in range(8)]


def test_six_iv_mask_and_trait_inheritance_with_bounded_mutation():
    from core.breeding import iv_source_mask, offspring_dna
    masks, traits = set(), [set(), set()]
    a, b = bytes(4), bytes([255] * 4)
    for seed in range(1, 4097):
        mask = iv_source_mask(seed)
        assert 0 < mask < 63
        masks.add(mask)
        dna = offspring_dna(a, b, seed)
        assert dna == offspring_dna(a, b, seed)
        values = nibbles(dna)
        assert len(dna) == 4
        for locus in range(6):
            assert values[locus] in ((14, 15) if mask & (1 << locus) else (0, 1))
        for locus in range(2):
            assert values[6 + locus] in (0, 1, 14, 15)
            traits[locus].add(values[6 + locus] >= 14)
    assert masks == set(range(1, 63))
    assert traits == [{False, True}, {False, True}]


def test_mutation_rate_both_directions_and_clamp_at_each_of_eight_loci():
    from core.breeding import offspring_dna
    counts = [[0, 0] for _ in range(8)]
    for seed in range(16384):
        for locus, value in enumerate(nibbles(offspring_dna([0x88] * 4, [0x88] * 4, seed))):
            assert value in (7, 8, 9)
            if value != 8:
                counts[locus][value == 9] += 1
        for endpoint in (0, 15):
            values = nibbles(offspring_dna([endpoint * 17] * 4, [endpoint * 17] * 4, seed))
            assert all(v in ((0, 1) if endpoint == 0 else (14, 15)) for v in values)
    for down, up in counts:
        assert 0.025 < (down + up) / 16384 < 0.038
        assert down > 150 and up > 150


def test_equal_parent_dna_can_yield_equal_child_and_inputs_are_unchanged():
    from core.breeding import offspring_dna
    a, b = [0x88] * 4, bytearray([0x88] * 4)
    before = (a[:], b[:])
    assert any(offspring_dna(a, b, s) == bytes(a) for s in range(64))
    assert (a, b) == before


@pytest.mark.parametrize("bad", [None, "abcd", [], [0] * 3, [0] * 5,
                                     [0, 0, 0, -1], [256, 0, 0, 0],
                                     [True, 0, 0, 0], [1.0, 0, 0, 0]])
def test_reject_invalid_dna(bad):
    from core.breeding import offspring_dna
    with pytest.raises(ValueError):
        offspring_dna(bad, bytes(4), 1)
    with pytest.raises(ValueError):
        offspring_dna(bytes(4), bad, 1)


@pytest.mark.parametrize("seed", [-1, 0x100000000, True, 1.0, None, "1"])
def test_reject_non_uint32_seed(seed):
    from core.breeding import iv_source_mask, offspring_dna
    with pytest.raises(ValueError):
        iv_source_mask(seed)
    with pytest.raises(ValueError):
        offspring_dna(bytes(4), bytes(4), seed)


@pytest.fixture(scope="module")
def breeding_binary(tmp_path_factory):
    binary = tmp_path_factory.mktemp("breeding") / "trace"
    subprocess.run(["c++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-pedantic",
                    "-I" + str(ROOT / "firmware/t-display/lib/vpet_core/src"),
                    str(ROOT / "tests/breeding_trace.cpp"), "-o", str(binary)], check=True)
    return binary


def test_cpp_dna_parity_many_seeds_and_parent_genomes(breeding_binary):
    from core.breeding import iv_source_mask, offspring_dna
    genomes = [(bytes(4), bytes([255] * 4)), (bytes([0x88] * 4), bytes([0x88] * 4)),
               (bytes([0x10, 0x32, 0x54, 0x76]), bytes([0xFE, 0xDC, 0xBA, 0x98])),
               (bytes([0xFF, 0, 0x81, 0xA7]), bytes([0x13, 0x57, 0x9B, 0xDF]))]
    cases = [(a, b, seed) for a, b in genomes for seed in [0, *range(1, 1025), 0x7FFFFFFF, 0x80000000, 0xFFFFFFFE, 0xFFFFFFFF]]
    cases += [(bytes([v * 17] * 4), bytes([v * 17] * 4), seed) for v in range(16) for seed in range(128)]
    payload = "".join(" ".join(map(str, (seed, *a, *b))) + "\n" for a, b, seed in cases)
    rows = subprocess.check_output([str(breeding_binary), "dna"], input=payload, text=True).splitlines()
    assert rows == [" ".join(map(str, (iv_source_mask(s), *offspring_dna(a, b, s)))) for a, b, s in cases]


def cpp_parent(values):
    # std::quoted preserves literal whitespace and only escapes quotes/backslashes.
    def quoted(value):
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'

    fields = [quoted(values[key]) for key in ("pet_id", "sex", "line_id")]
    fields += [str(int(values[key])) for key in ("adult", "health", "hunger", "energy", "happiness",
               "injured", "dead", "asleep", "away", "paused", "busy", "cooldown_remaining")]
    for name, size in (("parents", 2), ("grandparents", 4)):
        fields += [quoted(v) for v in (*values[name], *("",) * (size - len(values[name])))]
    return " ".join(fields)


def test_cpp_pair_rules_match_python(breeding_binary):
    from core.breeding import Parent, check_pair
    cases = []
    for _, left, right, allowed in PAIR_CASES:
        a, b = parent_values(**left), parent_values(2, **right)
        cases.extend(((a, b, allowed), (b, a, allowed)))
    payload = "".join(cpp_parent(a) + " " + cpp_parent(b) + "\n" for a, b, _ in cases)
    rows = subprocess.check_output([str(breeding_binary), "pair"], input=payload, text=True).splitlines()
    assert rows == [str(int(allowed)) for _, _, allowed in cases]
    assert rows == [str(int(check_pair(Parent(**a), Parent(**b)))) for a, b, _ in cases]
