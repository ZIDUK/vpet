"""Run bounded local checks and record evidence. Never deploys or publishes."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
import tempfile
from urllib.error import URLError
from urllib.request import urlopen
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.spec_check import load_registry, validate_registry, browser_scripts


def storage_preflight(profile, paths, usage=None):
    usage = usage or shutil.disk_usage
    minimum = 6*1024**3 if profile == 'full' else 128*1024**2
    locations = [{'path': str(path), 'free_bytes': usage(path).free} for path in paths]
    ok = all(location['free_bytes'] >= minimum for location in locations)
    return {'ok': ok, 'required_bytes': minimum, 'locations': locations,
            'error': '' if ok else ('Insufficient disk: '+('6 GiB' if profile == 'full' else '128 MiB')
                                   +' free required in workspace and temporary directory')}


def persist_report(report, output, reserve):
    try:
        reserve.unlink(missing_ok=True)
        (Path(output) / 'report.json').write_text(json.dumps(report, indent=2)+'\n')
        return True
    except OSError as error:
        report['result'] = 'failed'
        report['report_error'] = str(error)
        print('Could not persist report; fallback JSON follows:', file=sys.stderr)
        print(json.dumps(report), file=sys.stderr)
        return False


def source_identity(root=ROOT):
    def git(*args):
        return subprocess.run(['git', *args], cwd=root, capture_output=True)
    head = git('rev-parse', '--verify', 'HEAD')
    status = git('status', '--porcelain=v1', '--untracked-files=all')
    names = git('ls-files', '--cached', '--others', '--exclude-standard', '-z')
    if names.returncode or status.returncode:
        raise RuntimeError('Cannot fingerprint the Git working tree')
    digest = hashlib.sha256()
    for name in sorted(set(names.stdout.split(b'\0')) - {b''}):
        path = Path(root) / os.fsdecode(name)
        digest.update(name + b'\0')
        if path.is_symlink():
            digest.update(b'link:' + os.fsencode(os.readlink(path)))
        elif path.is_file():
            with path.open('rb') as stream:
                for chunk in iter(lambda: stream.read(1024*1024), b''):
                    digest.update(chunk)
        else:
            digest.update(b'<deleted>')
        digest.update(b'\0')
    return {'head': head.stdout.decode().strip() if head.returncode == 0 else None,
            'dirty': bool(status.stdout), 'status': status.stdout.decode(errors='replace').splitlines(),
            'sha256': digest.hexdigest()}


def run_checks(checks, root, output, env=None):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    results, stopped = [], False
    for index, (name, command) in enumerate(checks, 1):
        result = {'name': name, 'command': command, 'status': 'not-run', 'returncode': None}
        results.append(result)
        if stopped:
            continue
        log = output / f'{index:02d}-{name}.log'
        started = time.monotonic()
        try:
            with log.open('w') as stream:
                process = subprocess.run(command, cwd=root, env=env, stdout=stream,
                                         stderr=subprocess.STDOUT, timeout=900)
            result['returncode'] = process.returncode
            result['status'] = 'passed' if process.returncode == 0 else 'failed'
        except (OSError, subprocess.TimeoutExpired) as error:
            result['status'] = 'failed'
            result['error'] = str(error)
        result['seconds'] = round(time.monotonic()-started, 3)
        result['log'] = log.name
        stopped = result['status'] != 'passed'
        print(name + ': ' + result['status'], flush=True)
    return results


def check_commands(document, profile, output):
    python = sys.executable
    files = sorted({test['target'].split('::')[0] for requirement in document['requirements']
                    for test in requirement['tests'] if test['kind'] == 'pytest'})
    checks = [('traceability', [python, 'scripts/spec_check.py', '--collect']),
              ('pytest', [python, '-m', 'pytest', '-q', '--maxfail=1', '-p', 'no:cacheprovider',
                          '--junitxml='+str(output / 'pytest.xml'),
                          *(['tests/'] if profile == 'full' else files)]),
              ('hub-syntax', ['node', '--check', 'web/hub/app.js']),
              ('creator-syntax', ['node', '--check', 'web/hub/creator.js'])]
    if profile == 'full':
        checks.extend([
            ('content-generated', [python, 'scripts/content_definitions.py', '--check']),
            ('assets-build', ['make', 'build-tdisplay', 'PY='+python]),
            ('cpp-native', [python, '-m', 'platformio', 'test', '-d', 'firmware/t-display', '-e', 'native']),
            ('esp32-build', [python, '-m', 'platformio', 'run', '-d', 'firmware/t-display', '-e', 'tdisplay'])])
    for index, script in enumerate(browser_scripts(document), 1):
        checks.append((f'browser-{index}', ['node', script]))
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', choices=['creator', 'full'], default='creator')
    args = parser.parse_args()
    document = load_registry(ROOT / 'docs/requirements.json')
    errors = validate_registry(document, ROOT)
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        return 1
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    output = ROOT / 'out/local-verification' / (stamp+'-'+uuid4().hex[:8])
    output.mkdir(parents=True)
    report = {'schema': 1, 'started_at': stamp, 'profile': args.profile,
              'source': source_identity(), 'result': 'failed', 'checks': [],
              'verified_requirements': [], 'acceptance': 'automated-only',
              'release_ready': False, 'hardware': 'not-run', 'published': False,
              'pending_specs': [spec['id'] for spec in document['specs'] if spec['status'] != 'approved']}
    commands = check_commands(document, args.profile, output)
    report['checks'] = [{'name': name, 'command': command, 'status': 'not-run', 'returncode': None}
                        for name, command in commands]
    server = None
    reserve = output / 'report-space.reserve'
    try:
        report['storage'] = storage_preflight(args.profile, [ROOT, Path(tempfile.gettempdir())])
        if not report['storage']['ok']:
            raise RuntimeError(report['storage']['error'])
        # Hold actual allocated bytes for the final report even if tests fill the disk.
        with reserve.open('wb') as stream:
            stream.write(os.urandom(1024*1024))
            stream.flush()
            os.fsync(stream.fileno())
        # Own a separate loopback server; never stop the user's Hub or open USB.
        with socket.socket() as probe:
            probe.bind(('127.0.0.1', 0))
            port = probe.getsockname()[1]
        with (output / 'hub-server.log').open('w') as server_log:
            server = subprocess.Popen([sys.executable, 'scripts/hub_server.py', '--port', str(port)],
                                      cwd=ROOT, stdout=server_log, stderr=subprocess.STDOUT)
            url = f'http://127.0.0.1:{port}'
            deadline = time.monotonic()+15
            while True:
                if server.poll() is not None:
                    raise RuntimeError('Local Hub failed to start; see hub-server.log')
                try:
                    with urlopen(url+'/api/catalog', timeout=1) as response:
                        if response.status == 200:
                            break
                except (URLError, OSError):
                    pass
                if time.monotonic() >= deadline:
                    raise RuntimeError('Local Hub startup timed out')
                time.sleep(0.1)
            env = dict(os.environ, HUB_URL=url)
            report['checks'] = run_checks(commands, ROOT, output, env)
        report['source_end'] = source_identity()
        report['source_unchanged'] = report['source']['sha256'] == report['source_end']['sha256']
        if report['source_unchanged'] and all(item['status'] == 'passed' for item in report['checks']):
            report['result'] = 'passed'
            report['verified_requirements'] = [item['id'] for item in document['requirements']]
        elif not report['source_unchanged']:
            report['error'] = 'Source changed during verification; rerun against a stable tree'
    except (OSError, RuntimeError, KeyboardInterrupt) as error:
        report['error'] = str(error) or 'Interrupted'
    finally:
        if server is not None:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait()
        report['finished_at'] = datetime.now(timezone.utc).isoformat()
        saved = persist_report(report, output, reserve)
    print('Report:', output / 'report.json' if saved else 'stderr fallback (not persisted)')
    print('Result:', report['result'], '(automated scope only; no release or hardware acceptance)')
    return 0 if report['result'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
