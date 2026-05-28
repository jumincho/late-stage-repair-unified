"""Tolerant JSON extraction from messy LLM output.

LLM responses regularly carry the JSON we want surrounded by prose, with
trailing commas, or with single-token key/value corruptions. This module
provides:

- `_pre_fix_common_json_issues` — patch the most common key-quoting mistake,
- `extract_first_json` — return the first JSON object/array in a string,
  falling back through `json.loads`, the `json_repair` library, and a
  regex-anchored brace scanner.

Used by every client that has to parse structured tool output and by
`last_pack.formatting` when it loads instruction-following inputs.
"""

from __future__ import annotations

import json
import re
from typing import Any

from json_repair import repair_json


def _pre_fix_common_json_issues(text: str) -> str:
    """Fix frequent single-token JSON corruptions before heavier repair."""
    return re.sub(r'"([A-Za-z_][A-Za-z0-9_]*)\s+"([^"]+)"', r'"\1": "\2"', text)


def extract_first_json(text: str) -> Any:
    """Extract the first JSON object or array from model text output."""
    text = _pre_fix_common_json_issues(text.strip())
    if not text:
        raise ValueError("Empty model output")

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            return json.loads(repair_json(text))
        except json.JSONDecodeError:
            pass

    match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in output")
    candidate = match.group(1)
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return json.loads(repair_json(candidate))
