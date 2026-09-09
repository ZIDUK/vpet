"""Encode compact indexed assets for the native T-Display firmware."""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import struct

from PIL import Image


MAGIC = b"VPA1"
HEADER = struct.Struct("<4sHHHHB")


@dataclass(frozen=True)
class DecodedAsset:
    width: int
    height: int
    frame_count: int
    transparent_index: int
    palette: tuple
    frames: tuple

    @property
    def size(self):
        return self.width, self.height


def _rgb565(red, green, blue):
    return ((red & 0xF8) << 8) | ((green & 0xFC) << 3) | (blue >> 3)


def _rgb888(color):
    red = ((color >> 11) & 0x1F) * 255 // 31
    green = ((color >> 5) & 0x3F) * 255 // 63
    blue = (color & 0x1F) * 255 // 31
    return red, green, blue


def encode_vpa(frames, width, height):
    """Encode RGBA frames with one shared RGB565 palette and index-zero alpha."""
    frames = [frame.convert("RGBA") for frame in frames]
    if not frames:
        raise ValueError("A VPA asset needs at least one frame")
    if any(frame.size != (width, height) for frame in frames):
        raise ValueError(f"Every frame must be {width}x{height}")

    strip = Image.new("RGBA", (width * len(frames), height))
    for index, frame in enumerate(frames):
        strip.alpha_composite(frame, (index * width, 0))
    alpha = strip.getchannel("A")
    quantized = strip.convert("RGB").quantize(
        colors=255,
        method=Image.Quantize.MEDIANCUT,
        dither=Image.Dither.NONE,
    )
    palette_source = quantized.getpalette()
    strip_indices = bytes(
        0 if alpha_value < 128 else color_index + 1
        for color_index, alpha_value in zip(quantized.getdata(), alpha.getdata())
    )
    indexed = bytearray()
    strip_width = width * len(frames)
    for frame_index in range(len(frames)):
        frame_x = frame_index * width
        for row in range(height):
            start = row * strip_width + frame_x
            indexed.extend(strip_indices[start:start + width])
    indexed = bytes(indexed)
    used = max(indexed, default=0)
    palette = [0]
    for index in range(used):
        offset = index * 3
        palette.append(_rgb565(*palette_source[offset:offset + 3]))

    frame_bytes = width * height
    prefix_size = HEADER.size + len(palette) * 2 + len(frames) * 4
    offsets = [prefix_size + index * frame_bytes for index in range(len(frames))]
    payload = bytearray(
        HEADER.pack(MAGIC, width, height, len(frames), len(palette), 0)
    )
    payload.extend(struct.pack(f"<{len(palette)}H", *palette))
    payload.extend(struct.pack(f"<{len(offsets)}I", *offsets))
    payload.extend(indexed)
    return bytes(payload)


def decode_vpa(payload):
    """Decode VPA data for tests and host-side inspection."""
    if len(payload) < HEADER.size:
        raise ValueError("Truncated VPA header")
    magic, width, height, frame_count, palette_count, transparent = HEADER.unpack_from(payload)
    if magic != MAGIC:
        raise ValueError("Invalid VPA magic")
    palette_offset = HEADER.size
    offsets_offset = palette_offset + palette_count * 2
    pixels_offset = offsets_offset + frame_count * 4
    if pixels_offset > len(payload):
        raise ValueError("Truncated VPA tables")
    palette565 = struct.unpack_from(f"<{palette_count}H", payload, palette_offset)
    offsets = struct.unpack_from(f"<{frame_count}I", payload, offsets_offset)
    palette = tuple(_rgb888(color) for color in palette565)
    frame_size = width * height
    frames = []
    for offset in offsets:
        indices = payload[offset:offset + frame_size]
        if len(indices) != frame_size:
            raise ValueError("Truncated VPA frame")
        rgba = [
            (*palette[index], 0 if index == transparent else 255)
            for index in indices
        ]
        frame = Image.new("RGBA", (width, height))
        frame.putdata(rgba)
        frames.append(frame)
    return DecodedAsset(width, height, frame_count, transparent, palette, tuple(frames))


def write_asset(path, frames, size):
    path = Path(path)
    payload = encode_vpa(frames, *size)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return {
        "path": path.as_posix(),
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "width": size[0],
        "height": size[1],
        "frames": len(frames),
    }


def write_manifest(data_dir, records, catalog):
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    normalized = []
    for record in records:
        item = dict(record)
        path = Path(item["path"])
        try:
            item["path"] = path.relative_to(data_dir).as_posix()
        except ValueError:
            item["path"] = path.as_posix()
        normalized.append(item)
    manifest = dict(catalog)
    manifest["assets"] = sorted(normalized, key=lambda item: item["path"])
    target = data_dir / "manifest.json"
    target.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return target


def write_catalog_header(include_dir, catalog):
    include_dir = Path(include_dir)
    include_dir.mkdir(parents=True, exist_ok=True)
    animations = catalog["animations"]
    lines = [
        "#pragma once",
        "#include <stdint.h>",
        "",
        "namespace vpet::generated {",
        "struct AnimationAsset { const char* species; const char* action; const char* path; uint16_t frames; };",
        "inline constexpr AnimationAsset kAnimations[] = {",
    ]
    for item in animations:
        lines.append(
            f'    {{"{item["species"]}", "{item["action"]}", "/{item["path"]}", {item["frames"]}}},'
        )
    lines.extend([
        "};",
        "inline constexpr const char* kSpecies[] = {\"egg\", \"baby\", \"rookie\", \"champion\", \"ultimate\"};",
        "inline constexpr uint8_t kMenuActions[] = {0, 1, 2, 3, 4, 5, 6, 7};",
        "struct EvolutionEdge { const char* from; const char* to; bool requirementsPending; };",
        "inline constexpr EvolutionEdge kEvolutionEdges[] = {",
        '    {"egg", "baby", false},',
        '    {"baby", "rookie", true},',
        '    {"rookie", "champion", false},',
        '    {"champion", "ultimate", true},',
        "};",
        "}  // namespace vpet::generated",
        "",
    ])
    target = include_dir / "catalog.h"
    target.write_text("\n".join(lines))
    return target
