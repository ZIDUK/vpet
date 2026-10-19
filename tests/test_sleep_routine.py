import pytest

from core.sleep import SleepRoutine, is_night


def civil(day, hour, minute=0):
    return (20000 + day) * 86400 + hour * 3600 + minute * 60


@pytest.mark.parametrize('hour,minute,night', [(17,59,False),(18,0,True),(23,59,True),
                                             (0,0,True),(5,59,True),(6,0,False)])
def test_exact_environment_boundaries(hour, minute, night):
    assert is_night(hour * 60 + minute) == night


def test_learns_consistent_routine_gradually_once_per_night():
    routine = SleepRoutine()
    before = routine.preferred(1)
    for day in range(2):
        assert routine.start(civil(day,22),1)
        routine.advance(routine.required, 0)
        assert routine.preferred(1) == before
    assert routine.start(civil(2,22),1)
    routine.advance(routine.required, 0)
    assert routine.preferred(1) == before + 15
    routine.stop()
    routine.start(civil(2,22,20),1)
    routine.advance(routine.required, 0)
    assert routine.preferred(1) == before + 15
    routine.stop()
    routine.start(civil(3,19),1)
    routine.advance(routine.required, 0)
    assert routine.preferred(1) == before + 15


def test_dawn_and_sleep_duration_are_independent_and_serializable():
    routine = SleepRoutine()
    assert routine.start(civil(0,23),0)
    assert routine.required == 8 * 3600
    energy, complete, reward = routine.advance(7*3600,0)
    assert routine.asleep and not complete and energy == 84 and not reward
    restored = SleepRoutine(routine.to_dict())
    energy, complete, reward = restored.advance(3600,energy)
    assert not restored.asleep and complete and reward and energy == 96
    assert restored.advance(3600,energy) == (energy, False, False)
    early = SleepRoutine()
    early.start(civil(0,18),1)
    assert early.required == 12 * 3600


def test_naps_and_interruption_do_not_reward_or_train():
    routine = SleepRoutine()
    routine.start(civil(0,12),2)
    assert routine.required == 1800 and routine.samples == 0
    assert routine.advance(1800,20) == (26,True,False)
    routine.start(civil(0,22),2)
    routine.advance(600,20)
    routine.stop()
    assert routine.advance(86400,20) == (20,False,False)
    routine.start(0,2)
    assert routine.required == 1800
    assert routine.advance(1800,99) == (100,True,False)
    assert routine.samples == 0 and routine.reward_night == -1


def test_tired_hysteresis_and_bedtime_not_removed_by_protein():
    routine = SleepRoutine()
    assert routine.tired(20,0,12*60)
    assert routine.tired(25,0,12*60)
    assert not routine.tired(30,0,12*60)
    assert routine.tired(100,0,23*60)
    routine.start(civil(0,23),0)
    assert not routine.tired(0,0,23*60)


def test_rewind_clock_does_not_repeat_learning_or_rewards():
    routine = SleepRoutine()
    for index, day in enumerate((2, 1, 2)):
        routine.start(civil(day,22),1)
        _, _, reward = routine.advance(43200,0)
        assert reward == (index == 0)
        assert routine.samples == 1 and routine.learned_night == 20002


@pytest.mark.parametrize('record', ['2,0', '1,0', 'future', '1,'+','.join(['-1']*13)])
def test_rejects_invalid_sleep_record(record):
    with pytest.raises(ValueError):
        SleepRoutine.decode(record)


def test_sleep_saved_restored_and_survives_evolution(tmp_path):
    from core.pet import Pet
    from scripts.sim_services import SimulatorServices
    pet = Pet(species='rookie', state='live')
    services = SimulatorServices(tmp_path)
    services.exploration_time = lambda: civil(0,23)
    pet.stats['e'] = 0
    assert services.toggle_sleep(pet)
    assert not services.advance_sleep(pet, 7*3600000)
    assert pet.sleep.asleep and pet.stats['e'] == 84
    restored = Pet()
    assert services.load(restored)
    assert restored.sleep.encode() == pet.sleep.encode()
    before = restored.to_dict()
    services.save = lambda pet: False
    assert not services.advance_sleep(restored,3600000)
    assert restored.to_dict()['sleep'] == before['sleep']
    assert restored.stats == before['stats']
    services.save = SimulatorServices(tmp_path).save
    assert services.advance_sleep(restored,3600000)
    assert not restored.sleep.asleep and restored.stats['e'] == 96
    routine = restored.sleep.encode()
    restored.species = 'champion'
    restored.reset_after_evolution()
    assert restored.sleep.encode() == routine
    restored.reset_to_egg()
    assert restored.sleep.encode() == SleepRoutine().encode()


def test_legacy_json_and_rejected_light_off(tmp_path):
    from core.pet import Pet
    from scripts.sim_services import SimulatorServices
    pet = Pet(species='rookie', state='live')
    old = pet.to_dict()
    del old['sleep']
    pet.load_from_dict(old)
    assert not pet.sleep.asleep and pet.sleep.bedtime == 0
    services = SimulatorServices(tmp_path)
    services.save = lambda pet: False
    assert not services.toggle_sleep(pet)
    assert not pet.sleep.asleep
    pet.call_reason = 'lights'
    pet.update_call(99999999,1,23,lights_enabled=False)
    assert not pet.call_reason and pet.care_mistakes == 0


def test_sleeping_pet_cannot_start_trip_eat_or_consume_items():
    from core.pet import Pet
    from core.inventory import use_inventory_item
    from core.options import OptionsSession, OPTION_EVOLVE
    pet = Pet(species='rookie',state='live')
    pet.sleep.start(civil(0,23),1)
    before = pet.to_dict()
    assert not pet.exploration.start(pet,'patio',None,civil(0,23))
    assert not pet.use_food('meat')['applied']
    assert use_inventory_item(pet,1) == 'blocked'
    session = OptionsSession(); session.index = OPTION_EVOLVE
    session.action(pet,None)
    assert pet.species == 'rookie' and session.message == 'NO EVO'
    assert pet.to_dict()['stats'] == before['stats']
