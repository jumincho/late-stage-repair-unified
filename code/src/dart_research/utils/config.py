from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml


_ENV_PATTERN = re.compile(r"\$\{([^:}]+)(?::-(.*?))?\}")


def _expand_env(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _expand_env(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_expand_env(item) for item in value]
    if not isinstance(value, str):
        return value

    def replacer(match: re.Match[str]) -> str:
        var_name = match.group(1)
        default = match.group(2) or ""
        return os.getenv(var_name, default)

    return _ENV_PATTERN.sub(replacer, value)


def load_yaml(path: Path) -> dict[str, Any]:
    """Load YAML config with simple ${ENV:-default} expansion."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return _expand_env(data)
