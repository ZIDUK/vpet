#!/usr/bin/env python3
"""Create profile-sized runtime assets for Pico and T-Display."""
import argparse
import json
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps


ROOT = Path(__file__).parent.parent
SRC = ROOT / "src"
BUILD = ROOT / "build"
ASSETS = ROOT / "assets"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from core.options import OPTION_ICONS
from display_profiles import get_display_profile

ENTRYPOINT = "from app import run\n\nrun()\n"
MENU_ICONS = ("Status", "Feed", "Training", "Battle", "Rest", "Items", "Pedia", "Options")
STATUS_ICONS = ("Heart", "Clock", "Protein", "Medkit", "Energy", "Trophy", "Versus", "Weight")
IGNORED_NAMES = {".DS_Store", "__pycache__"}
FIREMON_COLUMNS = 5
FIREMON_ROWS = 4
FIREMON_FRAME_SIZE = 256
FIREMON_OUTPUT_SIZE = 64
ACTIVE_PROFILE = get_display_profile("pico")


def clean_build():
    if BUILD.exists():
        shutil.rmtree(BUILD)
    BUILD.mkdir(parents=True)


def copy_runtime_sources():
    """Copy importable modules without rewriting their imports."""
    for filename in ("app.py", "hal.py", "config.py"):
        source = SRC / filename
        if not source.exists():
            raise FileNotFoundError(f"Missing runtime source: {source}")
        shutil.copy2(source, BUILD / filename)

    runtime_packages = {
        "core": (
            "__init__.py",
            "evolution.py",
            "device_services.py",
            "dna.py",
            "inventory.py",
            "menu.py",
            "motion.py",
            "options.py",
            "pet.py",
            "save.py",
            "status_card.py",
        ),
        "ui": ("__init__.py", "sprites.py", "status.py"),
    }
    for directory, filenames in runtime_packages.items():
        target = BUILD / directory
        target.mkdir()
        for filename in filenames:
            source = SRC / directory / filename
            if not source.is_file():
                raise FileNotFoundError(f"Missing runtime source: {source}")
            shutil.copy2(source, target / filename)

    for filename in ("boot.py", "settings.toml"):
        source = SRC / filename
        if not source.exists():
            raise FileNotFoundError(f"Missing runtime source: {source}")
        shutil.copy2(source, BUILD / filename)

    (BUILD / "code.py").write_text(ENTRYPOINT)


def _swap_palette_index(image, source_index, target_index=0):
    if source_index == target_index:
        return image

    palette = image.getpalette()
    mapping = list(range(256))
    mapping[source_index], mapping[target_index] = target_index, source_index
    remapped = image.point(mapping)

    source_color = palette[source_index * 3:source_index * 3 + 3]
    target_color = palette[target_index * 3:target_index * 3 + 3]
    palette[target_index * 3:target_index * 3 + 3] = source_color
    palette[source_index * 3:source_index * 3 + 3] = target_color
    remapped.putpalette(palette)
    return remapped


def _quantize_rgba_with_transparency(image):
    """Reserve palette index 0 for transparent pixels without losing black art."""
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    rgb = rgba.convert("RGB")
    quantized = rgb.quantize(
        colors=255,
        method=Image.Quantize.MEDIANCUT,
        dither=Image.Dither.NONE,
    )

    output = Image.new("P", rgba.size, 0)
    output.putpalette([0, 0, 0] + quantized.getpalette()[: 255 * 3])
    output.putdata([
        0 if alpha_value < 128 else color_index + 1
        for color_index, alpha_value in zip(quantized.getdata(), alpha.getdata())
    ])
    return output


def save_runtime_bmp(source, target, transparent=False, expected_size=None, transform=None):
    """Save a positive-height, 8-bit paletted BMP suitable for displayio."""
    with Image.open(source) as opened:
        image = opened.copy()

    if transform is not None:
        image = transform(image)

    if expected_size and image.size != expected_size:
        raise ValueError(f"{source} must be {expected_size[0]}x{expected_size[1]}, got {image.size}")

    if transparent and "A" in image.getbands():
        image = _quantize_rgba_with_transparency(image)
    elif image.mode != "P":
        image = image.convert("RGB").quantize(
            colors=255 if transparent else 256,
            method=Image.Quantize.MEDIANCUT,
            dither=Image.Dither.NONE,
        )

    if transparent:
        image = _swap_palette_index(image, image.getpixel((0, 0)), 0)

    target.parent.mkdir(parents=True, exist_ok=True)
    image.save(target, format="BMP")


