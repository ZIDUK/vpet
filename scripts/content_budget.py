"""Conservative logical budget; does not pretend payload bytes are LittleFS usage."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))


def budget(*, shared_bytes, package_bytes, individual_bytes, slots, journal_bytes,
           fs_capacity, reserve_bytes):
    values = [shared_bytes, individual_bytes, slots, journal_bytes, fs_capacity, reserve_bytes, *package_bytes]
    if any(type(v) is not int or v < 0 for v in values):
        raise ValueError("Budget requires nonnegative integer bytes/counts")
    installed = shared_bytes + sum(package_bytes)
    staging = max(package_bytes, default=0)
    records = individual_bytes * slots
    required = installed + staging + records + journal_bytes + reserve_bytes
    return {"shared_bytes": shared_bytes, "package_bytes": list(package_bytes),
            "installed_bytes": installed, "individual_bytes": records,
            "staging_bytes": staging, "journal_bytes": journal_bytes,
            "reserve_bytes": reserve_bytes, "required_bytes": required,
            "fs_capacity": fs_capacity, "fits": required <= fs_capacity}


def from_manifest(path):
    from core.content import ACTIONS, CONTEXTS, ROLES, PetDefinition
    manifest = json.loads(Path(path).read_text())
    definition = PetDefinition(manifest["content_definition"])
    owned = {definition.clip(role, action, context)["path"].lstrip("/")
             for role in ROLES for action in ACTIONS for context in CONTEXTS}
    owned.update(definition.stage(role)["portrait_asset"].lstrip("/") for role in ROLES)
    pet, shared = 0, 0
    for asset in manifest["assets"]:
        p = asset["path"]
        if p in owned:
            pet += asset["bytes"]
        else:
            shared += asset["bytes"]
    result = budget(shared_bytes=shared, package_bytes=[pet, pet], individual_bytes=4096,
                    slots=4, journal_bytes=131072, fs_capacity=12451840, reserve_bytes=1245184)
    result["assumptions"] = ["Second distinct art set modeled at current line size, not measured art",
                             "4 KiB per individual is a provisional budget, not serialized roster size",
                             "LittleFS overhead and real board free space must be measured separately"]
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    print(json.dumps(from_manifest(parser.parse_args().manifest), indent=2))
