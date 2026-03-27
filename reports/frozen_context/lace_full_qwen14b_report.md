# LACE-FULL Qwen-14B Report

## Setup

- Holdout split: `train=437`, `eval=244`.
- Best simple family on the frozen Qwen-14B train split: `SIMPLE_THRESHOLDED_TREE`.

## Scale read

- Screened IFEval `SIMPLE_BEST_GATE - ALWAYS_FULL_REWRITE`: `+0.1561 [+0.0922, +0.2199]`.
- IFBench `SIMPLE_BEST_GATE - ALWAYS_FULL_REWRITE`: `+0.0472 [-0.0291, +0.1262]`.
- Screened IFEval `LEARNED_GATE - ALWAYS_FULL_REWRITE`: `+0.1419 [+0.0851, +0.2057]`.
- IFBench `LEARNED_GATE - ALWAYS_FULL_REWRITE`: `-0.0010 [-0.0485, +0.0485]`.

## Scale interpretation

- Overall Qwen-14B utility: `SIMPLE_BEST_GATE = 0.664`, `LEARNED_GATE = 0.635`, `HEURISTIC_GATE = 0.660`, `ALWAYS_FULL_REWRITE = 0.553`.
- The scale question is whether the format-side local-repair advantage remains intact or compresses toward stronger direct-formatting baselines.