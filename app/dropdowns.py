import os
import yaml

_yaml_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "dropdowns.yaml")
_cache: dict | None = None


def _load():
    global _cache
    with open(_yaml_path, "r", encoding="utf-8") as f:
        _cache = yaml.safe_load(f)


def get_options(key: str) -> list[str]:
    global _cache
    if _cache is None:
        _load()
    return list(_cache.get(key, []))
