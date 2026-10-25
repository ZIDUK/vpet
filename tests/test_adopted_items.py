import subprocess
from pathlib import Path

import pytest


def test_catalog_excludes_unsupported_systems():
    from core.adopted_items import ITEMS
    assert len({i['id'] for i in ITEMS}) == len(ITEMS)
    assert {i['category'] for i in ITEMS} == {
        'feeding', 'combat_recovery', 'condition', 'battle_boost',
        'permanent', 'care', 'training_boost'}
    assert {i['id'] for i in ITEMS if i['unlimited']} == {'meat', 'protein'}
    assert not any(i['category'] in ('evolution', 'key', 'fishing', 'sale') for i in ITEMS)


@pytest.mark.parametrize('percent,expected', [(20, 17), (50, 43), (90, 77), (100, 86)])
def test_recovery_uses_combat_maximum(percent, expected):
    from core.adopted_items import recovered
    assert recovered(0, 86, percent) == expected
    assert recovered(85, 86, percent) == 86
    assert recovered(0, 1, percent) == 1


def test_combat_item_consumes_only_when_effective_and_does_not_revive():
    from core.adopted_items import use_combat_item
    from core.practice import Fighter
    f = Fighter((25, 20, 24, 20, 22, 20))
    stock = {'small_recovery': 2, 'off_disk': 2}
    assert not use_combat_item(f, stock, 'small_recovery')
    f.hp = 1
    assert use_combat_item(f, stock, 'small_recovery')
    assert f.hp == 19 and stock['small_recovery'] == 1
    assert use_combat_item(f, stock, 'off_disk')
    assert f.stats[2] == 28
    assert not use_combat_item(f, stock, 'off_disk')
    assert stock['off_disk'] == 1
    f.hp = 0
    assert not use_combat_item(f, stock, 'small_recovery')
    assert stock['small_recovery'] == 1


def test_cpp_recovery_and_boost_match_python(tmp_path):
    from core.adopted_items import recovered
    root = Path(__file__).resolve().parents[1]
    binary = tmp_path / 'items'
    subprocess.run(['c++', '-std=c++11', '-I', str(root / 'firmware/t-display/lib/vpet_core/src'),
                    str(root / 'tests/adopted_items_trace.cpp'), '-o', str(binary)], check=True)
    values = list(map(int, subprocess.check_output([str(binary)], text=True).split()))
    assert values == [recovered(0, 86, p) for p in (20, 50, 90, 100)] + [1, 28, 0, 1]


def test_export_is_reproducible_and_sprites_unique():
    from scripts.export_adopted_items import export
    from core.adopted_items import ITEMS
    from PIL import Image
    root = Path(__file__).resolve().parents[1]
    export(check=True)
    pixels = []
    for item in ITEMS:
        with Image.open(root / item['sprite']) as image:
            assert image.mode == 'RGBA' and image.size == (32, 32)
            assert image.getpixel((0, 0))[3] == 0
            pixels.append(image.tobytes())
    assert len(set(pixels)) == len(ITEMS)


def test_care_items_respect_caps_and_context():
    from core.adopted_items import use_care_item
    from core.pet import Pet
    p = Pet(species='rookie', state='live')
    stock = {'off_chip': 2, 'bandage': 1, 'prickly_pear': 1}
    p.ev['off'] = p.ev_limit()-2
    assert use_care_item(p, stock, 'off_chip') and p.ev['off'] == p.ev_limit()
    assert not use_care_item(p, stock, 'off_chip') and stock['off_chip'] == 1
    assert not use_care_item(p, stock, 'bandage')
    p.injured = True
    assert use_care_item(p, stock, 'bandage') and not p.injured
    p.weight = 1
    assert not use_care_item(p, stock, 'prickly_pear')


def test_stronger_boost_replaces_weaker_without_compounding():
    from core.adopted_items import use_combat_item
    from core.practice import Fighter
    f = Fighter((25, 20, 50, 20, 22, 20))
    stock = {'off_disk': 2, 'super_off_disk': 1}
    assert use_combat_item(f, stock, 'off_disk') and f.stats[2] == 60
    assert use_combat_item(f, stock, 'super_off_disk') and f.stats[2] == 70
    assert not use_combat_item(f, stock, 'off_disk') and stock['off_disk'] == 1


def test_battle_result_blocks_consumption():
    from core.practice import Fighter, PracticeBattle
    b = PracticeBattle(Fighter((25, 20, 25, 20, 20, 20)))
    b.player.hp = 1
    stock = {'small_recovery': 1}
    b.result = 'DERROTA'
    assert not b.use_item(stock, 'small_recovery') and stock['small_recovery'] == 1
