import copy
import json

import pytest

from core.pet import Pet
from core.profile import PetProfile


def adult(n=2):
    pet = Pet(species="rookie", state="live")
    pet.profile = PetProfile.from_words((n, 1, 2, 3))
    pet.restore_dna([0x12, 0x34, 0x56, 0x78])
    pet.stats = {"h": 90, "e": 90, "p": 90, "hp": 100}
    return pet


def test_migration_preserves_identity_and_uses_active_stock_only():
    from core.collection import Collection
    a, b = adult(), adult(3)
    a.inventory["energy"] = 1
    b.inventory["energy"] = 9
    before = copy.deepcopy(b.to_dict())
    collection = Collection.from_pet(a, b)
    assert len(collection.slots) == 2
    assert collection.current().profile == a.profile
    assert collection.shared["inventory"]["energy"] == 1
    assert b.to_dict() == before
    assert collection.slots[1]["pet"]["profile"] == b.profile.encode()


def test_switch_does_not_refill_stock_or_rejuvenate_inactive_pet():
    from core.collection import Collection
    a, b = adult(), adult(3)
    collection = Collection.from_pet(a, b)
    a.inventory["energy"] = 0
    a.ev["spd"] = 42
    target = collection.switch(a, 1, confirmed=True)
    assert target.inventory["energy"] == 0
    assert target.profile == b.profile
    target.inventory["energy"] = 2
    restored = collection.switch(target, 0, confirmed=True)
    assert restored.inventory["energy"] == 2 and restored.ev["spd"] == 42


def test_founder_requires_confirmation_and_never_grants_stock():
    from core.collection import Collection
    a = adult()
    collection = Collection.from_pet(a)
    before = collection.encode()
    with pytest.raises(ValueError):
        collection.founder((3, 4, 5, 6), 123, confirmed=False, sequence=1)
    assert collection.encode() == before
    slot = collection.founder((3, 4, 5, 6), 123, confirmed=True, sequence=1)
    assert slot == 1 and len(collection.slots) == 2
    assert collection.current().inventory == a.inventory
    assert collection.slots[slot]["pet"]["species"] == "egg"
    assert collection.slots[slot]["pet"]["profile"] != a.profile.encode()
    assert collection.founder((9, 9, 9, 9), 789, confirmed=True, sequence=1) == slot
    assert len(collection.slots) == 2


def test_capacity_and_sequence_rejection_leave_collection_unchanged():
    from core.collection import Collection
    collection = Collection.from_pet(adult())
    for i in range(1, 4):
        collection.founder((i + 2, 4, 5, 6), i, confirmed=True, sequence=i)
    before = collection.encode()
    with pytest.raises(ValueError):
        collection.founder((8, 4, 5, 6), 42, confirmed=True, sequence=4)
    assert collection.encode() == before
    assert len(collection.slots) == 4


def test_egg_sex_is_hidden_in_collection_views(tmp_path):
    from core.collection import Collection
    from scripts.collection_session import CollectionSession
    from scripts.sim_services import SimulatorServices

    pet = adult()
    collection = Collection.from_pet(pet)
    collection.founder((3, 4, 5, 6), 123, confirmed=True, sequence=1)

    services = SimulatorServices(tmp_path)
    services.collection = collection
    session = CollectionSession(pet, services)
    assert session.choices()[1].endswith(" ?")


def test_invalid_duplicate_identity_or_future_data_is_not_migrated():
    from core.collection import Collection
    a = adult()
    assert len(Collection.from_pet(a, copy.deepcopy(a)).slots) == 1
    b = copy.deepcopy(a)
    b.ev["spd"] = 1
    with pytest.raises(ValueError):
        Collection.from_pet(a, b)
    collection = Collection.from_pet(a)
    data = json.loads(collection.encode())
    data["version"] = 99
    with pytest.raises(ValueError):
        Collection.decode(json.dumps(data))


def test_switch_is_blocked_during_sleep_trip_pause_or_session():
    from core.collection import Collection
    a, b = adult(), adult(3)
    collection = Collection.from_pet(a, b)
    before = collection.encode()
    for flag in ("cold", "busy"):
        a.cold = flag == "cold"
        with pytest.raises(ValueError):
            collection.switch(a, 1, confirmed=True, busy=flag == "busy")
        assert collection.encode() == before


