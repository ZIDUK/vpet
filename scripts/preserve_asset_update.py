"""Prepare an offline asset update; never access or flash a connected device."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil

ASSET_ROOTS = {'training', 'animations', 'battle', 'exploration', 'backgrounds', 'ui'}


def hashes(root):
    result = {}
    for file in root.rglob('*'):
        if file.is_symlink():
            raise ValueError('Symlink in snapshot')
        if file.is_file():
            result[file.relative_to(root).as_posix()] = hashlib.sha256(file.read_bytes()).hexdigest()
    return result


def managed(root, files):
    document = json.loads((root / 'manifest.json').read_text())
    if document.get('format') != 1 or not isinstance(document.get('assets'), list):
        raise ValueError('Unsupported manifest')
    result = set()
    for item in document['assets']:
        name = item['path']
        path = PurePosixPath(name)
        if (not name or path.is_absolute() or '..' in path.parts or '\\' in name
                or path.as_posix() != name or path.parts[0] not in ASSET_ROOTS
                or path.suffix != '.vpa' or name in result):
            raise ValueError('Unsafe or duplicate managed path: ' + name)
        if files.get(name) != item['sha256'] or (root / name).stat().st_size != item['bytes']:
            raise ValueError('Managed asset hash/size mismatch: ' + name)
        result.add(name)
    return result


def prepare(snapshot, assets, output, *, inventory=None):
    snapshot, assets, output = map(Path, (snapshot, assets, output))
    if output.exists():
        raise ValueError('Output exists; refusing to overwrite')
    if (snapshot.is_symlink() or assets.is_symlink()
            or output.resolve().is_relative_to(snapshot.resolve())
            or output.resolve().is_relative_to(assets.resolve())):
        raise ValueError('Output must be outside input trees; symlinks are not allowed')
    old_files, new_files = hashes(snapshot), hashes(assets)
    if inventory is None:
        raise ValueError('LIVE_INVENTORY_REQUIRED: host extraction alone is not proof of board state')
    if old_files != inventory:
        raise ValueError('Extracted snapshot differs from live board inventory')
    # Repository bookkeeping is not installed content. Board files, including
    # any existing .gitkeep, remain protected by the snapshot inventory.
    new_files.pop('.gitkeep', None)
    old_managed, new_managed = managed(snapshot, old_files), managed(assets, new_files)
    protected = {name: digest for name, digest in old_files.items()
                 if name != 'manifest.json' and name not in old_managed}
    if new_managed & protected.keys():
        raise ValueError('New assets collide with unmanaged board files')
    if set(new_files) != new_managed | {'manifest.json'}:
        raise ValueError('Generated asset directory contains unmanaged files')
    shutil.copytree(snapshot, output)
    for name in old_managed - new_managed:
        (output / name).unlink()
    for name in new_managed | {'manifest.json'}:
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(assets / name, target)
    merged = hashes(output)
    expected = dict(protected)
    expected.update(new_files)
    if merged != expected:
        raise ValueError('Merged tree verification failed; do not deploy')
    return {'preserved_files': len(protected), 'protected_sha256': protected,
            'merged_sha256': merged,
            'before_bytes': sum((snapshot / p).stat().st_size for p in old_files),
            'after_bytes': sum((output / p).stat().st_size for p in merged),
            'removed_assets': sorted(old_managed - new_managed)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('snapshot', type=Path)
    parser.add_argument('assets', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--inventory', type=Path, required=True,
                        help='Path->SHA256 inventory independently captured from the live device; not from host unpack')
    args = parser.parse_args()
    print(json.dumps(prepare(args.snapshot, args.assets, args.output,
                             inventory=json.loads(args.inventory.read_text())), indent=2, sort_keys=True))