def repack_stacked_hatch_frames(image):
    """Turn the legacy 4x4 egg sheet into four centered 64x64 frames."""
    if image.size != (256, 64):
        return image

    background = image.getpixel((0, 0))
    first_tile = image.crop((0, 0, 64, 64))
    occupied_bands = 0
    for row in range(4):
        band = first_tile.crop((0, row * 16, 64, (row + 1) * 16))
        if any(pixel != background for pixel in band.getdata()):
            occupied_bands += 1
    if occupied_bands < 3:
        return image

    atlas = Image.new(image.mode, (256, 64), color=background)
    if image.mode == "P":
        atlas.putpalette(image.getpalette())
    for frame in range(4):
        cell = image.crop((frame * 64, frame * 16, (frame + 1) * 64, (frame + 1) * 16))
        atlas.paste(cell, (frame * 64, 24))
    return atlas


def collect_background():
    source_dir = ASSETS / "backgrounds"
    candidates = sorted(
        path for path in source_dir.iterdir()
        if path.is_file() and path.suffix.lower() in {".bmp", ".png"}
    ) if source_dir.exists() else []
    if not candidates:
        raise FileNotFoundError(f"No background image found in {source_dir}")

    source = candidates[0]
    target_size = (ACTIVE_PROFILE.width, ACTIVE_PROFILE.height)

    def fit_background(image):
        return ImageOps.fit(
            image.convert("RGB"),
            target_size,
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        )

    target = BUILD / "Background" / "background.bmp"
    save_runtime_bmp(source, target, expected_size=target_size, transform=fit_background)
    print(f"  background: {source.name} -> {target.relative_to(BUILD)}")

    def make_night(image):
        fitted = fit_background(image)
        dark = ImageEnhance.Brightness(fitted).enhance(0.34)
        blue = Image.new("RGB", dark.size, (8, 22, 52))
        return Image.blend(dark, blue, 0.28)

    night_target = BUILD / "Background" / "background_night.bmp"
    save_runtime_bmp(
        source,
        night_target,
        expected_size=target_size,
        transform=make_night,
    )
    print(f"  background: {source.name} -> {night_target.relative_to(BUILD)}")


def _build_firemon_atlas(
    source,
    rows,
    expected_frames,
    viewport,
    output_size,
    frame_indices=None,
    tile_size=FIREMON_OUTPUT_SIZE,
    columns=FIREMON_COLUMNS,
    frame_size=FIREMON_FRAME_SIZE,
):
    if not source.is_file():
        raise FileNotFoundError(f"Missing Firemon spritesheet: {source}")

    with Image.open(source) as opened:
        if "A" in opened.getbands():
            sheet = opened.convert("RGBA")
        elif opened.mode == "P":
            background_index = opened.getpixel((0, 0))
            alpha = opened.point(
                [0 if index == background_index else 255 for index in range(256)],
                mode="L",
            )
            sheet = opened.convert("RGBA")
            sheet.putalpha(alpha)
        else:
            sheet = opened.convert("RGBA")
            pixels = [
                (0, 0, 0, 0) if red < 12 and green < 12 and blue < 12 else (red, green, blue, alpha)
                for red, green, blue, alpha in sheet.getdata()
            ]
            sheet.putdata(pixels)
    expected = (columns * frame_size, rows * frame_size)
    if sheet.size[0] < expected[0] or sheet.size[1] < expected[1]:
        raise ValueError(f"{source} must be at least {expected[0]}x{expected[1]}, got {sheet.size}")
    if sheet.size != expected:
        sheet = sheet.crop((0, 0, expected[0], expected[1]))

    frames = []
    for row in range(rows):
        for column in range(columns):
            cell = sheet.crop(
                (
                    column * frame_size,
                    row * frame_size,
                    (column + 1) * frame_size,
                    (row + 1) * frame_size,
                )
            )
            if cell.getchannel("A").getbbox() is None:
                continue
            resized = cell.crop(viewport).resize(output_size, Image.Resampling.LANCZOS)
            frame = Image.new("RGBA", (tile_size, tile_size))
            frame.alpha_composite(
                resized,
                (
                    (tile_size - output_size[0]) // 2,
                    tile_size - output_size[1],
                ),
            )
            frames.append(frame)

    if len(frames) != expected_frames:
        raise ValueError(f"Expected {expected_frames} frames in {source}, found {len(frames)}")
    if frame_indices is not None:
        frames = [frames[index] for index in frame_indices]

    atlas = Image.new("RGBA", (len(frames) * tile_size, tile_size))
    for index, frame in enumerate(frames):
        atlas.alpha_composite(frame, (index * tile_size, 0))

    return atlas


