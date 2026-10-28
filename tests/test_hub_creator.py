import base64
from copy import deepcopy
from io import BytesIO
import json
import zipfile

import pytest
from PIL import Image

from scripts.hub_creator import inspect_project, export_project
from scripts.content_definitions import validate_art
from core.content import PetDefinition, ROLES


def png(size=(16, 8), opaque=False):
    image = Image.new('RGBA', size, (0, 0, 0, 255 if opaque else 0))
    image.paste((255, 100, 0, 255), (2, 2, size[0]-2, size[1]-2))
    out = BytesIO()
    image.save(out, 'PNG')
    return {'data': base64.b64encode(out.getvalue()).decode(), 'filename': 'test.png'}


@pytest.fixture
def project():
    return {'schema': 1, 'identity': {'id': 'author.aquamon', 'version': '1.0.0',
            'name': 'Aquamon', 'author': 'Autor', 'license': 'CC-BY-4.0',
            'description': 'Mi nueva mascota'},
            'stages': {role: {'name': 'AQUA'+str(i), 'short_name': 'AQUA'+str(i),
                'portrait': png((8, 8)), 'actions': {'idle': {'use': 'upload',
                'asset': png(), 'columns': 2, 'rows': 1, 'frames': 2,
                'interval_ms': 100}}} for i, role in enumerate(ROLES)},
            'resources': {'day': png((240, 135), opaque=True), 'reuse_day': True}}


def test_generation_and_archive(project, tmp_path):
    report = inspect_project(project)
    assert report['valid'] and not report['installable'], report
    definition = PetDefinition(report['definition'])
    assert definition.clip('rookie', 'punch')['frames'] == 2
    payload = export_project(project)
    with zipfile.ZipFile(BytesIO(payload)) as archive:
        names = archive.namelist()
        assert len(names) == len(set(names))
        assert 'content.json' in names and 'project.json' in names
        metadata = json.loads(archive.read('project.json'))
        assert metadata['identity']['author'] == 'Autor'
        assert metadata['installable'] is False
        assert all(not n.startswith('/') and '..' not in n.split('/') for n in names)
        archive.extractall(tmp_path)
    validate_art(definition, tmp_path / 'prepared')
    atlas = tmp_path / 'prepared' / definition.clip('baby', 'idle')['atlas'].lstrip('/')
    with Image.open(atlas) as image:
        assert image.size == (176, 88)
        assert image.mode == 'P' and image.getpixel((0, 0)) == 0


def test_missing_resources_not_exportable(project):
    del project['stages']['baby']['portrait']
    report = inspect_project(project)
    assert not report['valid']
    assert any('baby' in issue for issue in report['errors'])
    with pytest.raises(ValueError):
        export_project(project)


@pytest.mark.parametrize('change', ['grid', 'frames', 'interval', 'alias', 'image', 'loop', 'identity'])
def test_reject_invalid(project, change):
    clip = project['stages']['rookie']['actions']['idle']
    if change == 'grid': clip['columns'] = 3
    if change == 'frames': clip['frames'] = 65
    if change == 'interval': clip['interval_ms'] = 0
    if change == 'alias': project['stages']['rookie']['actions']['walk'] = {'use': 'walk'}
    if change == 'image': clip['asset']['data'] = base64.b64encode(b'not PNG').decode()
    if change == 'loop': clip['loop'] = [0, 8]
    if change == 'identity': project['identity']['id'] = '../escape'
    assert not inspect_project(project)['valid']


def test_no_mutation_and_new_dna_not_in_content(project):
    original = deepcopy(project)
    assert inspect_project(project)['valid']
    assert project == original
    assert 'dna' not in inspect_project(project)['definition']


@pytest.mark.parametrize('value', [None, [], 'invalid', 5, {'schema': 2}])
def test_bad_document(value):
    assert not inspect_project(value)['valid']


def test_background_and_portrait_dimensions(project):
    project['resources']['day'] = png((128, 128), opaque=True)
    project['stages']['egg']['portrait'] = png((16, 8))
    report = inspect_project(project)
    assert not report['valid']
    assert any('240x135' in error for error in report['errors'])
    assert any('Retrato cuadrado' in error for error in report['errors'])


def test_empty_frame_and_unknown_action(project):
    transparent = Image.new('RGBA', (16, 8))
    output = BytesIO()
    transparent.save(output, 'PNG')
    project['stages']['egg']['actions']['idle']['asset']['data'] = base64.b64encode(output.getvalue()).decode()
    report = inspect_project(project)
    assert not report['valid']
    assert any('transparentes' in error for error in report['errors'])
    project['stages']['rookie']['actions']['execute_script'] = {'use': 'idle'}
    assert not inspect_project(project)['valid']


def test_per_file_and_total_budget():
    from scripts.hub_creator import _png, MAX_FILE, MAX_TOTAL
    with pytest.raises(ValueError):
        _png({'data': 'x' * (((MAX_FILE+2)//3*4)+4)}, [0])
    with pytest.raises(ValueError):
        _png(png(), [MAX_TOTAL])


def test_source_layout_is_exported(project):
    with zipfile.ZipFile(BytesIO(export_project(project))) as archive:
        metadata = json.loads(archive.read('project.json'))
        assert metadata['source_layouts']['baby']['idle']['columns'] == 2
        assert 'asset' not in metadata['source_layouts']['baby']['idle']
