from itertools import combinations
from pathlib import Path

import pytest
from PIL import ImageDraw
from core.adopted_items import ITEMS, menu_index
from core.pet import Pet
from scripts import build as build_script
from scripts.practice_session import PracticeSession
from scripts.practice_renderer import render_practice
from scripts.sim_renderer import render_frame
from display_profiles import get_display_profile


@pytest.fixture(scope='module')
def assets(tmp_path_factory):
    folder = tmp_path_factory.mktemp('consumables-ui')
    build_script.main(profile_name='tdisplay', output_dir=folder)
    return folder


@pytest.mark.parametrize('language', ['ES', 'EN'])
def test_all_adopted_home_and_battle_bag_choices_fit(assets, language, monkeypatch):
    pet = Pet(species='rookie', state='live')
    pet.language = language
    for item in ITEMS:
        if not item['unlimited']:
            pet.adopted_inventory[item['id']] = item['stack_max']
    records = []
    original = ImageDraw.ImageDraw.text

    def checked(draw, xy, value, *args, **kwargs):
        box = draw.textbbox(xy, str(value), font=kwargs.get('font'), anchor=kwargs.get('anchor'))
        assert 0 <= box[0] <= box[2] <= 240, (value, box)
        assert 0 <= box[1] <= box[3] <= 135, (value, box)
        records.append((value, box))
        return original(draw, xy, value, *args, **kwargs)

    def check():
        for (a, r), (b, s) in combinations(records, 2):
            assert r[2] <= s[0] or s[2] <= r[0] or r[3] <= s[1] or s[3] <= r[1], (a, b, r, s)

    monkeypatch.setattr(ImageDraw.ImageDraw, 'text', checked)
    for item in ITEMS:
        if item['unlimited']:
            continue
        records.clear()
        render_frame(assets, pet, panel_mode='inventory', panel_index=menu_index(item['id']),
                     profile=get_display_profile('tdisplay'))
        check()
    session = PracticeSession(pet, lambda _: True)
    session.page = 'items'
    for i in range(len(session.choices())):
        records.clear()
        session.index = i
        render_practice(assets, session, 1000)
        check()
    session.page, session.index = 'battle', 0
    session.battle.player.personality = 0
    session.battle.player.bond = 100
    session.battle.player.stats = (25, 20, 24, 20, 99, 20)
    session.battle.rival.hp = 1
    session._round(0, 1000)
    assert session.battle.result == 'VICTORIA'
    records.clear()
    render_practice(assets, session, 1000)
    check()