def collect_pet_images():
    egg_dir = ASSETS / "digimon" / "digimon1" / "egg" / "idle"
    baby_dir = ASSETS / "digimon" / "digimon1" / "baby" / "idle"
    rookie_dir = ASSETS / "digimon" / "digimon1" / "rookie" / "idle"
    champion_dir = ASSETS / "digimon" / "digimon1" / "champion" / "idle"
    ultimate_dir = ASSETS / "digimon" / "digimon1" / "ultimate" / "idle"
    animations = (
        (
            "Egg", "idle", egg_dir / "egg_hatch.png", 4, 16,
            (60, 30, 200, 208), (50, 64), None, 64,
        ),
        (
            "Egg", "hatch", egg_dir / "egg_break.png", 4, 16,
            (8, 8, 248, 232), (64, 60), tuple(range(6, 16)), 64,
        ),
        (
            "Baby", "idle", baby_dir / "sparkmon_idle.png", 5, 25,
            (46, 38, 207, 220), (57, 64), None, 64,
        ),
        (
            "Baby", "walk", baby_dir / "sparkmon_walk.png", 5, 25,
            (36, 36, 207, 224), (58, 64), None, 64,
        ),
        (
            "Baby", "eat", baby_dir / "sparkmon_eat.png", 5, 25,
            (38, 34, 207, 224), (57, 64), None, 64,
        ),
        (
            "Baby", "sleep", baby_dir / "sparkmon_sleep.png", 5, 25,
            (24, 24, 214, 218), (63, 64), None, 64,
        ),
        (
            "Baby", "evolution", baby_dir / "sparkmon_evolution.png", 4, 16,
            (48, 48, 208, 208), (112, 112), None, 112,
        ),
        ("Rookie", "idle", rookie_dir / "firemon_idle.png", FIREMON_ROWS, 19, (48, 52, 184, 216), (53, 64), None, 64),
        ("Rookie", "walk", rookie_dir / "firemon_walk.png", 5, 22, (40, 48, 180, 208), (56, 64), None, 64),
        ("Rookie", "eat", rookie_dir / "firemon_eat.png", 5, 25, (44, 48, 204, 216), (61, 64), None, 64),
        (
            "Rookie",
            "punch",
            rookie_dir / "firemon_punch.png",
            5,
            25,
            (24, 52, 234, 220),
            (64, 52),
            tuple(range(0, 1)) + tuple(range(6, 20)),
            64,
        ),
        (
            "Rookie",
            "sleep",
            rookie_dir / "firemon_sleep.png",
            5,
            25,
            (18, 30, 215, 219),
            (64, 61),
            tuple(range(13)) + (18, 24),
            64,
        ),
        (
            "Rookie",
            "cast",
            rookie_dir / "firemon_cast.png",
            5,
            25,
            (37, 45, 256, 202),
            (64, 46),
            (0, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 18, 19, 24),
            64,
        ),
        (
            "Rookie",
            "hit",
            rookie_dir / "firemon_hit.png",
            5,
            25,
            (0, 20, 204, 190),
            (64, 54),
            (0, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 18, 19, 24),
            64,
            204,
        ),
        (
            "Rookie",
            "hurt",
            rookie_dir / "firemon_hurt.png",
            5,
            25,
            (0, 20, 204, 190),
            (64, 54),
            (0, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 18, 19, 24),
            64,
            204,
        ),
        (
            "Rookie",
            "dodge",
            rookie_dir / "firemon_dodge.png",
            5,
            25,
            (0, 20, 204, 190),
            (64, 54),
            (0, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 18, 19, 24),
            64,
            204,
        ),
        (
            "Rookie",
            "block",
            rookie_dir / "firemon_block.png",
            5,
            25,
            (0, 20, 204, 190),
            (64, 54),
            (0, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 18, 19, 24),
            64,
            204,
        ),
        (
            "Rookie", "evolution", rookie_dir / "firemon_evolution.png", 5, 25,
            (48, 40, 208, 216), (112, 112),
            (0, 4, 8, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 22, 24), 112,
        ),
        (
            "Champion", "idle", champion_dir / "flamemon_idle.png", 5, 25,
            (35, 30, 179, 222), (48, 64), tuple(range(0, 25, 2)) + (21, 23), 64,
        ),
        (
            "Champion", "walk", champion_dir / "flamemon_walk.png", 5, 25,
            (24, 22, 203, 231), (55, 64), tuple(range(0, 25, 2)) + (21, 23), 64,
        ),
        (
            "Champion", "eat", champion_dir / "flamemon_eat.png", 5, 25,
            (35, 30, 203, 222), (56, 64), None, 64,
        ),
        (
            "Champion", "punch", champion_dir / "flamemon_punch.png", 5, 25,
            (30, 35, 234, 221), (64, 58),
            tuple(range(0, 1)) + tuple(range(6, 20)), 64,
        ),
        (
            "Champion", "sleep", champion_dir / "flamemon_sleep.png", 5, 25,
            (35, 30, 179, 222), (48, 64), tuple(range(13)) + (18, 24), 64,
        ),
        (
            "Champion", "cast", champion_dir / "flamemon_cast.png", 5, 25,
            (27, 30, 256, 222), (64, 54),
            (0, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 18, 19, 24), 64,
        ),
        (
            "Champion", "evolution", champion_dir / "flamemon_evolution.png", 5, 25,
            (32, 24, 208, 232), (112, 112),
            (0, 4, 8, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 22, 24), 112,
        ),
        (
            "Ultimate", "idle", ultimate_dir / "dragfiremon_idle.png", 5, 25,
            (48, 30, 204, 224), (51, 64), None, 64,
        ),
        (
            "Ultimate", "fly", ultimate_dir / "dragfiremon_fly.png", 5, 25,
            (20, 0, 234, 224), (61, 64), None, 64,
        ),
        (
            "Ultimate", "eat", ultimate_dir / "dragfiremon_eat.png", 5, 25,
            (30, 26, 212, 224), (59, 64), None, 64,
        ),
        (
            "Ultimate", "punch", ultimate_dir / "dragfiremon_punch.png", 5, 25,
            (20, 30, 256, 224), (64, 53),
            tuple(range(0, 1)) + tuple(range(6, 20)), 64,
        ),
        (
            "Ultimate", "sleep", ultimate_dir / "dragfiremon_sleep.png", 5, 25,
            (8, 36, 210, 208), (64, 55), None, 64,
        ),
        (
            "Ultimate", "cast", ultimate_dir / "dragfiremon_cast.png", 5, 25,
            (20, 30, 256, 224), (64, 53),
            (0, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 18, 19, 24), 64,
        ),
    )
    for spec in animations:
        stage, name, source, rows, source_frames, viewport, output_size, frame_indices, tile_size = spec[:9]
        frame_size = spec[9] if len(spec) > 9 else FIREMON_FRAME_SIZE
        base_tile_size = tile_size
        tile_size = (
            ACTIVE_PROFILE.pet_size
            if base_tile_size == FIREMON_OUTPUT_SIZE
            else ACTIVE_PROFILE.height - ACTIVE_PROFILE.menu_height
        )
        scale = tile_size / base_tile_size
        output_size = tuple(max(1, round(value * scale)) for value in output_size)
        atlas = _build_firemon_atlas(
            source,
            rows,
            source_frames,
            viewport,
            output_size,
            frame_indices,
            tile_size,
            columns=(
                4
                if stage == "Egg" or (stage == "Baby" and name == "evolution")
                else FIREMON_COLUMNS
            ),
            frame_size=frame_size,
        )
        frame_count = atlas.width // tile_size
        prefix = {
            "Egg": "egg",
            "Baby": "sparkmon",
            "Rookie": "firemon",
            "Champion": "flamemon",
            "Ultimate": "dragfiremon",
        }[stage]
        target = BUILD / "digimon1" / stage / f"{prefix}_{name}_atlas.bmp"
        save_runtime_bmp(
            source,
            target,
            transparent=True,
            expected_size=(frame_count * tile_size, tile_size),
            transform=lambda _, generated=atlas: generated,
        )
        print(f"  pet animation: {target.name} ({frame_count} frames)")


