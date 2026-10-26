import copy
import json

from core.pet import Pet
from scripts.sim_services import SimulatorServices


def test_collection_is_explicit_and_legacy_save_is_preserved(tmp_path):
    services = SimulatorServices(tmp_path)
    pet = Pet()
    assert services.start(pet)
    original = services.save_path.read_bytes()
    assert not services.enable_collection(pet, confirmed=False)
    assert services.enable_collection(pet, confirmed=True)
    assert services.save_path.read_bytes() == original
    assert services.add_founder(pet, confirmed=True)
    assert len(services.collection.slots) == 2
    assert services.switch_individual(pet, 1, confirmed=True)
    assert services.save_path.read_bytes() == original
    second_id = pet.profile.pet_id
    restored = Pet()
    fresh = SimulatorServices(tmp_path)
    assert fresh.start(restored)
    assert restored.profile.pet_id == second_id
    assert len(fresh.collection.slots) == 2


def test_failed_founder_or_switch_does_not_publish_memory_state(tmp_path, monkeypatch):
    services = SimulatorServices(tmp_path)
    pet = Pet()
    assert services.start(pet) and services.enable_collection(pet, confirmed=True)
    before = pet.to_dict()
    encoded = services.collection.encode()
    monkeypatch.setattr("scripts.collection_store.os.replace", lambda *_: (_ for _ in ()).throw(OSError("full")))
    assert not services.add_founder(pet, confirmed=True)
    assert services.collection.encode() == encoded
    assert pet.to_dict() == before


def test_ordinary_save_updates_shared_bag_and_never_restores_founder_defaults(tmp_path):
    services = SimulatorServices(tmp_path)
    pet = Pet()
    assert services.start(pet) and services.enable_collection(pet, confirmed=True)
    assert services.add_founder(pet, confirmed=True)
    pet.inventory["energy"] = 0
    assert services.save(pet)
    assert services.switch_individual(pet, 1, confirmed=True)
    assert pet.inventory["energy"] == 0
    fresh = SimulatorServices(tmp_path)
    restored = Pet()
    assert fresh.start(restored) and restored.inventory["energy"] == 0


def test_corrupt_collection_blocks_legacy_fallback_and_overwrite(tmp_path):
    services = SimulatorServices(tmp_path)
    pet = Pet()
    assert services.start(pet) and services.enable_collection(pet, confirmed=True)
    for path in services.collection_repository.root.glob("generation-*.json"):
        path.write_text(json.dumps({"version": 99}))
    fresh = SimulatorServices(tmp_path)
    restored = Pet()
    before = copy.deepcopy(restored.to_dict())
    assert not fresh.start(restored)
    assert fresh.storage_blocked
    assert restored.to_dict() == before
    assert not fresh.save(restored)


def test_collection_saves_preserve_live_clocks_and_manual_calendar(tmp_path):
    services = SimulatorServices(tmp_path)
    pet = Pet()
    assert services.start(pet) and services.enable_collection(pet, confirmed=True)
    original_birth, original_decay = pet.born_at, pet.last_decay
    services._clock_offset = 120000.25
    assert services.save(pet)
    assert (pet.born_at, pet.last_decay) == (original_birth, original_decay)
    fresh = SimulatorServices(tmp_path)
    assert fresh.start(Pet())
    assert fresh._clock_offset == services._clock_offset


def test_breeding_commit_failure_and_powered_incubation(tmp_path, monkeypatch):
    from core.collection import Collection, INCUBATION_MS
    from core.profile import PetProfile
    a, b = Pet(species="rookie", state="live"), Pet(species="rookie", state="live")
    for n, pet in ((2, a), (3, b)):
        pet.profile = PetProfile.from_words((n, 1, 2, 3))
        pet.stats = {"h": 90, "e": 90, "p": 90, "hp": 100}
        pet.roll_dna(n)
    services = SimulatorServices(tmp_path)
    services.collection = Collection.from_pet(a, b)
    assert services.save(a)
    before = services.collection.encode()
    with monkeypatch.context() as m:
        m.setattr("scripts.collection_store.os.replace", lambda *_: (_ for _ in ()).throw(OSError("full")))
        assert not services.breed_individuals(a, 0, 1, confirmed=True)
    assert services.collection.encode() == before
    assert services.breed_individuals(a, 0, 1, confirmed=True)
    assert services.switch_individual(a, 2, confirmed=True)
    assert services.is_incubating(a)
    identity, genes = a.profile.encode(), list(a.dna)
    assert services.advance_collection(a, INCUBATION_MS)
    assert a.species == "baby" and not services.is_incubating(a)
    restored = Pet()
    fresh = SimulatorServices(tmp_path)
    assert fresh.start(restored)
    assert restored.profile.encode() == identity and restored.dna == genes


