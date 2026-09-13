#!/usr/bin/env python3
"""Package the wide simulator artwork for the native ESP32 application."""
import argparse
import json
from pathlib import Path
import shutil
import sys

from PIL import Image

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.tdisplay_assets import write_asset, write_catalog_header, write_manifest


SPECIES = {
    "Egg": "egg",
    "Baby": "baby",
    "Rookie": "rookie",
    "Champion": "champion",
    "Ultimate": "ultimate",
}


def _rgba_image(path, transparent=False):
    with Image.open(path) as opened:
        if transparent and opened.mode == "P":
            background = opened.getpixel((0, 0))
            alpha = opened.point(
                [0 if index == background else 255 for index in range(256)],
                mode="L",
            )
            image = opened.convert("RGBA")
            image.putalpha(alpha)
            return image
        return opened.convert("RGBA")


def _atlas_frames(path):
    atlas = _rgba_image(path, transparent=True)
    frame_size = atlas.height
    if atlas.width % frame_size:
        raise ValueError(f"Atlas width is not divisible by frame size: {path}")
    return [
        atlas.crop((x, 0, x + frame_size, frame_size))
        for x in range(0, atlas.width, frame_size)
    ]


def _reset_generated(directory):
    directory.mkdir(parents=True, exist_ok=True)
    for child in directory.iterdir():
        if child.name == ".gitkeep":
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()


def build(root=ROOT, sim_build=None, data_dir=None, include_dir=None):
    root = Path(root)
    sim_build = Path(sim_build or root / "build-tdisplay")
    data_dir = Path(data_dir or root / "firmware" / "t-display" / "data")
    include_dir = Path(include_dir or root / "firmware" / "t-display" / "include" / "generated")
    _reset_generated(data_dir)
    _reset_generated(include_dir)

    records = []
    animations = []
    for stage, species in SPECIES.items():
        source_dir = sim_build / "digimon1" / stage
        for source in sorted(source_dir.glob("*_atlas.bmp")):
            action = source.stem.split("_", 1)[1].removesuffix("_atlas")
            frames = _atlas_frames(source)
            relative = Path("animations") / species / f"{source.stem.removesuffix('_atlas')}.vpa"
            record = write_asset(data_dir / relative, frames, frames[0].size)
            records.append(record)
            animations.append({
                "species": species,
                "action": action,
                "path": relative.as_posix(),
                "frames": len(frames),
            })

    singles = []
    singles.extend((path, Path("backgrounds") / f"{path.stem}.vpa", False) for path in sorted((sim_build / "Background").glob("*.bmp")))
    singles.extend((path, Path("ui/icons") / f"{path.stem.lower()}.vpa", False) for path in sorted((sim_build / "UIIcons").glob("*.bmp")))
    singles.extend((path, Path("ui/evolution") / f"{path.stem.lower()}.vpa", True) for path in sorted((sim_build / "UIEvolution").glob("*.bmp")))
    for source, relative, transparent in singles:
        image = _rgba_image(source, transparent=transparent)
        records.append(write_asset(data_dir / relative, [image], image.size))
    for source in sorted((sim_build / "UIFx").glob("*.bmp")):
        if source.stem.endswith("_atlas"):
            frames = _atlas_frames(source)
            relative = Path("ui/fx") / f"{source.stem.removesuffix('_atlas')}.vpa"
            records.append(write_asset(data_dir / relative, frames, frames[0].size))
        else:
            image = _rgba_image(source, transparent=True)
            relative = Path("ui/fx") / f"{source.stem.lower()}.vpa"
            records.append(write_asset(data_dir / relative, [image], image.size))

    catalog = {
        "format": 1,
        "display": {"width": 240, "height": 135, "menu_height": 24},
        "species": {
            "egg": {"name": "Egg", "stage": 0},
            "baby": {"name": "Sparkmon", "stage": 1},
            "rookie": {"name": "Firemon", "stage": 2},
            "champion": {"name": "Flamemon", "stage": 3},
            "ultimate": {"name": "Dragfiremon", "stage": 4},
        },
        "animations": sorted(animations, key=lambda item: (item["species"], item["action"])),
        "evolution": [
            {"from": "egg", "to": "baby", "automatic": False, "requirements_pending": False, "min_stage_age_seconds": 8},
            {"from": "baby", "to": "rookie", "automatic": True, "requirements_pending": False, "min_stage_age_seconds": 43800, "max_care_mistakes": 1},
            {"from": "rookie", "to": "champion", "automatic": True, "requirements_pending": False, "min_stage_age_seconds": 86400, "requirements": {"h": 55, "e": 55, "p": 55, "hp": 75}},
            {"from": "champion", "to": "ultimate", "automatic": True, "requirements_pending": False, "min_stage_age_seconds": 129600, "battles_required": 15},
        ],
    }
    manifest_path = write_manifest(data_dir, records, catalog)
    write_catalog_header(include_dir, catalog)
    manifest = json.loads(manifest_path.read_text())
    print(f"T-Display assets: {len(records)} files, {sum(item['bytes'] for item in manifest['assets'])} bytes")
    return manifest


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sim-build", default=str(ROOT / "build-tdisplay"))
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    build(ROOT, sim_build=arguments.sim_build)