def collect_ui():
    source_dir = ASSETS / "ui" / "icons"

    def resize_icon(image):
        size = ACTIVE_PROFILE.icon_size
        return image.convert("RGB").resize((size, size), Image.Resampling.LANCZOS)

    names = tuple(dict.fromkeys((*MENU_ICONS, *STATUS_ICONS, *OPTION_ICONS)))
    for name in names:
        source = source_dir / f"{name}.png"
        if not source.is_file():
            raise FileNotFoundError(f"Missing menu icon: {source}")
        target = BUILD / "UIIcons" / f"{name}.bmp"
        size = ACTIVE_PROFILE.icon_size
        save_runtime_bmp(source, target, expected_size=(size, size), transform=resize_icon)
    print(f"  menu icons: {len(names)}")


def collect_fx():
    source_dir = ASSETS / "ui" / "fx"
    bag_sheet = source_dir / "bag_sheet.png"
    if not bag_sheet.is_file():
        raise FileNotFoundError(f"Missing fx sprite: {bag_sheet}")
    tile_size = ACTIVE_PROFILE.pet_size
    scale = tile_size / FIREMON_OUTPUT_SIZE
    bag_atlas = _build_firemon_atlas(
        bag_sheet,
        4,
        16,
        (0, 16, 256, 220),
        (max(1, round(48 * scale)), max(1, round(64 * scale))),
        None,
        tile_size,
        columns=4,
        frame_size=256,
    )
    bag_target = BUILD / "UIFx" / "bag_atlas.bmp"
    save_runtime_bmp(
        bag_sheet,
        bag_target,
        transparent=True,
        expected_size=(16 * tile_size, tile_size),
        transform=lambda _, generated=bag_atlas: generated,
    )
    print(f"  fx: {bag_target.name} (16 frames)")

    grave_source = source_dir / "grave.png"
    if not grave_source.is_file():
        raise FileNotFoundError(f"Missing fx sprite: {grave_source}")
    grave_size = (88, 88)

    def resize_grave(image):
        return image.convert("RGBA").resize(grave_size, Image.Resampling.LANCZOS)

    grave_target = BUILD / "UIFx" / "grave.bmp"
    save_runtime_bmp(
        grave_source,
        grave_target,
        transparent=True,
        expected_size=grave_size,
        transform=resize_grave,
    )
    print(f"  fx: {grave_target.name}")


