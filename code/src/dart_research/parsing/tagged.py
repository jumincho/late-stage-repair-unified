from __future__ import annotations

import re
from typing import Iterable


TAG_PATTERN = re.compile(r"<(?P<tag>[a-zA-Z0-9_]+)>(?P<value>.*?)</(?P=tag)>", re.DOTALL)


def extract_tagged_fields(text: str) -> dict[str, str]:
    """Extract simple XML-like tagged fields from model output."""
    fields: dict[str, str] = {}
    for match in TAG_PATTERN.finditer(text):
        tag = match.group("tag").strip().lower()
        value = match.group("value").strip()
        if tag and tag not in fields:
            fields[tag] = value
    return fields


def require_tags(text: str, required: Iterable[str]) -> dict[str, str]:
    """Extract tags and raise if any required tag is missing."""
    fields = extract_tagged_fields(text)
    missing = [tag for tag in required if not fields.get(tag)]
    if missing:
        raise ValueError(f"Missing required tags: {', '.join(missing)}")
    return fields


def parse_int_tag(text: str, tag: str, minimum: int, maximum: int) -> int:
    """Parse a bounded integer from a tagged field."""
    fields = require_tags(text, [tag])
    raw = fields[tag]
    match = re.search(r"-?\d+", raw)
    if not match:
        raise ValueError(f"Unable to parse integer for tag {tag}")
    value = int(match.group(0))
    return max(minimum, min(maximum, value))
