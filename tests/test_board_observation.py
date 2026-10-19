from scripts.observe_tdisplay import summarize


def test_observation_does_not_invent_measurements_from_silence():
    value=summarize(['VPET_INPUT event=1'])
    assert value['runtime_samples']==0 and not value['liveness_observed']
    assert value['heap_free_min'] is None and value['input_events']==1


def test_observation_records_heap_loop_time_and_ble_without_calling_it_fps():
    lines=['VPET_RUNTIME uptime_ms=10000 heap_free=65000 heap_min=63000 loop_max_us=42000 ble=1',
           'VPET_BLE status=CONNECTED name=vPet-F908',
           'VPET_RUNTIME uptime_ms=20000 heap_free=64900 heap_min=62900 loop_max_us=55000 ble=2']
    value=summarize(lines)
    assert value['runtime_samples']==2 and value['liveness_observed']
    assert value['heap_free_min']==64900 and value['heap_minimum_watermark']==62900
    assert value['loop_max_us']==55000 and value['ble_states']==[1,2]
    assert value['restarts_observed']==0 and 'fps' not in value


def test_observation_detects_restarts_and_fatals():
    value=summarize(['VPET_RUNTIME uptime_ms=90000 heap_free=60000 heap_min=59000 loop_max_us=2 ble=2',
                     'VPET_RUNTIME uptime_ms=10000 heap_free=60000 heap_min=59000 loop_max_us=2 ble=1',
                     'Guru Meditation Error: panic'])
    assert value['restarts_observed']==1 and value['fatal_lines']
    assert not value['liveness_observed']
