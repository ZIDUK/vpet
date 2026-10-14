"""Simulator clock contract: get_datetime() is a 5-tuple, not a datetime."""

from scripts.sim_services import SimulatorServices, clock_hour, format_clock


def test_get_datetime_is_tuple_and_clock_hour_reads_index_three(tmp_path):
    services = SimulatorServices(tmp_path)
    services.set_time(21, 5)
    clock = services.get_datetime()
    assert clock == (clock[0], clock[1], clock[2], 21, 5)
    assert clock_hour(clock) == 21
    assert clock_hour(None) == 12


def test_format_clock_uses_datetime_tuple():
    assert format_clock((2026, 9, 5, 10, 15)) == "2026/09/05 10:15"
    assert format_clock(None) == "--"


def test_simulator_save_replaces_complete_snapshot_atomically(tmp_path):
    import json

    services = SimulatorServices(tmp_path)
    first = type("PetSnapshot", (), {"to_dict": lambda self: {"h": 20}})()
    second = type("PetSnapshot", (), {"to_dict": lambda self: {"h": 40}})()
    assert services.save(first)
    assert services.save(second)
    assert json.loads(services.save_path.read_text()) == {"h": 40}
    assert list(services.save_path.parent.glob("*.tmp")) == []


def test_simulator_save_failure_keeps_previous_snapshot(tmp_path, monkeypatch):
    import json
    import scripts.sim_services as sim_services

    services = SimulatorServices(tmp_path)
    first = type("PetSnapshot", (), {"to_dict": lambda self: {"h": 20}})()
    second = type("PetSnapshot", (), {"to_dict": lambda self: {"h": 40}})()
    assert services.save(first)

    def fail_replace(*_args):
        raise OSError("simulated power-loss boundary")

    monkeypatch.setattr(sim_services.os, "replace", fail_replace)
    assert not services.save(second)
    assert json.loads(services.save_path.read_text()) == {"h": 20}
    assert not list(services.save_path.parent.glob("*.tmp"))
