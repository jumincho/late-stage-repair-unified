from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import orjson

from dart_research.utils.io import ensure_dir, read_json, write_json


class DiskCache:
    """Content-addressed disk cache for requests and responses."""

    def __init__(self, root: Path):
        self.root = ensure_dir(root)

    def _key(self, payload: dict[str, Any]) -> str:
        blob = orjson.dumps(payload, option=orjson.OPT_SORT_KEYS)
        return hashlib.sha256(blob).hexdigest()

    def path_for(self, payload: dict[str, Any]) -> Path:
        key = self._key(payload)
        return self.root / f"{key}.json"

    def get(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        path = self.path_for(payload)
        if not path.exists():
            return None
        return read_json(path)

    def set(self, payload: dict[str, Any], response: dict[str, Any]) -> Path:
        path = self.path_for(payload)
        write_json(path, response)
        return path
