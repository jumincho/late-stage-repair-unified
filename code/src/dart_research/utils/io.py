from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import orjson


def ensure_dir(path: Path) -> Path:
    """Create a directory if needed and return it."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_text(path: Path) -> str:
    """Read a UTF-8 text file."""
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    """Write a UTF-8 text file, creating parent directories."""
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8")


def read_json(path: Path) -> Any:
    """Read a JSON file."""
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    """Write a pretty JSON file."""
    ensure_dir(path.parent)
    path.write_bytes(orjson.dumps(payload, option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS))


def append_jsonl(path: Path, payload: Any) -> None:
    """Append a JSON line."""
    ensure_dir(path.parent)
    with path.open("ab", buffering=0) as handle:
        handle.write(orjson.dumps(payload))
        handle.write(b"\n")
