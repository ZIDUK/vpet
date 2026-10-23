import copy
import pytest
from core.pet import Pet


def live():
    return Pet(species='rookie', state='live')


def test_starter_stock_migrates_once_and_saved_empty_stays_empty():
    p = live()
    assert p.adopted_inventory['small_recovery'] == 2
    data = p.to_dict()
    p.adopted_inventory['small_recovery'] = 0
    q = live()
    q.load_from_dict(p.to_dict())
    assert q.adopted_inventory['small_recovery'] == 0
    assert 'adopted_items' in data
    del data['adopted_items']
    q.load_from_dict(data)
    assert q.adopted_inventory['small_recovery'] == 2
    q.adopted_inventory['small_recovery'] = 0
    q.reset_to_egg()
    assert q.adopted_inventory['small_recovery'] == 0


def test_invalid_or_future_stock_does_not_give_free_starters():
    p = live()
    data = p.to_dict()
    data['adopted_items'] = {'version': 99}
    p.load_from_dict(data)
    assert not any(p.adopted_inventory.values())
    data['adopted_items'] = {'version': 1, 'counts': {
        'small_recovery': 10000, 'training_manual': 100, 'off_disk': -1,
        'medium_mp': 'bad', 'evolution_stone': 3}, 'reward_cursor': -3}
    p.load_from_dict(data)
    assert p.adopted_inventory['small_recovery'] == 99
    assert p.adopted_inventory['training_manual'] == 1
    assert p.adopted_inventory['off_disk'] == 0
    assert 'evolution_stone' not in p.adopted_inventory
    assert p.item_reward_cursor == 0


def test_home_bag_lists_adopted_items_and_blocks_combat_consumption():
    from core.inventory import visible_inventory_indexes, use_inventory_item
    from core.adopted_items import menu_index
    p = live()
    index = menu_index('small_recovery')
    assert index in visible_inventory_indexes(p)
    assert use_inventory_item(p, index) == 'blocked'
    p.adopted_inventory['blue_apple'] = 1
    p.stats['p'] = 10
    assert use_inventory_item(p, menu_index('blue_apple')) == 'used'
    assert p.stats['p'] == 30 and p.adopted_inventory['blue_apple'] == 0


@pytest.mark.parametrize('species', ['baby', 'rookie', 'champion', 'ultimate'])
def test_all_starter_bag_items_respect_their_context_and_need(species):
    from core.inventory import use_inventory_item
    from core.adopted_items import menu_index
    p = Pet(species=species, state='live')
    p.stats['p'] = 100
    before = dict(p.adopted_inventory)
    for item_id in ('small_recovery', 'mp_floppy', 'off_disk', 'bandage', 'blue_apple'):
        assert use_inventory_item(p, menu_index(item_id)) == 'blocked'
    assert p.adopted_inventory == before
    p.stats['p'] = 10
    p.injured = True
    p.sleep.asleep = True
    for item_id in ('bandage', 'blue_apple'):
        assert use_inventory_item(p, menu_index(item_id)) == 'blocked'
    assert p.adopted_inventory == before
    p.sleep.asleep = False
    assert use_inventory_item(p, menu_index('bandage')) == 'used'
    assert not p.injured and p.adopted_inventory['bandage'] == 0
    assert use_inventory_item(p, menu_index('blue_apple')) == 'used'
    assert p.stats['p'] == 30 and p.adopted_inventory['blue_apple'] == 0


def test_cold_blocks_care_combat_and_manual_without_spending():
    from core.inventory import use_inventory_item
    from core.adopted_items import menu_index
    from scripts.practice_session import PracticeSession
    p = live()
    p.cold = True
    p.adopted_inventory['training_manual'] = 1
    p.stats['p'] = 10
    before = dict(p.adopted_inventory)
    assert use_inventory_item(p, menu_index('blue_apple')) == 'blocked'
    assert use_inventory_item(p, menu_index('training_manual')) == 'blocked'
    s = PracticeSession(p, lambda _: True)
    s.battle.player.hp = 1
    s.page = 'items'
    s.input('action', 0)
    assert s.battle.player.hp == 1 and p.adopted_inventory == before


def test_failed_victory_save_keeps_session_active_for_retry():
    from scripts.practice_session import PracticeSession
    p = live()
    s = PracticeSession(p, lambda _: False)
    s.battle.result = 'VICTORIA'
    assert not s._award_result()
    assert s.busy
    s.save = lambda _: True
    s.input('action', 10000)
    assert not s.busy


def test_victory_reward_is_single_and_save_failure_rolls_back():
    from scripts.practice_session import PracticeSession
    p = live()
    saved = [False]
    s = PracticeSession(p, lambda _: saved[0])
    before = copy.deepcopy(p.to_dict())
    s.battle.rival.hp = 1
    s._round(-1, 1000)
    assert s.battle.result == 'VICTORIA'
    assert not s.awarded and p.to_dict() == before
    saved[0] = True
    s.input('action', 1100)
    assert s.awarded
    assert p.adopted_inventory['small_recovery'] == 3
    after = copy.deepcopy(p.to_dict())
    s.tick(9000)
    assert p.to_dict() == after