def test_founder_activation_starts_ordinary_hatch_not_breeding_timer(tmp_path):
    services = SimulatorServices(tmp_path)
    pet = Pet()
    assert services.start(pet) and services.enable_collection(pet, confirmed=True)
    assert services.add_founder(pet, confirmed=True)
    assert services.switch_individual(pet, 1, confirmed=True)
    assert pet.is_hatching and not services.is_incubating(pet)


def test_switch_on_incubation_boundary_does_not_restore_the_unhatched_egg(tmp_path):
    from core.collection import Collection, INCUBATION_MS
    from core.profile import PetProfile
    services = SimulatorServices(tmp_path)
    parents = []
    for n in (2, 3):
        p = Pet(species="rookie", state="live")
        p.profile = PetProfile.from_words((n, 1, 2, 3))
        p.stats = {"hp": 100, "h": 90, "e": 90, "p": 90}
        parents.append(p)
    pet = parents[0]
    services.collection = Collection.from_pet(*parents)
    assert services.save(pet)
    assert services.breed_individuals(pet, 0, 1, confirmed=True)
    assert services.switch_individual(pet, 2, confirmed=True)
    services._collection_elapsed_ms = INCUBATION_MS
    assert services.switch_individual(pet, 0, confirmed=True)
    assert services.collection.pet_at(2).species == "baby"
    assert services.collection.slots[2]["incubation_ms"] == 0


def test_founder_hatch_is_durable_and_rollback_preserves_zero_genes(tmp_path, monkeypatch):
    services = SimulatorServices(tmp_path)
    pet = Pet()
    assert services.start(pet) and services.enable_collection(pet, confirmed=True)
    pet.restore_dna([0, 0, 0, 0])
    pet.start_hatch()
    assert services.save(pet)
    before = copy.deepcopy(pet.to_dict())
    hatch_started = pet.hatch_started_at
    with monkeypatch.context() as m:
        m.setattr("scripts.collection_store.os.replace", lambda *_: (_ for _ in ()).throw(OSError("full")))
        assert not services.complete_hatch(pet)
    assert pet.to_dict() == before and pet.hatch_started_at == hatch_started
    assert services.complete_hatch(pet)
    fresh, restored = SimulatorServices(tmp_path), Pet()
    assert fresh.start(restored)
    assert restored.species == "baby" and restored.dna == [0, 0, 0, 0]


def test_uncertain_commit_blocks_retry_until_reload_without_a_duplicate_egg(tmp_path, monkeypatch):
    import os
    import stat
    services = SimulatorServices(tmp_path)
    pet = Pet()
    assert services.start(pet) and services.enable_collection(pet, confirmed=True)
    fsync = os.fsync

    def fail_directory_sync(fd):
        if stat.S_ISDIR(os.fstat(fd).st_mode):
            raise OSError("directory sync uncertain")
        return fsync(fd)

    with monkeypatch.context() as m:
        m.setattr("scripts.collection_store.os.fsync", fail_directory_sync)
        assert not services.add_founder(pet, confirmed=True)
    assert services.storage_blocked
    assert len(services.collection.slots) == 1
    assert not services.add_founder(pet, confirmed=True)
    fresh, restored = SimulatorServices(tmp_path), Pet()
    assert fresh.start(restored)
    assert len(fresh.collection.slots) == 2
    assert restored.inventory == pet.inventory
