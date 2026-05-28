"""Prompt bank for OSCAR (schema probe + constrained compile, math domain).

Loads the two `.txt` prompts under `prompts/oscar/`:

- `schema_probe` — ask the model to emit a structured operator schema,
- `constrained_compile` — re-ask the model with explicit allowed-op
  constraints so it tightens up the schema before compilation.

The version bundle is merged with the TIER prompt versions because OSCAR
sits between TIER (probe-level) and the higher rounds (ATLAS / CASS).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dart_research.tier.prompts import TIERPromptBank
from dart_research.utils.prompts import PromptTemplate, load_prompt


@dataclass(slots=True)
class OSCARPromptBank:
    schema_probe: PromptTemplate
    constrained_compile: PromptTemplate

    @classmethod
    def load(cls, repo_root: Path) -> "OSCARPromptBank":
        root = repo_root / "prompts" / "oscar"
        return cls(
            schema_probe=load_prompt(root / "schema_probe_v1.txt"),
            constrained_compile=load_prompt(root / "constrained_compile_v1.txt"),
        )

    def version_bundle_with_tier(self, *, tier_bundle: dict[str, str]) -> dict[str, str]:
        bundle = dict(tier_bundle)
        bundle.update(
            {
                "oscar_schema_probe": self.schema_probe.version,
                "oscar_constrained_compile": self.constrained_compile.version,
            }
        )
        return bundle
