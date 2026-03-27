# LACE-FULL Mistral Report

## Setup

- Holdout split: `train=437`, `eval=244`.
- Qwen-transferred simple family: `SIMPLE_THRESHOLDED_TREE`.
- Mistral within-tuned simple family: `SIMPLE_THRESHOLDED_TREE`.

## Full cross-family read

- Screened IFEval `SIMPLE_BEST_GATE_TRANSFER - ALWAYS_FULL_REWRITE`: `+0.1130 [+0.0426, +0.1773]`.
- IFBench `SIMPLE_BEST_GATE_TRANSFER - ALWAYS_FULL_REWRITE`: `+0.0686 [+0.0000, +0.1359]`.
- Screened IFEval `LEARNED_GATE_TRANSFER - ALWAYS_FULL_REWRITE`: `+0.0212 [-0.0142, +0.0567]`.
- IFBench `LEARNED_GATE_TRANSFER - ALWAYS_FULL_REWRITE`: `+0.0588 [-0.0097, +0.1262]`.

## Portability interpretation

- Overall Mistral utility: `SIMPLE_BEST_GATE_TRANSFER = 0.459`, `LEARNED_GATE_TRANSFER = 0.402`, `LEARNED_GATE_WITHIN = 0.385`, `ALWAYS_FULL_REWRITE = 0.365`.
- The portability question is whether a small transferred rule remains competitive with learned transfer and still clears naive rewrite on both surfaces.