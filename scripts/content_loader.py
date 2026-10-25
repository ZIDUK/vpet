"""Host-side definition binding; active content is immutable for a render session."""
from functools import lru_cache
from pathlib import Path

from core.content import builtin_definition
from scripts.content_definitions import load_definition


@lru_cache(maxsize=8)
def definition_for(build_dir):
    source = Path(build_dir) / "content.json"
    return load_definition(source) if source.is_file() else builtin_definition()


def clear_definitions():
    definition_for.cache_clear()
