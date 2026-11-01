"""Lossless sharing keeps VPA1's random-access frame contract."""
import struct

from PIL import Image

from scripts.tdisplay_assets import HEADER, decode_vpa, encode_vpa


def test_identical_frames_share_storage_without_changing_sequence():
    red = Image.new('RGBA', (8, 8), 'red')
    blue = Image.new('RGBA', (8, 8), 'blue')
    sequence = [red, blue, red, red, blue]
    payload = encode_vpa(sequence, 8, 8)
    palette_count = HEADER.unpack_from(payload)[4]
    table = HEADER.size + palette_count * 2
    offsets = struct.unpack_from('<5I', payload, table)
    assert offsets[0] == offsets[2] == offsets[3]
    assert offsets[1] == offsets[4] != offsets[0]
    assert len(payload) == table + 5 * 4 + 2 * 64
    decoded = decode_vpa(payload)
    assert decoded.frame_count == 5
    assert [frame.tobytes() for frame in decoded.frames] == [frame.tobytes() for frame in sequence]


def test_transparency_distinguishes_frames_with_same_visible_color():
    opaque = Image.new('RGBA', (8, 8), 'red')
    cutout = opaque.copy()
    cutout.putpixel((0, 0), (255, 0, 0, 0))
    payload = encode_vpa([opaque, cutout, opaque], 8, 8)
    decoded = decode_vpa(payload)
    assert decoded.frames[0].getpixel((0, 0))[3] == 255
    assert decoded.frames[1].getpixel((0, 0))[3] == 0
    assert decoded.frames[2].tobytes() == decoded.frames[0].tobytes()


def test_adjacent_frames_share_transparent_padding_without_cropping():
    first = Image.new('RGBA', (8, 8))
    second = Image.new('RGBA', (8, 8))
    first.putpixel((0, 1), (255, 0, 0, 255))
    second.putpixel((0, 6), (0, 0, 255, 255))
    payload = encode_vpa([first, second, first], 8, 8)
    palette_count = HEADER.unpack_from(payload)[4]
    table = HEADER.size + palette_count * 2
    offsets = struct.unpack_from('<3I', payload, table)
    assert offsets[1] < offsets[0] + 64
    assert offsets[2] == offsets[0]
    decoded = decode_vpa(payload)
    assert decoded.size == (8, 8)
    assert [f.tobytes() for f in decoded.frames] == [f.tobytes() for f in (first, second, first)]


def test_fully_transparent_frames_do_not_corrupt_following_frames():
    empty = Image.new('RGBA', (8, 8))
    red = Image.new('RGBA', (8, 8))
    red.putpixel((4, 4), (255, 0, 0, 255))
    decoded = decode_vpa(encode_vpa([empty, red, empty, red], 8, 8))
    assert [f.getbbox() for f in decoded.frames] == [None, red.getbbox(), None, red.getbbox()]


def test_asset_comparison_reports_changed_pixels_and_removed_files(tmp_path):
    from scripts.compare_vpa_assets import compare
    before, after = tmp_path / 'before', tmp_path / 'after'
    before.mkdir()
    after.mkdir()
    red = encode_vpa([Image.new('RGBA', (8, 8), 'red')], 8, 8)
    blue = encode_vpa([Image.new('RGBA', (8, 8), 'blue')], 8, 8)
    (before / 'pet.vpa').write_bytes(red)
    (before / 'legacy.vpa').write_bytes(red)
    (after / 'pet.vpa').write_bytes(red)
    result = compare(before, after)
    assert result['changed_pixels'] == []
    assert result['removed'] == ['legacy.vpa']
    assert result['saved_bytes'] == len(red)
    (after / 'pet.vpa').write_bytes(blue)
    assert compare(before, after)['changed_pixels'] == ['pet.vpa']
