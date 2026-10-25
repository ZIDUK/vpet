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
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from scripts.tdisplay_assets import write_asset, write_catalog_header, write_manifest
from scripts.training_assets import package_training
from scripts.battle_assets import ACTIONS as BATTLE_ACTIONS, normalize_frames
from scripts.content_definitions import load_definition, validate_art, export, rules_registry
from core.content import ROLES


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


def build(root=ROOT, sim_build=None, data_dir=None, include_dir=None, definition=None):
    root = Path(root)
    if definition and definition.document != load_definition().document and root.resolve() == ROOT.resolve() and (data_dir is None or include_dir is None):
        raise ValueError("Alternative content requires separate data_dir and include_dir; not a board installer")
    sim_build = Path(sim_build or root / "build-tdisplay")
    data_dir = Path(data_dir or root / "firmware" / "t-display" / "data")
    include_dir = Path(include_dir or root / "firmware" / "t-display" / "include" / "generated")
    definition = definition or load_definition()
    export(check=True)
    validate_art(definition, sim_build)
    _reset_generated(data_dir)
    _reset_generated(include_dir)

    records = []
    animations = []
    for species in ROLES:
        stage = definition.stage(species)
        for semantic, source_clip in sorted(stage["actions"].items()):
            clip = definition.clip(species, semantic)
            source = sim_build / clip["atlas"].lstrip("/")
            action = source_clip.get("file", semantic)
            frames = _atlas_frames(source)
            relative = Path(clip["path"].lstrip("/"))
            record = write_asset(data_dir / relative, frames, frames[0].size,
                                 trim_transparent=action in ("tired","angry","eat","walk","fly","sleep",
                                                             "punch","cast","hurt","block","dodge","hit","hit_react"))
            records.append(record)
            if semantic in stage["battle_actions"] and action in BATTLE_ACTIONS:
                battle_frames = normalize_frames(frames)
                battle_path = Path(definition.clip(species, semantic, "battle")["path"].lstrip("/"))
                records.append(write_asset(data_dir / battle_path, battle_frames, battle_frames[0].size))
            animations.append({
                "species": species,
                "action": action,
                "path": relative.as_posix(),
                "frames": len(frames),
            })

    singles = []
    singles.extend((path, Path("ui/mood") / f"{path.stem}.vpa", True) for path in sorted((sim_build / "UIMood").glob("*.bmp")))
    singles.extend((path, Path("backgrounds") / f"{path.stem}.vpa", False) for path in sorted((sim_build / "Background").glob("*.bmp")))
    singles.extend((path, Path("ui/icons") / f"{path.stem.lower()}.vpa", False) for path in sorted((sim_build / "UIIcons").glob("*.bmp")))
    adopted_dir = Path(__file__).resolve().parents[1] / "assets/ui/items/adopted"
    for source in sorted(adopted_dir.glob("*.png")):
        with Image.open(source) as sprite:
            image = sprite.convert("RGBA").resize((16, 16), Image.Resampling.NEAREST)
            records.append(write_asset(data_dir / "ui/items" / (source.stem + ".vpa"), [image], image.size))
    singles.extend((sim_build / definition.stage(role)["portrait"].lstrip("/"),
                    Path(definition.stage(role)["portrait_asset"].lstrip("/")), True) for role in ROLES)
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

    records.extend(package_training(sim_build, data_dir, include_dir, definition))
    rules = rules_registry()
    catalog = {
        "format": 1,
        "display": {"width": 240, "height": 135, "menu_height": 24},
        "species": {role: {"name": definition.name(role), "stage": i} for i, role in enumerate(ROLES)},
        "content_definition": definition.document,
        "animations": sorted(animations, key=lambda item: (item["species"], item["action"])),
        "evolution": [
            {"from": "egg", "to": "baby", "automatic": False, "requirements_pending": False, "min_stage_age_seconds": 8},
        ] + [{"from": role, "to": rule["evolves_to"], **{k: v for k, v in rule.items() if k != "evolves_to"}}
             for role, rule in rules.items()],
    }
    manifest_path = write_manifest(data_dir, records, catalog)
    write_catalog_header(include_dir, catalog)
    manifest = json.loads(manifest_path.read_text())
    print(f"T-Display assets: {len(records)} files, {sum(item['bytes'] for item in manifest['assets'])} bytes")
    return manifest


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sim-build", default=str(ROOT / "build-tdisplay"))
    parser.add_argument("--definition", help="Validated build-time definition; not a board installer")
    parser.add_argument("--data-dir", type=Path)
    parser.add_argument("--include-dir", type=Path)
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    build(ROOT, sim_build=arguments.sim_build,
          data_dir=arguments.data_dir, include_dir=arguments.include_dir,
          definition=load_definition(arguments.definition) if arguments.definition else None)