def test_repository_rejected_commit_keeps_previous_generation(tmp_path, monkeypatch):
    from core.collection import Collection
    from scripts.collection_store import CollectionRepository
    repo = CollectionRepository(tmp_path / "collection")
    collection = Collection.from_pet(adult())
    assert repo.commit(collection)
    before = repo.load().encode()
    collection.founder((3, 4, 5, 6), 123, confirmed=True, sequence=1)
    monkeypatch.setattr("scripts.collection_store.os.replace", lambda *_: (_ for _ in ()).throw(OSError("full")))
    assert not repo.commit(collection)
    assert repo.load().encode() == before


def test_repository_does_not_accept_corruption_as_missing(tmp_path):
    from core.collection import Collection
    from scripts.collection_store import CollectionRepository
    repo = CollectionRepository(tmp_path / "collection")
    assert repo.commit(Collection.from_pet(adult()))
    for path in repo.root.glob("generation-*.json"):
        path.write_text('{"version":99}')
    with pytest.raises(ValueError):
        repo.load()


def test_breeding_records_parents_genes_cooldown_and_one_egg():
    from core.collection import Collection, INCUBATION_MS
    a, b = adult(), adult(3)
    b.restore_dna([0xEF, 0xCD, 0xAB, 0x89])
    collection = Collection.from_pet(a, b)
    child = collection.breed(0, 1, (8, 9, 10, 11), 1234, confirmed=True, sequence=1)
    assert child == 2
    profile = PetProfile.decode(collection.slots[child]["pet"]["profile"])
    assert (profile.parent_a, profile.parent_b) == (a.profile.pet_id, b.profile.pet_id)
    assert collection.slots[child]["incubation_ms"] == INCUBATION_MS
    assert collection.slots[0]["cooldown_until"] == 86400000
    assert collection.breed(0, 1, (19, 19, 19, 19), 44, confirmed=True, sequence=1) == child
    assert len(collection.slots) == 3
    before = collection.encode()
    with pytest.raises(ValueError):
        collection.breed(0, 1, (18, 19, 20, 21), 44, confirmed=True, sequence=2)
    assert collection.encode() == before


def test_breeding_incubation_only_advances_active_egg_and_preserves_identity():
    from core.collection import Collection, INCUBATION_MS
    collection = Collection.from_pet(adult(), adult(3))
    index = collection.breed(0, 1, (8, 9, 10, 11), 1234, confirmed=True, sequence=1)
    collection.advance_ms(INCUBATION_MS)
    assert collection.slots[index]["incubation_ms"] == INCUBATION_MS
    collection.switch(collection.current(), index, confirmed=True)
    profile, dna = collection.current().profile, list(collection.current().dna)
    collection.advance_ms(INCUBATION_MS - 1)
    assert collection.current().is_egg
    restored = Collection.decode(collection.encode())
    restored.advance_ms(1)
    assert restored.current().species == "baby"
    assert restored.current().profile == profile and restored.current().dna == dna
    assert all(value == 0 for value in restored.current().ev.values())


def test_bred_egg_keeps_hidden_inherited_sex_through_hatch():
    from core.collection import Collection, INCUBATION_MS
    a, b = adult(), adult(3)
    collection = Collection.from_pet(a, b)
    index = collection.breed(0, 1, (8, 9, 10, 11), 1234, confirmed=True, sequence=1)
    inherited = collection.pet_at(index)
    assert inherited.profile.sex in ("M", "F")
    assert inherited.dna[4] == (1 if inherited.profile.sex == "M" else 2)
    assert collection.slots[index]["pet"]["profile"].split(":")[2] == inherited.profile.sex
    collection.switch(collection.current(), index, confirmed=True)
    assert collection.current().is_egg and collection.current().profile.sex == inherited.profile.sex
    collection.advance_ms(INCUBATION_MS)
    assert collection.current().species == "baby"
    assert collection.current().profile.sex == inherited.profile.sex
    assert collection.current().dna[4] == inherited.dna[4]


def test_breeding_rejects_related_parents_without_mutation():
    from core.collection import Collection
    a, b = adult(), adult(3)
    ancestor = adult(6).profile.pet_id
    other = adult(7).profile.pet_id
    a.profile = PetProfile(a.profile.pet_id, "M", ancestor, other)
    b.profile = PetProfile(b.profile.pet_id, "F", ancestor, other)
    collection = Collection.from_pet(a, b)
    before = collection.encode()
    with pytest.raises(ValueError):
        collection.breed(0, 1, (8, 9, 10, 11), 1234, confirmed=True, sequence=1)
    assert collection.encode() == before


