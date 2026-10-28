from copy import deepcopy
import json
from pathlib import Path

import pytest

from scripts.spec_check import validate_registry, REQUIRED_SECTIONS, load_registry

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def registry_tree(tmp_path):
    (tmp_path / 'docs').mkdir()
    (tmp_path / 'tests').mkdir()
    text = '# SPEC-TEST-001\n'
    for title in REQUIRED_SECTIONS:
        text += '## '+title+'\nContenido definido.\n'
        if title == 'Requisitos': text += '\n### REQ-TEST-001\nRegla.\n'
        if title == 'Criterios De Aceptacion': text += '\n### AC-TEST-001\nResultado verificable.\n'
    (tmp_path / 'docs/spec.md').write_text(text)
    (tmp_path / 'docs/plan.md').write_text('Plan con REQ-TEST-001.\n')
    (tmp_path / 'tests/test_sample.py').write_text('def test_example():\n    assert True\n')
    document = {'schema': 1,
        'specs': [{'id': 'SPEC-TEST-001', 'path': 'docs/spec.md', 'plan': 'docs/plan.md',
                   'status': 'retrospective-review', 'approval': None}],
        'deliveries': [{'id': 'DEL-TEST-001', 'status': 'local-unreleased', 'commit': None,
                        'evidence': ['docs/plan.md']}],
        'requirements': [{'id': 'REQ-TEST-001', 'spec': 'SPEC-TEST-001',
                          'title': 'Regla de prueba', 'status': 'implemented',
                          'acceptance': 'AC-TEST-001', 'implementation': ['tests/test_sample.py'],
                          'tests': [{'kind': 'pytest', 'target': 'tests/test_sample.py::test_example'}],
                          'delivery': 'DEL-TEST-001'}]}
    return tmp_path, document


def test_valid_registry_is_not_release_ready(registry_tree):
    root, doc = registry_tree
    assert validate_registry(doc, root) == []
    errors = validate_registry(doc, root, release=True)
    assert any('approval' in error for error in errors)
    assert any('release' in error for error in errors)


def test_duplicate_ids(registry_tree):
    root, doc = registry_tree
    doc['requirements'].append(deepcopy(doc['requirements'][0]))
    assert any('duplicate' in error for error in validate_registry(doc, root))


@pytest.mark.parametrize('change', ['criterion', 'section', 'function', 'file', 'spec', 'delivery', 'plan'])
def test_broken_trace_is_rejected(registry_tree, change):
    root, doc = registry_tree
    requirement = doc['requirements'][0]
    if change == 'criterion': requirement['acceptance'] = 'AC-MISSING-001'
    if change == 'section': (root / 'docs/spec.md').write_text('# SPEC-TEST-001\n')
    if change == 'function': requirement['tests'][0]['target'] = 'tests/test_sample.py::test_missing'
    if change == 'file': requirement['implementation'] = ['missing.py']
    if change == 'spec': requirement['spec'] = 'SPEC-MISSING-001'
    if change == 'delivery': requirement['delivery'] = 'DEL-MISSING-001'
    if change == 'plan': (root / 'docs/plan.md').write_text('No requirement linked.\n')
    assert validate_registry(doc, root)


@pytest.mark.parametrize('path', ['../escape.py', '/tmp/escape.py', 'docs/../docs/spec.md'])
def test_paths_are_confined(registry_tree, path):
    root, doc = registry_tree
    doc['requirements'][0]['implementation'] = [path]
    assert validate_registry(doc, root)


@pytest.mark.parametrize('field,value', [('status', 'verified'), ('status', 'invented')])
def test_status_cannot_fake_verification(registry_tree, field, value):
    root, doc = registry_tree
    doc['requirements'][0][field] = value
    assert validate_registry(doc, root)


def test_load_rejects_duplicate_json_keys(tmp_path):
    source = tmp_path / 'bad.json'
    source.write_text('{"schema":1,"schema":1}')
    with pytest.raises(ValueError):
        load_registry(source)


def test_unregistered_requirement_in_spec_is_rejected(registry_tree):
    root, doc = registry_tree
    path = root / 'docs/spec.md'
    text = path.read_text().replace('## Criterios De Aceptacion',
        '### REQ-TEST-ORPHAN\nSin registro.\n\n## Criterios De Aceptacion')
    path.write_text(text)
    assert validate_registry(doc, root)


@pytest.mark.parametrize('report', [[], {}, {'result': 'passed', 'verified_requirements': ['REQ-TEST-001']}])
def test_empty_or_malformed_execution_report_cannot_verify(registry_tree, report):
    root, doc = registry_tree
    (root / 'report.json').write_text(json.dumps(report))
    doc['requirements'][0].update(status='verified', verification='report.json')
    assert validate_registry(doc, root)


def test_real_registry():
    assert validate_registry(load_registry(ROOT / 'docs/requirements.json'), ROOT) == []
