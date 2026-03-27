from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class PromptTemplate:
    name: str
    version: str
    text: str

    def render(self, **kwargs: str) -> str:
        rendered = self.text
        for key, value in kwargs.items():
            rendered = rendered.replace(f"{{{key}}}", value)
        return rendered


def load_prompt(path: Path) -> PromptTemplate:
    """Load a prompt template and parse its version header."""
    raw = path.read_text(encoding="utf-8")
    lines = raw.splitlines()
    if not lines or not lines[0].startswith("VERSION:"):
        raise ValueError(f"Prompt file missing VERSION header: {path}")
    version = lines[0].split(":", 1)[1].strip()
    body = "\n".join(lines[2:]) if len(lines) > 2 else ""
    return PromptTemplate(name=path.stem, version=version, text=body)