@pytest.mark.parametrize("change", [
    lambda d: d["shared"]["adopted_items"].update(version=99),
    lambda d: d["shared"]["inventory"].update(energy=255),
    lambda d: d["slots"][0]["pet"]["ev"].update(unknown=1),
    lambda d: d["slots"][0]["pet"].update(extra="future"),
    lambda d: d["slots"][0]["pet"].update(state="invalid"),
    lambda d: d["slots"][0].update(incubation_ms=1),
])
def test_strict_collection_does_not_silently_normalize_corrupt_progress(change):
    from core.collection import Collection
    collection = Collection.from_pet(adult())
    data = json.loads(collection.encode())
    change(data)
    with pytest.raises(ValueError):
        Collection.decode(json.dumps(data))


def test_zero_gene_child_is_not_mistaken_for_legacy_missing_dna():
    from core.collection import Collection, INCUBATION_MS
    from core.breeding import offspring_dna
    a, b = adult(), adult(3)
    for p in (a, b):
        p.restore_dna([0, 0, 0, 0])
    seed = next(i for i in range(100) if offspring_dna(a.dna[:4], b.dna[:4], i) == bytes(4))
    collection = Collection.from_pet(a, b)
    child = collection.breed(0, 1, (8, 9, 10, 11), seed, confirmed=True, sequence=1)
    collection.switch(collection.current(), child, confirmed=True)
    collection.advance_ms(INCUBATION_MS)
    restored = Collection.decode(collection.encode())
    assert restored.current().species == "baby"
    assert restored.current().dna == [0, 0, 0, 0, 1]


def test_repository_never_silently_rolls_back_a_committed_corrupt_generation(tmp_path):
    from core.collection import Collection
    from scripts.collection_store import CollectionRepository
    repo = CollectionRepository(tmp_path / "collection")
    collection = Collection.from_pet(adult())
    assert repo.commit(collection)
    collection.founder((3, 4, 5, 6), 123, confirmed=True, sequence=1)
    assert repo.commit(collection)
    (repo.root / "generation-0.json").write_text("damaged")
    with pytest.raises(ValueError):
        repo.load()


def test_repository_rejects_stale_writer_instead_of_overwriting_newer_collection(tmp_path):
    from core.collection import Collection
    from scripts.collection_store import CollectionRepository
    repo = CollectionRepository(tmp_path / "collection")
    assert repo.commit(Collection.from_pet(adult()))
    old, current = repo.load(), repo.load()
    current.founder((3, 4, 5, 6), 123, confirmed=True, sequence=1)
    assert repo.commit(current)
    assert not repo.commit(old)
    assert len(repo.load().slots) == 2


def test_four_individuals_with_full_learning_histories_fit_the_collection_budget(tmp_path):
    from core.collection import Collection, MAX_BYTES
    from core.learning import LearningState
    from scripts.collection_store import CollectionRepository
    collection = Collection.from_pet(adult())
    policy = LearningState()
    for sequence in range(1, 257):
        assert policy.record(sequence, 1, 0, sequence % 5, (sequence % 201) - 100)
    for n in range(1, 4):
        collection.founder((n + 2, 4, 5, 6), n, confirmed=True, sequence=n)
    for slot in collection.slots:
        slot["pet"]["learning"] = policy.encode()
    assert len(collection.encode().encode()) < MAX_BYTES
    repo = CollectionRepository(tmp_path / "collection")
    assert repo.commit(collection)
    restored = repo.load()
    assert all(restored.pet_at(i).learning.encode() == policy.encode() for i in range(4))


def test_deeply_nested_generation_is_rejected_without_escaping_validation(tmp_path):
    from scripts.collection_store import CollectionRepository
    repo = CollectionRepository(tmp_path / "collection")
    repo.root.mkdir()
    (repo.root / "generation-1.json").write_text("[" * 2000 + "0" + "]" * 2000)
    with pytest.raises(ValueError):
        repo.load()


def test_repository_rejects_an_overlapping_writer_without_touching_generations(tmp_path):
    import fcntl
    from core.collection import Collection
    from scripts.collection_store import CollectionRepository
    repo = CollectionRepository(tmp_path / "collection")
    collection = Collection.from_pet(adult())
    assert repo.commit(collection)
    before = repo.load().encode()
    with (repo.root / ".writer.lock").open("a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert not repo.commit(collection)
    assert repo.load().encode() == before
    assert repo.commit(collection)
