"""Individual identity is separate from DNA, species and asset packages."""
import copy
import json
from pathlib import Path
import subprocess

import pytest
from core.pet import Pet
from scripts.sim_services import SimulatorServices

ROOT = Path(__file__).resolve().parents[1]


def test_pet_has_unassigned_profile_until_persistence_allocates_it():
    assert Pet().profile.encode() == ""


def test_profile_codec_sex_and_parentage():
    from core.profile import PetProfile
    a = PetProfile.from_words((2, 3, 4, 5))
    b = PetProfile.from_words((3, 3, 4, 5))
    assert a.encode() == "1:00000002000000030000000400000005:M:-:-"
    assert b.sex == "F"
    child = PetProfile.from_words((4, 5, 6, 7), a.pet_id, b.pet_id)
    assert PetProfile.decode(child.encode()).encode() == child.encode()
    assert child.parent_a == a.pet_id and child.parent_b == b.pet_id
    assert sum(PetProfile.from_words((n, 3, 4, 5)).sex == "M" for n in range(1024)) == 512
    for bad in ("99:future", "1:" + "0"*32 + ":M:-:-", a.encode()+"\n",
                a.encode().replace(":M:", ":X:"), a.encode().replace(":-:-", ":-:"+b.pet_id),
                a.encode().replace(":-:-", ":"+a.pet_id+":"+b.pet_id),
                child.encode().replace(b.pet_id, a.pet_id), "1:"+"A"*32+":M:-:-"):
        with pytest.raises(ValueError):
            PetProfile.decode(bad)


def test_profile_survives_hatch_evolution_and_save_but_not_new_life(tmp_path):
    services = SimulatorServices(tmp_path)
    p = Pet()
    assert services.save(p)
    profile = p.profile.encode()
    assert profile
    p.complete_hatch("baby", entropy=42)
    dna = list(p.dna)
    for species in ("rookie", "champion", "ultimate"):
        p.species = species
        p.reset_after_evolution()
        assert p.profile.encode() == profile and p.dna == dna
    assert services.save(p)
    q = Pet()
    assert services.load(q) and q.profile.encode() == profile
    q.reset_to_egg()
    assert q.profile.encode() == ""
    assert services.save(q) and q.profile.encode() != profile


def test_legacy_migration_is_durable_without_gene_or_progress_changes(tmp_path):
    services = SimulatorServices(tmp_path)
    p = Pet(species="rookie", state="live")
    p.restore_dna([10, 20, 30, 40])
    p.ev["off"] = 252
    data = p.to_dict()
    data.pop("profile", None)
    services.save_path.parent.mkdir(parents=True)
    services.save_path.write_text(json.dumps(data))
    q = Pet()
    assert services.load(q)
    profile = q.profile.encode()
    assert profile and q.dna == p.dna and q.ev == p.ev
    disk = json.loads(services.save_path.read_text())
    assert disk["profile"] == profile
    for key, value in data.items():
        assert disk[key] == value
    r = Pet()
    assert SimulatorServices(tmp_path).load(r) and r.profile.encode() == profile


def test_failed_migration_and_corrupt_profile_never_overwrite_save(tmp_path, monkeypatch):
    services = SimulatorServices(tmp_path)
    services.save_path.parent.mkdir(parents=True)
    data = Pet().to_dict()
    data.pop("profile", None)
    services.save_path.write_text(json.dumps(data))
    old = services.save_path.read_bytes()
    p = Pet()
    before = copy.deepcopy(p.to_dict())
    born_at, last_decay = p.born_at, p.last_decay
    with monkeypatch.context() as m:
        m.setattr("scripts.sim_services.os.replace", lambda *_: (_ for _ in ()).throw(OSError("full")))
        assert not services.load(p)
    assert p.to_dict() == before and services.save_path.read_bytes() == old
    assert p.born_at == born_at and p.last_decay == last_decay
    assert services.load(p) and p.profile.encode()
    data["profile"] = "2:future"
    services.save_path.write_text(json.dumps(data))
    old = services.save_path.read_bytes()
    assert not services.load(p)
    assert not services.save(Pet())
    assert services.save_path.read_bytes() == old


