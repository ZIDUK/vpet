import hashlib

import pytest

from scripts.asset_maintenance import capture, MaintenanceError


class Link:
    def __init__(self, lines):
        self.lines = iter(lines)
        self.sent = []

    def write(self, data):
        self.sent.append(data)

    def readline(self):
        return next(self.lines, b'')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def test_capture_recovers_files_missing_from_host_unpacker(tmp_path):
    baseline, output = tmp_path / 'baseline', tmp_path / 'live'
    baseline.mkdir()
    (baseline / 'manifest.json').write_bytes(b'catalog')
    link = Link([
        b'MAINT BEGIN\n',
        f'MAINT FILE /manifest.json 7 {digest(b"catalog")}\n'.encode(),
        f'MAINT FILE /collection/current.bin 4 {digest(b"save")}\n'.encode(),
        b'MAINT END 2\n',
        b'MAINT READ /collection/current.bin 4\n',
        b'MAINT DATA 73617665\n',
        f'MAINT DONE {digest(b"save")}\n'.encode(),
    ])
    inventory = capture(link, baseline, output)
    assert (output / 'collection/current.bin').read_bytes() == b'save'
    assert inventory['collection/current.bin'] == digest(b'save')
    assert link.sent == [b'VPET MAINT INVENTORY\n', b'VPET MAINT READ /collection/current.bin\n']


@pytest.mark.parametrize('record', [
    'MAINT FILE /../secret 4 ' + digest(b'save'),
    'MAINT FILE /collection/current.bin -1 ' + digest(b'save'),
    'MAINT FILE /collection/current.bin 4 invalid',
])
def test_capture_rejects_unsafe_inventory(tmp_path, record):
    with pytest.raises(MaintenanceError):
        capture(Link([b'MAINT BEGIN\n', (record + '\n').encode()]), tmp_path, tmp_path / 'out')


def test_capture_rejects_truncated_or_modified_file(tmp_path):
    link = Link([b'MAINT BEGIN\n',
                 f'MAINT FILE /save.bin 4 {digest(b"save")}\n'.encode(),
                 b'MAINT END 1\n', b'MAINT READ /save.bin 4\n',
                 b'MAINT DATA 61626364\n', f'MAINT DONE {digest(b"save")}\n'.encode()])
    with pytest.raises(MaintenanceError, match='hash'):
        capture(link, tmp_path / 'missing', tmp_path / 'out')


def test_capture_rejects_empty_response_and_count_mismatch(tmp_path):
    for lines in ([], [b'MAINT BEGIN\n', b'MAINT END 1\n']):
        with pytest.raises(MaintenanceError):
            capture(Link(lines), tmp_path / 'missing', tmp_path / 'out')


def test_capture_rejects_duplicate_paths_before_creating_output(tmp_path):
    record = f'MAINT FILE /save.bin 4 {digest(b"save")}\n'.encode()
    with pytest.raises(MaintenanceError):
        capture(Link([b'MAINT BEGIN\n', record, record]), tmp_path, tmp_path / 'out')
    assert not (tmp_path / 'out').exists()


def test_capture_rejects_inventory_larger_than_partition(tmp_path):
    record = f'MAINT FILE /huge.bin 16777216 {digest(b"save")}\n'.encode()
    with pytest.raises(MaintenanceError, match='capacity'):
        capture(Link([b'MAINT BEGIN\n', record]), tmp_path, tmp_path / 'out')
