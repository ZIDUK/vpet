"""Capture a frozen device's file inventory using the read-only maintenance build."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re

CAPACITY = 0xBE0000


class MaintenanceError(ValueError):
    pass


def canonical(path):
    if (not re.fullmatch(r'/[A-Za-z0-9_./-]+', path) or len(path) > 192
            or '..' in PurePosixPath(path).parts or PurePosixPath(path).as_posix() != path
            or path == '/'):
        raise MaintenanceError('Unsafe inventory path')
    return path[1:]


def line(link):
    raw = link.readline()
    if not raw or len(raw) > 2048:
        raise MaintenanceError('Missing or oversized maintenance response')
    try:
        result = raw.decode('ascii').strip()
    except UnicodeError as error:
        raise MaintenanceError('Non-ASCII maintenance response') from error
    if result.startswith('MAINT ERR'):
        raise MaintenanceError(result)
    return result


def capture(link, baseline, output):
    baseline, output = Path(baseline), Path(output)
    if output.exists():
        raise MaintenanceError('Output already exists')
    link.write(b'VPET MAINT INVENTORY\n')
    # Boot logs may precede the first reply, but never ignore errors or wait forever.
    for _ in range(30):
        if line(link) == 'MAINT BEGIN':
            break
    else:
        raise MaintenanceError('Inventory did not begin')
    inventory, sizes, total = {}, {}, 0
    for _ in range(4097):
        record = line(link).split()
        if record[:2] == ['MAINT', 'END']:
            if len(record) != 3 or not record[2].isdigit() or int(record[2]) != len(inventory):
                raise MaintenanceError('Inventory count mismatch')
            break
        if len(record) != 5 or record[:2] != ['MAINT', 'FILE']:
            raise MaintenanceError('Unexpected inventory response')
        name = canonical(record[2])
        if (name in inventory or not record[3].isdigit()
                or not re.fullmatch('[0-9a-f]{64}', record[4])):
            raise MaintenanceError('Invalid inventory entry')
        size = int(record[3])
        total += size
        if total > CAPACITY:
            raise MaintenanceError('Inventory exceeds partition capacity')
        inventory[name], sizes[name] = record[4], size
    else:
        raise MaintenanceError('Too many files')
    if not inventory:
        raise MaintenanceError('Refusing empty inventory')
    output.mkdir(parents=True)
    for name, sha in inventory.items():
        source = baseline / name
        data = source.read_bytes() if source.is_file() and not source.is_symlink() else b''
        if len(data) != sizes[name] or hashlib.sha256(data).hexdigest() != sha:
            link.write(('VPET MAINT READ /' + name + '\n').encode('ascii'))
            if line(link) != f'MAINT READ /{name} {sizes[name]}':
                raise MaintenanceError('File header mismatch')
            chunks = bytearray()
            while True:
                record = line(link).split()
                if record[:2] == ['MAINT', 'DONE']:
                    if record != ['MAINT', 'DONE', sha]:
                        raise MaintenanceError('File hash mismatch')
                    break
                if (len(record) != 3 or record[:2] != ['MAINT', 'DATA']
                        or len(record[2]) % 2 or not re.fullmatch('[0-9a-f]+', record[2])):
                    raise MaintenanceError('Invalid file data')
                chunks.extend(bytes.fromhex(record[2]))
                if len(chunks) > sizes[name]:
                    raise MaintenanceError('File exceeds declared size')
            data = bytes(chunks)
        if len(data) != sizes[name] or hashlib.sha256(data).hexdigest() != sha:
            raise MaintenanceError('File size/hash mismatch: ' + name)
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return inventory


if __name__ == '__main__':
    import serial
    import time
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--inventory', type=Path, required=True)
    args = parser.parse_args()
    connection = serial.Serial()
    connection.port, connection.baudrate, connection.timeout = args.port, 115200, 10
    connection.dtr = connection.rts = False
    connection.open()
    try:
        time.sleep(1)
        connection.reset_input_buffer()
        inventory = capture(connection, args.baseline, args.output)
    finally:
        connection.close()
    args.inventory.write_text(json.dumps(inventory, indent=2, sort_keys=True) + '\n')
    print(f'Live inventory and snapshot verified: {len(inventory)} files')