@pytest.fixture(scope="module")
def profile_board(tmp_path_factory):
    binary = tmp_path_factory.mktemp("profile-board") / "profile"
    core = ROOT / "firmware/t-display/lib/vpet_core/src"
    subprocess.run(["c++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-I", str(core),
                    str(ROOT / "tests/pet_profile.cpp"),
                    *[str(core / "vpet" / n) for n in ("PetState.cpp", "Nutrition.cpp", "SettingsStore.cpp")],
                    "-o", str(binary)], check=True, capture_output=True, text=True)
    return binary


def test_firmware_profile_migration_and_power_loss(profile_board):
    result = subprocess.run([str(profile_board)], capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stdout + result.stderr


def test_python_cpp_codec_parity(profile_board):
    from core.profile import PetProfile
    result = subprocess.run([str(profile_board), "trace"], capture_output=True, text=True, check=True)
    assert result.stdout.splitlines() == [PetProfile.from_words((n, 3, 4, 5)).encode() for n in range(1024)]


def test_canonical_records_and_parent_validation_match_cpp(profile_board):
    from core.profile import PetProfile
    a = PetProfile.from_words((2, 3, 4, 5))
    b = PetProfile.from_words((3, 3, 4, 5))
    child = PetProfile.from_words((4, 5, 6, 7), a.pet_id, b.pet_id)
    records = ["", a.encode(), child.encode(), "2:future", "1:"+"0"*32+":M:-:-",
               a.encode()+"\n", a.encode().replace(":M:", ":X:"),
               a.encode().replace(":-:-", ":-:"+b.pet_id),
               a.encode().replace(":-:-", ":"+a.pet_id+":"+b.pet_id),
               child.encode().replace(b.pet_id, a.pet_id), "1:"+"A"*32+":M:-:-",
               a.encode().replace(":-:-", "::"), "x"*5000]
    for record in records:
        try:
            expected = PetProfile.decode(record).encode()
        except ValueError:
            expected = "!"
        result = subprocess.run([str(profile_board), "decode", record], capture_output=True, text=True, check=True)
        assert result.stdout.rstrip("\n") == expected


def test_new_pets_with_same_dna_are_distinct_and_sex_has_no_combat_effect(tmp_path):
    from core.profile import PetProfile
    from core.dna import COMBAT_STATS
    services = SimulatorServices(tmp_path)
    a, b = Pet(species="rookie", state="live"), Pet(species="rookie", state="live")
    for p in (a, b):
        p.restore_dna([10, 20, 30, 40])
        assert services.save(p)
    assert a.profile.pet_id != b.profile.pet_id
    a.profile = PetProfile.from_words((2, 3, 4, 5))
    b.profile = PetProfile.from_words((3, 3, 4, 5))
    assert a.profile.sex != b.profile.sex
    assert [a.combat_stat(s) for s in COMBAT_STATS] == [b.combat_stat(s) for s in COMBAT_STATS]
    child = PetProfile.from_words((4, 5, 6, 7), a.profile.pet_id, b.profile.pet_id)
    a.profile = child
    assert services.save(a)
    restored = Pet()
    assert services.load(restored) and restored.profile.encode() == child.encode()


def test_rejected_save_does_not_publish_candidate_identity(tmp_path, monkeypatch):
    services = SimulatorServices(tmp_path)
    p = Pet()
    monkeypatch.setattr("scripts.sim_services.os.replace", lambda *_: (_ for _ in ()).throw(OSError("full")))
    assert not services.save(p) and p.profile.encode() == ""
    assert not services.save_path.exists()


def test_simulator_start_persists_egg_before_play_and_blocks_invalid_save(tmp_path):
    services = SimulatorServices(tmp_path)
    egg = Pet()
    assert services.start(egg) and egg.is_egg and egg.profile.pet_id
    identity = egg.profile.encode()
    reboot = Pet()
    assert services.start(reboot) and reboot.profile.encode() == identity
    invalid = json.loads(services.save_path.read_text())
    invalid["profile"] = "99:future"
    services.save_path.write_text(json.dumps(invalid))
    assert not services.start(Pet())


def test_board_entropy_is_seeded_before_radio_and_failure_is_closed(tmp_path):
    binary = tmp_path / "random"
    firmware = ROOT / "firmware/t-display"
    result = subprocess.run(["c++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
                            "-I", str(ROOT / "tests/profile_random_stubs"),
                            "-I", str(firmware / "include"), "-I", str(firmware / "lib/vpet_core/src"),
                            str(ROOT / "tests/profile_random.cpp"), str(firmware / "src/ProfileRandom.cpp"),
                            "-o", str(binary)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    subprocess.run([str(binary)], check=True, timeout=5)
