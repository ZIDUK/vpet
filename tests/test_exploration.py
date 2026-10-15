"""Real-clock boundaries, migration, caps and atomic expedition transactions."""
import pytest
from core.exploration import DURATIONS, Exploration, week_id
from core.pet import Pet
from core.training import batch_commit, batch_block_reason, BatchSaveError
from core.inventory import INVENTORY_GUIDE_INDEX, INVENTORY_BACK_INDEX, visible_inventory_indexes, use_inventory_item
from scripts.exploration_session import ExplorationSession
from scripts.sim_services import SimulatorServices

NOW = 1791979200


def pet():
    p = Pet(species="rookie", state="live")
    p.stats.update(h=70, e=70, p=70)
    return p


@pytest.mark.parametrize("species", ["egg", "baby"])
def test_young_pets_cannot_depart(species):
    p = Pet(species=species, state="live")
    assert not p.exploration.start(p, "patio", None, NOW)


def test_departure_is_free_and_freezes_care_quality():
    p = pet()
    p.stats["e"] = 0
    assert p.exploration.start(p, "patio", None, NOW)
    assert p.stats["e"] == 0
    assert not p.exploration.start(p, "noche", None, NOW)
    p.stats["e"] = 70
    assert p.exploration.preview(p, NOW + 1800)["energy"] == 10


@pytest.mark.parametrize("elapsed,expected", [(0, 0), (1799, 24), (1800, 25), (999999, 25)])
def test_patio_returns_only_proportional_energy(elapsed, expected):
    p = pet()
    p.exploration.start(p, "patio", None, NOW)
    reward = p.exploration.claim(p, NOW + elapsed)
    assert reward["energy"] == expected
    assert not any(p.ev.values())
    assert p.inventory == pet().inventory
    assert p.exploration.claim(p, NOW + elapsed + 10000) is None


@pytest.mark.parametrize("stat", ["hp", "mp", "off", "def", "spd", "brn"])
@pytest.mark.parametrize("elapsed,expected", [(14399, 0), (14400, 1), (28799, 1), (28800, 2)])
def test_jornada_reward_thresholds_all_stats(stat, elapsed, expected):
    p = pet()
    assert p.exploration.start(p, "jornada", stat, NOW)
    reward = p.exploration.claim(p, NOW + elapsed)
    assert reward["ev"] == expected == p.ev_at(stat)
    assert p.exploration.guide == (elapsed == 28800)


def test_jornada_cap_and_one_guide_across_repeated_claims():
    p = pet()
    for i in range(6):
        p.exploration.start(p, "jornada", "off", NOW + i * 28800)
        p.exploration.claim(p, NOW + (i + 1) * 28800)
    assert p.ev_at("off") == 8
    assert p.exploration.guide
    assert not p.exploration.guide_pending


def test_poor_care_does_not_create_a_guide():
    p = pet()
    p.stats["h"] = 49
    p.exploration.start(p, "jornada", "def", NOW)
    reward = p.exploration.claim(p, NOW + 28800)
    assert reward["ev"] == 2
    assert not p.exploration.guide


def test_two_full_nights_unlock_flame_then_mastery_is_capped():
    p = pet()
    p.exploration.start(p, "noche", None, NOW)
    p.exploration.claim(p, NOW + 28799)
    assert p.techniques.training == 0
    for i in range(2):
        p.exploration.start(p, "noche", None, NOW + i * 28800)
        p.exploration.claim(p, NOW + (i + 1) * 28800)
    assert p.techniques.learned(1)
    assert p.techniques.equipped == [0, 2]
    for i in range(3):
        p.exploration.start(p, "noche", None, NOW + (i + 2) * 28800)
        p.exploration.claim(p, NOW + (i + 3) * 28800)
    assert p.techniques.mastery[1] == 4


def test_week_boundary_and_clock_rollback_do_not_reset_spent_allowance():
    monday = 4 * 86400  # 1970-01-05, local Monday midnight.
    assert week_id(monday - 1) + 1 == week_id(monday)
    p = pet()
    e = p.exploration
    e.week, e.week_ev = week_id(NOW), 8
    e.start(p, "jornada", "off", NOW)
    assert e.preview(p, NOW + 28800)["ev"] == 0
    assert e.claim(p, NOW + 604800)["ev"] == 2
    e.start(p, "jornada", "off", NOW + 604800)
    assert e.claim(p, NOW)["ev"] == 0
    assert e.week_ev == 2


