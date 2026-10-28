"""Validate local spec traceability; does not run tests or authenticate approvals."""
import argparse
import ast
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_SECTIONS = ('Estado Y Aprobacion', 'Problema', 'Objetivo', 'Alcance', 'Exclusiones',
                     'Requisitos', 'Criterios De Aceptacion', 'Contratos Y Compatibilidad',
                     'Errores Y Recuperacion', 'Riesgos', 'Verificacion', 'Preguntas Pendientes')


def load_registry(path):
    def unique(pairs):
        values = {}
        for key, value in pairs:
            if key in values:
                raise ValueError('duplicate JSON key: ' + key)
            values[key] = value
        return values
    return json.loads(Path(path).read_text(), object_pairs_hook=unique)


def confined_file(root, value):
    if not isinstance(value, str) or not value or '\\' in value:
        raise ValueError('invalid path')
    path = Path(value)
    if path.is_absolute() or any(part in ('', '.', '..') for part in value.split('/')):
        raise ValueError('escaping or noncanonical path: ' + value)
    result = root / path
    if not result.resolve().is_relative_to(root.resolve()) or not result.is_file():
        raise ValueError('missing/escaping file: ' + value)
    return result


def pytest_nodes(document):
    return sorted({test['target'] for requirement in document['requirements']
                   for test in requirement['tests'] if test['kind'] == 'pytest'})


def browser_scripts(document):
    return sorted({test['target'] for requirement in document['requirements']
                   for test in requirement['tests'] if test['kind'] == 'browser'})


def _section(text, title):
    match = re.search(r'^## '+re.escape(title)+r'\s*\n(.*?)(?=^## |\Z)', text, re.M | re.S)
    return match.group(1).strip() if match else ''