def test_arena_bag_uses_and_saves_once_and_keeps_auto_combat_running():
    from scripts.practice_session import PracticeSession
    p = live()
    s = PracticeSession(p, lambda _: True)
    s.battle.player.hp = 1
    s.index = s.choices().index('MOCHILA')
    s.input('action', 0)
    assert s.page == 'items'
    assert s.input('action', 0)
    assert p.adopted_inventory['small_recovery'] == 1
    assert s.battle.player.hp > 1
    s.tick(0)
    s.tick(500)
    assert s.battle.round == 1


def test_arena_consumption_save_failure_restores_stock_and_fighter():
    from scripts.practice_session import PracticeSession
    p = live()
    s = PracticeSession(p, lambda _: False)
    s.battle.player.hp = 1
    s.page = 'items'
    before = copy.deepcopy(p.to_dict())
    s.input('action', 0)
    assert s.battle.player.hp == 1 and p.to_dict() == before


def test_manual_is_consumed_by_successful_training_not_by_opening_bag():
    from core.training import batch_commit, BatchSaveError
    p = live()
    p.adopted_inventory['training_manual'] = 1
    before = p.ev_at('off')
    with pytest.raises(BatchSaveError):
        batch_commit(p, 'off', 1, lambda _: False)
    assert p.ev_at('off') == before and p.adopted_inventory['training_manual'] == 1
    result = batch_commit(p, 'off', 1, lambda _: True)
    assert result['guide_ev'] == 1 and p.adopted_inventory['training_manual'] == 0
    assert p.ev_at('off') > before


def test_manual_does_not_stack_with_old_guide_or_get_consumed_at_cap():
    from core.training import batch_commit
    p = live()
    p.exploration.guide = True
    p.adopted_inventory['training_manual'] = 1
    result = batch_commit(p, 'off', 1, lambda _: True)
    assert result['guide_ev'] == 1 and not p.exploration.guide
    assert p.adopted_inventory['training_manual'] == 1
    p.ev['off'] = 251
    result = batch_commit(p, 'off', 1, lambda _: True)
    assert result['guide_ev'] == 0 and p.adopted_inventory['training_manual'] == 1


def test_reward_skips_full_stacks_and_rotates_across_reload(tmp_path):
    from core.adopted_items import award_victory_item, ITEMS
    from scripts.sim_services import SimulatorServices
    p = live()
    p.adopted_inventory['small_recovery'] = 99
    assert award_victory_item(p) == 'medium_recovery'
    services = SimulatorServices(tmp_path)
    assert services.save(p)
    q = live()
    assert services.load(q)
    assert q.item_reward_cursor == p.item_reward_cursor
    assert q.adopted_inventory == p.adopted_inventory
    assert award_victory_item(q) == 'large_recovery'
    for item in ITEMS:
        if not item['unlimited']:
            q.adopted_inventory[item['id']] = item['stack_max']
    assert award_victory_item(q) is None


@pytest.mark.parametrize('result', ['DERROTA', 'EMPATE'])
def test_non_victory_does_not_award_items(result):
    from scripts.practice_session import PracticeSession
    p = live()
    before = dict(p.adopted_inventory)
    s = PracticeSession(p, lambda _: True)
    s.battle.result = result
    assert s._award_result()
    assert p.adopted_inventory == before and p.item_reward_cursor == 0


def test_terminal_auto_round_closes_bag_and_prevents_posthumous_consumption():
    from scripts.practice_session import PracticeSession
    p = live()
    s = PracticeSession(p, lambda _: True)
    s.page = 'items'
    s.battle.player.hp = 1
    s.battle.player.equipped = (2,)
    s.tick(0)
    s.tick(500)
    assert s.battle.result == 'DERROTA' and s.page == 'battle'
    assert p.adopted_inventory['small_recovery'] == 2


def test_cpp_starter_caps_menu_indices_and_reward_rotation_match(tmp_path):
    import json
    import subprocess
    from pathlib import Path
    from core.adopted_items import ITEMS, menu_index, award_victory_item
    root = Path(__file__).resolve().parents[1]
    binary = tmp_path / 'items-trace'
    subprocess.run(['c++', '-std=c++11', '-I', str(root / 'firmware/t-display/lib/vpet_core/src'),
                    str(root / 'firmware/t-display/test/traces/consumables.cpp'), '-o', str(binary)], check=True)
    records = [json.loads(line) for line in subprocess.check_output([str(binary)], text=True).splitlines()]
    p = live()
    for i, item in enumerate(ITEMS):
        assert records[i] == {'item': item['id'], 'menu_index': menu_index(item['id']),
                              'stock': p.adopted_inventory.get(item['id'], 0), 'limit': item['stack_max']}
    for n, record in enumerate(records[len(ITEMS):]):
        key = award_victory_item(p)
        assert record == {'victory': n + 1, 'reward': key or '', 'cursor': p.item_reward_cursor,
                          'rewards': n + 1, 'stock': p.adopted_inventory.get(key, 0)}
