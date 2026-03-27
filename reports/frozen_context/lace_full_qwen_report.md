# LACE-FULL Qwen Report

## Setup

- Holdout split: `train=437`, `eval=244`.
- Best simple family on the frozen Qwen train split: `SIMPLE_THRESHOLDED_TREE`.

## Full-scale lock read

- Screened IFEval `SIMPLE_BEST_GATE - ALWAYS_FULL_REWRITE`: `+0.1556 [+0.0922, +0.2270]`.
- IFBench `SIMPLE_BEST_GATE - ALWAYS_FULL_REWRITE`: `+0.1452 [+0.0680, +0.2330]`.
- Screened IFEval `LEARNED_GATE - ALWAYS_FULL_REWRITE`: `+0.0281 [+0.0000, +0.0638]`.
- IFBench `LEARNED_GATE - ALWAYS_FULL_REWRITE`: `+0.1452 [+0.0680, +0.2330]`.

## Overall interpretation

- Overall Qwen utility: `SIMPLE_BEST_GATE = 0.623`, `LEARNED_GATE = 0.549`, `HEURISTIC_GATE = 0.619`, `ALWAYS_FULL_REWRITE = 0.471`.
- The reviewer-facing question on the primary family is no longer whether output-constraint support exists, but whether the simpler gate family stays close enough to the learned gate at full scale.