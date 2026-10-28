from pathlib import Path
import subprocess
import sys

from scripts.verify_local import run_checks, source_identity, check_commands, storage_preflight, persist_report


def test_failure_stops_and_records_not_run(tmp_path):
    checks = [('fail', [sys.executable, '-c', 'raise SystemExit(7)']),
              ('later', [sys.executable, '-c', 'print("must not run")'])]
    results = run_checks(checks, tmp_path, tmp_path)
    assert [entry['status'] for entry in results] == ['failed', 'not-run']
    assert results[0]['returncode'] == 7
    assert (tmp_path / '01-fail.log').exists()


def test_pass_has_real_exit_code(tmp_path):
    result = run_checks([('ok', [sys.executable, '-c', 'print("tested")'])], tmp_path, tmp_path)[0]
    assert result['status'] == 'passed' and result['returncode'] == 0
    assert 'tested' in (tmp_path / '01-ok.log').read_text()


def test_source_identity_includes_untracked_and_dirty_bytes(tmp_path):
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    (tmp_path / 'sample.txt').write_text('one')
    first = source_identity(tmp_path)
    (tmp_path / 'sample.txt').write_text('two')
    second = source_identity(tmp_path)
    assert first['head'] is None
    assert first['dirty'] and first['sha256'] != second['sha256']


def test_full_profile_builds_but_never_deploys(tmp_path):
    document = {'requirements': [{'tests': [{'kind': 'pytest', 'target': 'tests/test_hub_creator.py::test_generation_and_archive'},
                                           {'kind': 'browser', 'target': 'tests/hub_creator_browser.cjs'}]}]}
    checks = check_commands(document, 'full', tmp_path)
    assert {'cpp-native', 'esp32-build', 'browser-1'} <= {name for name, _ in checks}
    for _, command in checks:
        assert not {'deploy', 'upload', 'uploadfs', 'erase', '--firmware-only'} & set(command)


def test_full_profile_refuses_low_disk_before_spawning_tests(tmp_path):
    from types import SimpleNamespace
    usage = lambda path: SimpleNamespace(free=3*1024**3)
    result = storage_preflight('full', [tmp_path], usage)
    assert result['ok'] is False
    assert '6 GiB' in result['error']
    assert storage_preflight('creator', [tmp_path], usage)['ok'] is True


def test_report_write_failure_is_explicit_and_fails_closed(tmp_path, monkeypatch, capsys):
    reserve = tmp_path / 'reserve'
    reserve.write_bytes(b'reserved')
    def no_space(*args, **kwargs):
        raise OSError(28, 'No space left on device')
    monkeypatch.setattr(Path, 'write_text', no_space)
    report = {'result': 'passed'}
    assert persist_report(report, tmp_path, reserve) is False
    assert report['result'] == 'failed' and not reserve.exists()
    assert 'fallback JSON' in capsys.readouterr().err
