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
