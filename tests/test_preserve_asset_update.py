import hashlib
import json

import pytest

from scripts.preserve_asset_update import prepare as prepare_update, hashes


def prepare(snapshot, assets, output):
    return prepare_update(snapshot, assets, output, inventory=hashes(snapshot))


def test_live_inventory_is_required_before_preparing_a_deployment(tmp_path):
    old, new, output = (tmp_path / name for name in ('old', 'new', 'output'))
    asset_tree(old)
    asset_tree(new)
    with pytest.raises(ValueError, match='LIVE_INVENTORY_REQUIRED'):
        prepare_update(old, new, output)
    assert not output.exists()


def test_host_extraction_must_match_live_inventory(tmp_path):
    old, new, output = (tmp_path / name for name in ('old', 'new', 'output'))
    asset_tree(old)
    asset_tree(new)
    inventory = hashes(old)
    inventory['collection/current.bin'] = 'missing-from-host-extraction'
    with pytest.raises(ValueError, match='inventory'):
        prepare_update(old, new, output, inventory=inventory)
    assert not output.exists()


def asset_tree(root, content=b'old'):
    (root / 'training').mkdir(parents=True)
    (root / 'training/pet.vpa').write_bytes(content)
    (root / 'manifest.json').write_text(json.dumps({'format': 1, 'assets': [
        {'path': 'training/pet.vpa', 'bytes': len(content),
         'sha256': hashlib.sha256(content).hexdigest()}]}))


def test_update_preserves_every_unmanaged_file_and_updates_only_assets(tmp_path):
    old, new, output = (tmp_path / name for name in ('old', 'new', 'output'))
    asset_tree(old)
    asset_tree(new, b'new')
    (new / '.gitkeep').write_bytes(b'')
    (old / 'collection').mkdir()
    (old / 'collection/state.bin').write_bytes(b'private-save')
    (old / 'training/custom.bin').write_bytes(b'unknown')
    result = prepare(old, new, output)
    assert result['preserved_files'] == 2
    assert (output / 'collection/state.bin').read_bytes() == b'private-save'
    assert (output / 'training/custom.bin').read_bytes() == b'unknown'
    assert (output / 'training/pet.vpa').read_bytes() == b'new'


def test_rejects_modified_managed_assets_and_existing_output(tmp_path):
    old, new, output = (tmp_path / name for name in ('old', 'new', 'output'))
    asset_tree(old)
    asset_tree(new, b'new')
    (old / 'training/pet.vpa').write_bytes(b'changed-on-board')
    with pytest.raises(ValueError, match='hash'):
        prepare(old, new, output)
    assert not output.exists()
    output.mkdir()
    with pytest.raises(ValueError, match='exists'):
        prepare(old, new, output)


@pytest.mark.parametrize('path', ['../collection/state.bin', 'collection/state.vpa', '/training/pet.vpa'])
def test_rejects_paths_outside_managed_asset_roots(tmp_path, path):
    old, new, output = (tmp_path / name for name in ('old', 'new', 'output'))
    asset_tree(old)
    asset_tree(new)
    manifest = json.loads((new / 'manifest.json').read_text())
    manifest['assets'][0]['path'] = path
    (new / 'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        prepare(old, new, output)
    assert not output.exists()


def test_rejects_collision_with_unknown_board_file(tmp_path):
    old, new, output = (tmp_path / name for name in ('old', 'new', 'output'))
    asset_tree(old)
    asset_tree(new)
    (old / 'training/custom.vpa').write_bytes(b'must-not-overwrite')
    (new / 'training/custom.vpa').write_bytes(b'new')
    manifest = json.loads((new / 'manifest.json').read_text())
    manifest['assets'].append({'path': 'training/custom.vpa', 'bytes': 3,
                              'sha256': hashlib.sha256(b'new').hexdigest()})
    (new / 'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match='collide'):
        prepare(old, new, output)


def test_obsolete_managed_file_is_removed_but_unknown_files_remain(tmp_path):
    old, new, output = (tmp_path / name for name in ('old', 'new', 'output'))
    asset_tree(old)
    asset_tree(new)
    (old / 'training/legacy.vpa').write_bytes(b'old')
    manifest = json.loads((old / 'manifest.json').read_text())
    manifest['assets'].append({'path': 'training/legacy.vpa', 'bytes': 3,
                              'sha256': hashlib.sha256(b'old').hexdigest()})
    (old / 'manifest.json').write_text(json.dumps(manifest))
    result = prepare(old, new, output)
    assert result['removed_assets'] == ['training/legacy.vpa']
    assert not (output / 'training/legacy.vpa').exists()


def test_rejects_output_nested_in_snapshot(tmp_path):
    old, new = tmp_path / 'old', tmp_path / 'new'
    asset_tree(old)
    asset_tree(new)
    with pytest.raises(ValueError, match='outside'):
        prepare(old, new, old / 'nested')


def test_repacked_littlefs_keeps_all_merged_file_hashes(tmp_path):
    import subprocess
    from pathlib import Path
    from scripts.preserve_asset_update import hashes
    tool = Path.home() / '.platformio/packages/tool-mklittlefs/mklittlefs'
    if not tool.is_file():
        pytest.skip('PlatformIO mklittlefs is not installed')
    old, new, output = (tmp_path / name for name in ('old', 'new', 'output'))
    asset_tree(old)
    asset_tree(new, b'new')
    (old / 'collection').mkdir()
    (old / 'collection/state.bin').write_bytes(b'preserve-this')
    result = prepare(old, new, output)
    image, extracted = tmp_path / 'test.bin', tmp_path / 'extracted'
    extracted.mkdir()
    geometry = ['-b', '4096', '-p', '256', '-s', '1048576']
    subprocess.run([str(tool), '-a', '-c', str(output), *geometry, str(image)], check=True)
    subprocess.run([str(tool), '-u', str(extracted), *geometry, str(image)], check=True)
    assert hashes(extracted) == result['merged_sha256']
