# LACE-FULL Synthesis

## Cross-family rule comparison

- Qwen overall: `SIMPLE_BEST_GATE = 0.623`, `LEARNED_GATE = 0.549`, `ALWAYS_FULL_REWRITE = 0.471`.
- Mistral overall: `SIMPLE_BEST_GATE_TRANSFER = 0.459`, `LEARNED_GATE_TRANSFER = 0.402`, `ALWAYS_FULL_REWRITE = 0.365`.
- Qwen-14B overall: `SIMPLE_BEST_GATE = 0.664`, `LEARNED_GATE = 0.635`, `ALWAYS_FULL_REWRITE = 0.553`.

## Positioning read

- Output-constraint tasks now have full-scale primary-family evidence and a full non-Qwen rerun on the same validator family.
- The simplest portable gate family remains the cleanest portability story if it stays above rewrite and close to the learned gate on both surfaces.
- IFBench is the harder boundary surface; positive direction there matters more than absolute parity with screened IFEval.
- The optional Qwen-14B scale read now directly mirrors the math-side scale question instead of leaving it open.

## Final synthesis

- Full screened `IFEval` is now locked strongly enough to act as second-domain evidence, not just appendix support:
  - `Qwen-7B`: `SIMPLE_BEST_GATE - ALWAYS_FULL_REWRITE = +0.1556 [+0.0922, +0.2270]`
  - `Mistral-7B`: `SIMPLE_BEST_GATE_TRANSFER - ALWAYS_FULL_REWRITE = +0.1130 [+0.0426, +0.1773]`
  - `Qwen-14B`: `SIMPLE_BEST_GATE - ALWAYS_FULL_REWRITE = +0.1561 [+0.0922, +0.2199]`
- Full `IFBench` remains the harder validator boundary:
  - `Qwen-7B` stays clearly positive at `+0.1452 [+0.0680, +0.2330]`
  - `Mistral-7B` stays directionally positive at `+0.0686 [+0.0000, +0.1359]`
  - `Qwen-14B` compresses to `+0.0472 [-0.0291, +0.1262]`
- The strongest overall reviewer-facing read is therefore:
  - output-constraint tasks deserve co-main placement with math
  - the cleanest portable story is still the simple rule family, not learned transfer
  - stronger scale preserves the easy-validator win and softens the hard-boundary gain