def validate_registry(document, root=ROOT, release=False):
    root = Path(root)
    errors = []
    if not isinstance(document, dict) or type(document.get('schema')) is not int or document['schema'] != 1:
        return ['unsupported registry schema']
    tables = {}
    for key, prefix in [('specs', 'SPEC'), ('requirements', 'REQ'), ('deliveries', 'DEL')]:
        values = document.get(key)
        if not isinstance(values, list) or not values:
            errors.append(key + ': nonempty list required')
            tables[key] = {}
            continue
        indexed = {}
        for entry in values:
            if not isinstance(entry, dict) or not isinstance(entry.get('id'), str):
                errors.append(key + ': object with id required')
                continue
            identifier = entry['id']
            if not re.fullmatch(prefix+r'-[A-Z0-9]+(?:-[A-Z0-9]+)+', identifier):
                errors.append('invalid id: ' + identifier)
            if identifier in indexed:
                errors.append('duplicate id: ' + identifier)
            indexed[identifier] = entry
        tables[key] = indexed
    spec_text = {}
    for identifier, spec in tables['specs'].items():
        try:
            text = confined_file(root, spec.get('path')).read_text()
            plan = confined_file(root, spec.get('plan')).read_text()
            spec_text[identifier] = (text, plan)
            if identifier not in text:
                errors.append(identifier + ': missing spec identifier in document')
            declared = re.findall(r'^### (REQ-[A-Z0-9-]+)\s*$', _section(text, 'Requisitos'), re.M)
            registered = {key for key, item in tables['requirements'].items() if item.get('spec') == identifier}
            if set(declared) != registered or len(declared) != len(set(declared)):
                errors.append(identifier + ': unregistered, missing or duplicate requirement headings')
            for title in REQUIRED_SECTIONS:
                if not _section(text, title):
                    errors.append(identifier + ': missing/empty section ' + title)
            if re.search(r'\b(TODO|TBD)\b', text):
                errors.append(identifier + ': unresolved placeholder')
            if spec.get('status') not in ('draft', 'retrospective-review', 'scope-approved', 'approved'):
                errors.append(identifier + ': invalid spec status')
            if spec.get('status') == 'approved':
                approval = spec.get('approval')
                if not isinstance(approval, dict) or not all(approval.get(k) for k in ('by', 'date', 'evidence')):
                    errors.append(identifier + ': approval record required')
                else:
                    confined_file(root, approval['evidence'])
            if release and spec.get('status') != 'approved':
                errors.append(identifier + ': human approval pending')
        except (ValueError, OSError, UnicodeError) as error:
            errors.append(identifier + ': ' + str(error))
    for identifier, delivery in tables['deliveries'].items():
        try:
            if delivery.get('status') not in ('local-unreleased', 'released'):
                errors.append(identifier + ': invalid delivery status')
            evidence = delivery.get('evidence')
            if not isinstance(evidence, list) or not evidence:
                errors.append(identifier + ': evidence references required')
            else:
                for path in evidence:
                    confined_file(root, path)
            if release or delivery.get('status') == 'released':
                commit = delivery.get('commit')
                if delivery.get('status') != 'released' or not isinstance(commit, str) or not re.fullmatch(r'[0-9a-f]{40}', commit):
                    errors.append(identifier + ': release requires an actual full commit')
                elif subprocess.run(['git', 'cat-file', '-e', commit+'^{commit}'], cwd=root,
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode:
                    errors.append(identifier + ': release commit not found locally')
        except (ValueError, OSError) as error:
            errors.append(identifier + ': ' + str(error))
    criteria = set()
    for identifier, requirement in tables['requirements'].items():
        try:
            status = requirement.get('status')
            if status not in ('proposed', 'approved', 'implemented', 'verified'):
                errors.append(identifier + ': invalid requirement status')
            if not isinstance(requirement.get('title'), str) or not requirement['title'].strip():
                errors.append(identifier + ': title required')
            if requirement.get('spec') not in spec_text:
                errors.append(identifier + ': missing spec reference')
            else:
                text, plan = spec_text[requirement['spec']]
                if not re.search(r'^### '+re.escape(identifier)+r'\s*$', _section(text, 'Requisitos'), re.M):
                    errors.append(identifier + ': requirement missing from spec section')
                criterion = requirement.get('acceptance')
                if not isinstance(criterion, str) or not re.fullmatch(r'AC-[A-Z0-9]+(?:-[A-Z0-9]+)+', criterion):
                    errors.append(identifier + ': invalid acceptance identifier')
                elif criterion in criteria:
                    errors.append(identifier + ': duplicate acceptance criterion')
                else:
                    criteria.add(criterion)
                    if not re.search(r'^### '+re.escape(criterion)+r'\s*$', _section(text, 'Criterios De Aceptacion'), re.M):
                        errors.append(identifier + ': acceptance criterion missing from spec')
                if identifier not in plan:
                    errors.append(identifier + ': missing plan trace')
            if requirement.get('delivery') not in tables['deliveries']:
                errors.append(identifier + ': missing delivery reference')
            implementation = requirement.get('implementation')
            if not isinstance(implementation, list) or not implementation:
                errors.append(identifier + ': implementation references required')
            else:
                for path in implementation:
                    confined_file(root, path)
            tests = requirement.get('tests')
            if not isinstance(tests, list) or not tests:
                errors.append(identifier + ': test references required')
            else:
                for test in tests:
                    if not isinstance(test, dict) or not isinstance(test.get('target'), str):
                        raise ValueError('invalid test reference')
                    target = test['target']
                    file, *selectors = target.split('::')
                    source = confined_file(root, file)
                    if not file.startswith('tests/'):
                        raise ValueError('test must be under tests/')
                    if test.get('kind') == 'pytest' and source.suffix == '.py' and selectors:
                        members = ast.parse(source.read_text()).body
                        for selector in selectors:
                            name = selector.split('[', 1)[0]
                            match = next((node for node in members if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name == name), None)
                            if match is None:
                                raise ValueError('missing pytest function/class: ' + target)
                            members = match.body
                    elif test.get('kind') != 'browser' or selectors or source.suffix != '.cjs':
                        raise ValueError('unsupported test reference: ' + target)
            if status == 'verified':
                record = requirement.get('verification')
                if not isinstance(record, str):
                    errors.append(identifier + ': verified requires a recorded execution report')
                else:
                    report = load_registry(confined_file(root, record))
                    report = report if isinstance(report, dict) else {}
                    checks = report.get('checks', [])
                    source = report.get('source', {})
                    verified = report.get('verified_requirements', [])
                    valid = (report.get('result') == 'passed' and isinstance(verified, list)
                             and identifier in verified and report.get('source_unchanged') is True
                             and isinstance(source, dict) and isinstance(source.get('sha256'), str)
                             and re.fullmatch(r'[0-9a-f]{64}', source['sha256'])
                             and isinstance(checks, list) and bool(checks)
                             and all(isinstance(item, dict) and item.get('status') == 'passed'
                                     and type(item.get('returncode')) is int and item['returncode'] == 0
                                     for item in checks))
                    if not valid:
                        errors.append(identifier + ': execution report does not verify this requirement')
                    elif release:
                        delivery = tables['deliveries'].get(requirement.get('delivery'), {})
                        if source.get('dirty') is not False or source.get('head') != delivery.get('commit'):
                            errors.append(identifier + ': release evidence must match a clean delivery commit')
            if release and status != 'verified':
                errors.append(identifier + ': release requires verified evidence')
        except (ValueError, OSError, SyntaxError, UnicodeError) as error:
            errors.append(identifier + ': ' + str(error))
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registry', type=Path, default=ROOT / 'docs/requirements.json')
    parser.add_argument('--collect', action='store_true', help='Resolve pytest node IDs without running tests')
    parser.add_argument('--release', action='store_true', help='Also require recorded approval, verified evidence and release commit')
    args = parser.parse_args()
    try:
        document = load_registry(args.registry)
        errors = validate_registry(document, ROOT, args.release)
    except (ValueError, OSError) as error:
        errors = [str(error)]
    if errors:
        for error in errors:
            print('ERROR:', error)
        return 1
    if args.collect:
        result = subprocess.run([sys.executable, '-m', 'pytest', '--collect-only', '-q', '-p', 'no:cacheprovider',
                                 *pytest_nodes(document)], cwd=ROOT)
        if result.returncode:
            return result.returncode
    print(f"Traceability OK: {len(document['specs'])} specs, {len(document['requirements'])} requirements; no tests claimed passed.")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
