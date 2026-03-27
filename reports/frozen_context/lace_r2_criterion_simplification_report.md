# LACE-R2 Criterion Simplification Report

## Goal

- Distill the current online intervention criterion into a small, interpretable rule family.
- Keep the online action space frozen.
- Measure how much utility is lost, if any, relative to `LEARNED_GATE`.

## Math

- `LEARNED_GATE`: utility `0.759`, intervention `0.735`
- `HEURISTIC_GATE`: utility `0.743`, intervention `1.000`
- `SIMPLE_2FEATURE_GATE`: utility `0.753`, intervention `0.998`
- `SIMPLE_3FEATURE_GATE`: utility `0.759`, intervention `0.825`
- `SIMPLE_THRESHOLDED_TREE`: utility `0.733`, intervention `0.998`
- best simple by utility: `SIMPLE_3FEATURE_GATE`
- smallest viable simple rule: `SIMPLE_2FEATURE_GATE`
- rule: if max(target_score, role_score) < 3: NO_INTERVENTION; elif checker_target_score >= 1: LOCAL_PATCH; else: GLOBAL_RESTART

## Format

- `LEARNED_GATE`: utility `0.620`, intervention `0.539`
- `HEURISTIC_GATE`: utility `0.634`, intervention `0.542`
- `SIMPLE_2FEATURE_GATE`: utility `0.634`, intervention `0.542`
- `SIMPLE_3FEATURE_GATE`: utility `0.634`, intervention `0.542`
- `SIMPLE_THRESHOLDED_TREE`: utility `0.640`, intervention `0.542`
- best simple by utility: `SIMPLE_THRESHOLDED_TREE`
- smallest viable simple rule: `SIMPLE_2FEATURE_GATE`
- rule: if direct validator passes: NO_INTERVENTION; elif failed_instruction_count <= 2: SOLVE_THEN_FORMAT; else: GLOBAL_REWRITE

## Planning boundary

- `LEARNED_GATE`: utility `0.050`, intervention `0.455`
- `SIMPLE_2FEATURE_GATE`: utility `0.033`, intervention `1.000`
- `SIMPLE_3FEATURE_GATE`: utility `0.033`, intervention `1.000`
- `SIMPLE_THRESHOLDED_TREE`: utility `0.033`, intervention `1.000`
- smallest viable simple rule: `SIMPLE_2FEATURE_GATE`
- rule: if direct plan is valid: NO_INTERVENTION; elif prefix_valid = 1 and failure_position_ratio >= 0.25: LOCAL_SUFFIX_REPAIR; else: GLOBAL_RESTART

## Interpretation

- The main simplification question is whether a very small rule can stay close to `LEARNED_GATE` while remaining better than naive restart/rewrite.
- On math, the chosen simple rule is `SIMPLE_2FEATURE_GATE` with utility gap `0.005` relative to `LEARNED_GATE`.
- On format, the chosen simple rule is `SIMPLE_2FEATURE_GATE` with utility gap `-0.015` relative to `LEARNED_GATE`.
- Planning remains a boundary surface: simplification is still worth logging there, but it should not drive the broader claim.