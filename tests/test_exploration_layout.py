"""Pin text containment and icon-bearing lists at the actual board resolution."""
from PIL import Image, ImageDraw
from pathlib import Path
import pytest
from core.pet import Pet
from scripts.exploration_session import ExplorationSession


def test_text_is_contained_even_with_font_offsets():
    from scripts.exploration_renderer import fitted_text
    from scripts.sim_renderer import _status_font
    image = Image.new('RGB', (240, 135))
    bounds = fitted_text(ImageDraw.Draw(image), (40, 48, 190, 60),
                         'JORNADA', _status_font(12), 'white')
    assert 40 <= bounds[0] <= bounds[2] <= 190
    assert 48 <= bounds[1] <= bounds[3] <= 60
    assert image.crop((0, 61, 240, 135)).getbbox() is None


@pytest.mark.parametrize('language', ['ES', 'EN'])
def test_prepare_uses_training_style_cell_borders_and_outline_buttons(language):
    from scripts import exploration_renderer as renderer
    pet = Pet(species='champion', state='live')
    pet.language = language
    session = ExplorationSession(pet, lambda _: True, lambda: 100000)
    session.page, session.route = 'confirm', 'jornada'
    image = Image.new('RGB', (240, 135))
    renderer.draw_exploration(image, Path('build-tdisplay'), pet, session, 100000)
    assert image.getpixel((70, 60)) == renderer.PANEL
    assert image.getpixel((160, 66)) == renderer.PANEL
    assert image.getpixel((163, 66)) == renderer.INK
    assert image.getpixel((70, 73)) == renderer.PANEL
    assert image.getpixel((4, 116)) == renderer.YELLOW
    assert image.getpixel((6, 131)) == renderer.INK


@pytest.mark.parametrize('language', ['ES', 'EN'])
@pytest.mark.parametrize('page,index,route', [
    ('routes', i, 'jornada') for i in range(4)] + [
    ('stats', i, 'jornada') for i in range(7)] + [
    ('confirm', 0, route) for route in ('patio', 'jornada', 'noche')])
def test_list_and_table_text_boxes_do_not_overlap(language, page, index, route, monkeypatch):
    from scripts import exploration_renderer as renderer
    pet = Pet(species='champion', state='live')
    pet.language = language
    pet.stats.update(h=100, e=100, p=100)
    session = ExplorationSession(pet, lambda _: True, lambda: 100000)
    session.page, session.index, session.route = page, index, route
    records = []
    fitted = renderer.fitted_text

    def observe(draw, box, value, font, color, **kwargs):
        bounds = fitted(draw, box, value, font, color, **kwargs)
        assert box[0] <= bounds[0] <= bounds[2] <= box[2]
        assert box[1] <= bounds[1] <= bounds[3] <= box[3]
        records.append(bounds)
        return bounds

    monkeypatch.setattr(renderer, 'fitted_text', observe)
    renderer.draw_exploration(Image.new('RGB', (240, 135)),
                              Path('build-tdisplay'),
                              pet, session, 100000)
    assert len(records) >= 4
    for i, a in enumerate(records):
        for b in records[i + 1:]:
            assert a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1]


@pytest.mark.parametrize('language', ['ES', 'EN'])
@pytest.mark.parametrize('route', ['patio', 'jornada', 'noche'])
@pytest.mark.parametrize('page', ['ready', 'recall', 'receipt'])
def test_return_screens_use_measured_table_and_real_rewards(language, route, page, monkeypatch):
    from scripts import exploration_renderer as renderer
    from core.exploration import DURATIONS
    pet = Pet(species='champion', state='live')
    pet.language = language
    pet.stats.update(h=100, e=60, p=100)
    now = 100000
    session = ExplorationSession(pet, lambda _: True, lambda: now)
    elapsed = DURATIONS[route] // 2 if page == 'recall' else DURATIONS[route]
    pet.exploration.start(pet, route, 'off', now - elapsed)
    reward = pet.exploration.preview(pet, now)
    session.page = 'trip' if page == 'ready' else page
    if page == 'receipt':
        pet.exploration.claim(pet, now)
    records, values = [], []
    fitted = renderer.fitted_text

    def observe(draw, box, value, font, color, **kwargs):
        bounds = fitted(draw, box, value, font, color, **kwargs)
        assert box[0] <= bounds[0] <= bounds[2] <= box[2]
        assert box[1] <= bounds[1] <= bounds[3] <= box[3]
        records.append(bounds)
        values.append(str(value))
        return bounds

    monkeypatch.setattr(renderer, 'fitted_text', observe)
    renderer.draw_exploration(Image.new('RGB', (240, 135)), Path('build-tdisplay'),
                              pet, session, now)
    assert ('TIEMPO' if language == 'ES' else 'TIME') in values
    assert ('OBJETO' if language == 'ES' else 'ITEM') in values
    assert ('GUIA' in values or 'GUIDE' in values) == reward['guide']
    if route == 'jornada':
        assert '+%d EV' % reward['ev'] in values
    if route == 'patio':
        assert '+%d ENE' % reward['energy'] in values
    for i, a in enumerate(records):
        for b in records[i + 1:]:
            assert a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1]