def collect_evolution_thumbnails():
    """Generate small portraits from the same idle atlases used by the pet."""
    portraits = (
        (BUILD / "digimon1" / "Egg" / "egg_idle_atlas.bmp", "Egg.bmp"),
        (BUILD / "digimon1" / "Baby" / "sparkmon_idle_atlas.bmp", "Sparkmon.bmp"),
        (BUILD / "digimon1" / "Rookie" / "firemon_idle_atlas.bmp", "Firemon.bmp"),
        (BUILD / "digimon1" / "Champion" / "flamemon_idle_atlas.bmp", "Flamemon.bmp"),
        (BUILD / "digimon1" / "Ultimate" / "dragfiremon_idle_atlas.bmp", "Dragfiremon.bmp"),
    )

    def first_frame(image):
        tile_size = ACTIVE_PROFILE.pet_size
        frame = image.crop((0, 0, tile_size, tile_size))
        if frame.mode == "P":
            alpha = frame.point([0] + [255] * 255, mode="L")
            frame = frame.convert("RGBA")
            frame.putalpha(alpha)
        else:
            frame = frame.convert("RGBA")
        size = ACTIVE_PROFILE.portrait_size
        bounds = frame.getchannel("A").getbbox()
        if bounds:
            frame = frame.crop(bounds)
        available = size - 4
        scale = min(available / frame.width, available / frame.height)
        fitted = frame.resize(
            (max(1, round(frame.width * scale)), max(1, round(frame.height * scale))),
            Image.Resampling.NEAREST,
        )
        portrait = Image.new("RGBA", (size, size))
        portrait.alpha_composite(
            fitted,
            ((size - fitted.width) // 2, (size - fitted.height) // 2),
        )
        return portrait

    for source, filename in portraits:
        target = BUILD / "UIEvolution" / filename
        save_runtime_bmp(
            source,
            target,
            transparent=True,
            expected_size=(ACTIVE_PROFILE.portrait_size,) * 2,
            transform=first_frame,
        )
    print(f"  evolution portraits: {len(portraits)}")


def validate_runtime_assets():
    required = [
        "Background/background.bmp",
        "Background/background_night.bmp",
        "digimon1/Egg/egg_idle_atlas.bmp",
        "digimon1/Egg/egg_hatch_atlas.bmp",
        "digimon1/Baby/sparkmon_idle_atlas.bmp",
        "digimon1/Baby/sparkmon_walk_atlas.bmp",
        "digimon1/Baby/sparkmon_eat_atlas.bmp",
        "digimon1/Baby/sparkmon_sleep_atlas.bmp",
        "digimon1/Baby/sparkmon_evolution_atlas.bmp",
        "digimon1/Rookie/firemon_idle_atlas.bmp",
        "digimon1/Rookie/firemon_walk_atlas.bmp",
        "digimon1/Rookie/firemon_eat_atlas.bmp",
        "digimon1/Rookie/firemon_punch_atlas.bmp",
        "digimon1/Rookie/firemon_sleep_atlas.bmp",
        "digimon1/Rookie/firemon_cast_atlas.bmp",
        "digimon1/Rookie/firemon_hit_atlas.bmp",
        "digimon1/Rookie/firemon_hurt_atlas.bmp",
        "digimon1/Rookie/firemon_dodge_atlas.bmp",
        "digimon1/Rookie/firemon_block_atlas.bmp",
        "digimon1/Rookie/firemon_evolution_atlas.bmp",
        "digimon1/Champion/flamemon_idle_atlas.bmp",
        "digimon1/Champion/flamemon_walk_atlas.bmp",
        "digimon1/Champion/flamemon_eat_atlas.bmp",
        "digimon1/Champion/flamemon_punch_atlas.bmp",
        "digimon1/Champion/flamemon_sleep_atlas.bmp",
        "digimon1/Champion/flamemon_cast_atlas.bmp",
        "digimon1/Champion/flamemon_evolution_atlas.bmp",
        "digimon1/Ultimate/dragfiremon_idle_atlas.bmp",
        "digimon1/Ultimate/dragfiremon_fly_atlas.bmp",
        "digimon1/Ultimate/dragfiremon_eat_atlas.bmp",
        "digimon1/Ultimate/dragfiremon_punch_atlas.bmp",
        "digimon1/Ultimate/dragfiremon_sleep_atlas.bmp",
        "digimon1/Ultimate/dragfiremon_cast_atlas.bmp",
        "UIEvolution/Egg.bmp",
        "UIEvolution/Sparkmon.bmp",
        "UIEvolution/Firemon.bmp",
        "UIEvolution/Flamemon.bmp",
        "UIEvolution/Dragfiremon.bmp",
    ]
    required.extend(f"UIIcons/{name}.bmp" for name in dict.fromkeys((*MENU_ICONS, *STATUS_ICONS, *OPTION_ICONS)))
    required.extend(("UIFx/bag_atlas.bmp", "UIFx/grave.bmp"))
    missing = [path for path in required if not (BUILD / path).is_file()]
    if missing:
        raise FileNotFoundError("Missing runtime asset(s): " + ", ".join(missing))


def write_manifest():
    files = sorted(
        str(path.relative_to(BUILD))
        for path in BUILD.rglob("*")
        if path.is_file() and path.name not in IGNORED_NAMES
    )
    (BUILD / ".vpet-manifest.json").write_text(
        json.dumps({"version": 1, "files": files}, indent=2) + "\n"
    )
    print(f"  manifest: {len(files)} files")


def main(profile_name="pico", output_dir=None):
    global ACTIVE_PROFILE, BUILD
    previous_profile = ACTIVE_PROFILE
    previous_build = BUILD
    ACTIVE_PROFILE = get_display_profile(profile_name)
    if output_dir is not None:
        BUILD = Path(output_dir)
    print("=== build.py ===")
    try:
        clean_build()
        copy_runtime_sources()
        collect_background()
        collect_pet_images()
        collect_evolution_thumbnails()
        collect_ui()
        collect_fx()
        validate_runtime_assets()
        write_manifest()
        print("OK")
    finally:
        ACTIVE_PROFILE = previous_profile
        BUILD = previous_build


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=("pico", "tdisplay"), default="pico")
    parser.add_argument("--output")
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    main(arguments.profile, arguments.output)