def test_save_restore_pending_trip_and_receipt_do_not_replay_reward(tmp_path):
    p = pet()
    services = SimulatorServices(tmp_path)
    p.exploration.start(p, "jornada", "spd", NOW)
    assert services.save(p)
    restored = pet()
    assert services.load(restored)
    assert restored.exploration.remaining(NOW + 20000) == 8800
    restored.exploration.claim(restored, NOW + 28800)
    assert services.save(restored)
    assert services.load(p)
    assert p.exploration.receipt["ev"] == 2
    assert p.exploration.claim(p, NOW + 999999) is None
    assert p.ev_at("spd") == 2
    old = p.to_dict()
    old.pop("exploration")
    p.load_from_dict(old)
    assert not p.exploration.away and not p.exploration.guide


def test_atomic_start_claim_and_acknowledgment_retry():
    p = pet()
    clock = [NOW]
    fail = [True]
    s = ExplorationSession(p, lambda _: not fail[0], lambda: clock[0])
    s.input("action")  # patio -> confirmation
    s.input("action")  # failed start
    assert s.message == "save_failed" and not p.exploration.away
    fail[0] = False
    s.input("action")
    assert p.exploration.away and s.page == "trip"
    clock[0] += 1800
    fail[0] = True
    s.input("action")
    assert p.exploration.away and p.stats["e"] == 70
    fail[0] = False
    s.input("action")
    assert s.page == "receipt" and p.stats["e"] == 95
    fail[0] = True
    s.input("action")
    assert s.page == "receipt" and p.exploration.receipt
    fail[0] = False
    s.input("action")
    assert s.page == "routes" and not p.exploration.receipt
    assert p.stats["e"] == 95


def test_guide_goes_to_training_and_is_atomic_with_completion():
    p = pet()
    p.exploration.guide = True
    assert INVENTORY_BACK_INDEX == 6
    assert visible_inventory_indexes(p)[-2:] == (INVENTORY_GUIDE_INDEX, INVENTORY_BACK_INDEX)
    assert use_inventory_item(p, INVENTORY_GUIDE_INDEX) == "train"
    with pytest.raises(BatchSaveError):
        batch_commit(p, "off", 1, lambda _: False)
    assert p.exploration.guide and p.ev_at("off") == 0
    summary = batch_commit(p, "off", 1, lambda _: True)
    assert summary["ev_added"] == 7 and summary["guide_ev"] == 1
    assert not p.exploration.guide
    assert batch_commit(p, "off", 1, lambda _: True)["ev_added"] == 6


def test_guide_is_kept_when_base_training_fills_the_stat():
    p = pet()
    p.exploration.guide = True
    p.ev["off"] = 251
    assert batch_commit(p, "off", 1, lambda _: True)["ev_added"] == 1
    assert p.exploration.guide


def test_absent_pet_cannot_spend_items_or_train():
    p = pet()
    p.exploration.start(p, "patio", None, NOW)
    assert batch_block_reason(p, "off") == "DE EXPLORACION"
    assert use_inventory_item(p, 1) == "blocked"
    assert not p.techniques.train(p, 1)
    from scripts.practice_session import PracticeSession
    battle = PracticeSession(p, lambda _: True)
    battle._round(0, 500)
    assert battle.battle.round == 0


@pytest.mark.parametrize("data", [None, [], {"version": 99},
    {"version": 1, "trip": {"route": "bad"}},
    {"version": 1, "trip": {"route": "patio"}},
    {"version": 1, "trip": {"route": "patio", "started": -1}}])
def test_invalid_or_legacy_exploration_is_safe(data):
    assert not Exploration(data).away


def test_simulator_expedition_clock_advances(monkeypatch, tmp_path):
    from scripts import sim_services
    now = [1000000.0]
    monkeypatch.setattr(sim_services.time, "time", lambda: now[0])
    services = SimulatorServices(tmp_path)
    first = services.exploration_time()
    now[0] += 1800
    assert services.exploration_time() - first == 1800


def test_saved_clock_adjustment_survives_restart_and_offline_elapsed(monkeypatch, tmp_path):
    from scripts import sim_services
    now = [1791979200.0]
    monkeypatch.setattr(sim_services.time, "time", lambda: now[0])
    services = SimulatorServices(tmp_path)
    services.set_time(21, 0)
    p = pet()
    p.exploration.start(p, "patio", None, services.exploration_time())
    assert services.save(p)
    now[0] += 1800
    reopened = SimulatorServices(tmp_path)
    restored = pet()
    assert reopened.load(restored)
    assert restored.exploration.remaining(reopened.exploration_time()) == 0
    assert restored.exploration.claim(restored, reopened.exploration_time())["energy"] == 25
