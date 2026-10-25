"""Portable presentation definitions; never read or mutate an individual's save."""

ROLES = ("egg", "baby", "rookie", "champion", "ultimate")
LEGACY_ROLES = ("rookie", "champion", "ultimate", "egg", "baby")
ACTIONS = ("idle", "walk", "eat", "punch", "cast", "sleep", "evolution", "hatch",
           "hit", "hurt", "dodge", "block", "happy", "sad", "tired", "angry", "hit_react")
CONTEXTS = ("home", "training", "battle", "exploration")


def _path(value, maximum=63):
    if not isinstance(value, str) or not value or len(value) > maximum:
        raise ValueError("Invalid content path length")
    if any(part in (".", "..", "") for part in value.lstrip("/").split("/")):
        raise ValueError("Invalid content path")
    if any(not (c.isascii() and (c.isalnum() or c in "/._-")) for c in value):
        raise ValueError("Invalid content path characters")


class PetDefinition:
    def __init__(self, document):
        if not isinstance(document, dict):
            raise ValueError("Content definition must be an object")
        self.document = document
        if type(document.get("schema")) is not int or document["schema"] != 1 or document.get("profile") != "tdisplay-240x135":
            raise ValueError("Unsupported content schema/profile")
        allowed = {"schema", "id", "version", "profile", "background", "background_night",
                   "background_asset", "background_night_asset", "stages"}
        if set(document) - allowed:
            raise ValueError("Unsupported content fields")
        for key in ("id", "version"):
            _path(document.get(key, ""))
        for key in ("background", "background_night", "background_asset", "background_night_asset"):
            _path(document.get(key, ""))
        if not isinstance(document.get("stages"), dict) or set(document["stages"]) != set(ROLES):
            raise ValueError("Content requires the five supported roles")
        outputs = {}
        for role in ROLES:
            stage = self.stage(role)
            if not isinstance(stage, dict):
                raise ValueError("Invalid stage definition")
            for key in ("name", "short_name", "battle_name"):
                value = stage.get(key)
                if not isinstance(value, str) or not value or len(value) > 12 or not value.isascii():
                    raise ValueError("Invalid content name")
            for key in ("stem", "atlas_root", "home_root", "portrait", "portrait_asset",
                        "training_prefix", "battle_prefix", "exploration_prefix"):
                _path(stage.get(key, ""))
            if "/" in stage["stem"] or "." in stage["stem"]:
                raise ValueError("Invalid asset stem")
            actions, aliases = stage.get("actions", {}), stage.get("aliases", {})
            if not isinstance(actions, dict) or not isinstance(aliases, dict):
                raise ValueError("Invalid action maps")
            if "idle" not in actions or set(actions) & set(aliases) or set(actions) | set(aliases) != set(ACTIONS):
                raise ValueError("Every action needs a clip or explicit fallback")
            for action, clip in actions.items():
                if not isinstance(clip, dict) or set(clip) - {"file", "frames", "interval_ms", "loop"}:
                    raise ValueError("Invalid clip fields")
                frames, interval = clip.get("frames"), clip.get("interval_ms")
                if type(frames) is not int or not 1 <= frames <= 64:
                    raise ValueError("Invalid frame count")
                if type(interval) is not int or not 10 <= interval <= 1000:
                    raise ValueError("Invalid frame interval")
                file = clip.get("file", action)
                if not isinstance(file, str) or file not in ACTIONS + ("fly",):
                    raise ValueError("Unsupported source action")
                loop = clip.get("loop", [0, frames - 1])
                if not isinstance(loop, list) or len(loop) != 2 or any(type(i) is not int for i in loop) or not 0 <= loop[0] <= loop[1] < frames:
                    raise ValueError("Invalid clip loop")
            if any(not isinstance(target, str) or target not in actions for target in aliases.values()):
                raise ValueError("Fallback must reference an existing clip, without cycles")
            for context in ("training", "battle"):
                allowed = stage.get(context + "_actions", [])
                if not isinstance(allowed, list) or len(allowed) != len(set(allowed)) or any(a not in actions for a in allowed):
                    raise ValueError("Invalid context actions")
            if "idle" not in stage.get("training_actions", []):
                raise ValueError("Training needs idle fallback")
            for action, values in stage.get("motion_overrides", {}).items():
                if action not in ACTIONS or not isinstance(values, list) or len(values) != 2 or any(type(i) is not int for i in values) or not 1 <= values[0] <= 64 or not 10 <= values[1] <= 1000:
                    raise ValueError("Invalid legacy motion override")
            for context in CONTEXTS:
                for action in ACTIONS:
                    clip = self.clip(role, action, context)
                    _path(clip["path"])
                    _path(clip["atlas"])
                    identity = (clip["atlas"], clip["frames"], clip["canvas"])
                    previous = outputs.setdefault(clip["path"], identity)
                    if previous != identity:
                        raise ValueError("Conflicting output resource: " + clip["path"])

    def stage(self, role):
        if role not in ROLES:
            raise ValueError("Unknown stage role")
        return self.document["stages"][role]

    def name(self, role, context="full"):
        return self.stage(role)[{"full": "name", "short": "short_name", "battle": "battle_name"}[context]]

    def clip(self, role, action, context="home"):
        stage = self.stage(role)
        if action not in ACTIONS or context not in CONTEXTS:
            raise ValueError("Unknown content action/context")
        resolved = stage.get("aliases", {}).get(action, action)
        if context in ("training", "battle"):
            allowed = stage.get(context + "_actions", [])
            resolved = resolved if resolved in allowed else "idle"
        if context == "exploration":
            resolved = "walk" if action == "walk" and role != "egg" else "idle"
        source = stage["actions"][resolved]
        file = source.get("file", resolved)
        atlas = "/%s/%s_%s_atlas.bmp" % (stage["atlas_root"], stage["stem"], file)
        frames, interval = source["frames"], source["interval_ms"]
        canvas = 88
        path = "%s/%s_%s.vpa" % (stage["home_root"], stage["stem"], file)
        if context == "training":
            path = "%s_%s.vpa" % (stage["training_prefix"], resolved)
            interval, canvas = (120 if resolved == "idle" else 90), 68
        elif context == "battle" and stage.get("battle_actions"):
            path = "%s_%s.vpa" % (stage["battle_prefix"], file)
            canvas = 68
        elif context == "exploration":
            canvas = 44 if resolved == "walk" else 48
            interval = 70 if resolved == "walk" else 85
            path = "%s_%s%d.vpa" % (stage["exploration_prefix"], resolved, canvas)
        return {"path": path, "atlas": atlas, "frames": frames, "interval_ms": interval,
                "loop": source.get("loop", [0, frames - 1]), "canvas": canvas}


def builtin_definition():
    from core.content_builtin import BUILTIN_CONTENT
    return _builtin(BUILTIN_CONTENT)


_builtin_instance = None


def _builtin(document):
    global _builtin_instance
    if _builtin_instance is None:
        _builtin_instance = PetDefinition(document)
    return _builtin_instance
