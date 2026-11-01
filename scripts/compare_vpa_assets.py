"""Compare generated VPA trees by decoded pixels, not encoded byte layout."""
import argparse
from collections import defaultdict
import json
from pathlib import Path

from scripts.tdisplay_assets import decode_vpa


def compare(before, after):
    before, after = Path(before), Path(after)
    old = {p.relative_to(before): p for p in before.rglob('*.vpa')}
    new = {p.relative_to(after): p for p in after.rglob('*.vpa')}
    removed = sorted(str(p) for p in old.keys() - new.keys())
    added = sorted(str(p) for p in new.keys() - old.keys())
    changed = []
    for path in sorted(old.keys() & new.keys()):
        a, b = decode_vpa(old[path].read_bytes()), decode_vpa(new[path].read_bytes())
        if ((a.size, a.frame_count) != (b.size, b.frame_count)
                or any(x.tobytes() != y.tobytes() for x, y in zip(a.frames, b.frames))):
            changed.append(str(path))
    groups = defaultdict(lambda: {'before': 0, 'after': 0})
    for label, tree in (('before', old), ('after', new)):
        for path, file in tree.items():
            groups[path.parts[0]][label] += file.stat().st_size
    total_before = sum(p.stat().st_size for p in old.values())
    total_after = sum(p.stat().st_size for p in new.values())
    return {'before_bytes': total_before, 'after_bytes': total_after,
            'saved_bytes': total_before - total_after, 'compared_assets': len(old.keys() & new.keys()),
            'removed': removed, 'added': added, 'changed_pixels': changed, 'groups': dict(groups)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('before', type=Path)
    parser.add_argument('after', type=Path)
    args = parser.parse_args()
    result = compare(args.before, args.after)
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(1 if result['changed_pixels'] or result['added'] else 0)
