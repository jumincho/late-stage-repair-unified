# UNIFY-FULL Synthesis

## Main Read

- Qwen-7B overall best shared-action policy: `FORMAT_TUNED_RULE (0.706)`, with `POOLED_RULE_BEST` exactly tied.
- Mistral-7B overall best shared-action policy: `FORMAT_TUNED_RULE (0.432)`, with `POOLED_RULE_BEST` close behind.
- Qwen-7B math-vs-format pooled gaps: `math +0.0000`, `format +0.0000`.
- Mistral-7B math-vs-format pooled gaps: `math +0.0000`, `format +0.0000`.
- Qwen-14B overall best shared-action policy: `FORMAT_TUNED_RULE (0.773)`, with `POOLED_RULE_BEST` exactly tied.

## Pairwise Lock Checks

- Qwen-7B pooled-vs-rewrite overall: `+0.2176 [+0.1799, +0.2578]`
- Mistral-7B pooled-vs-rewrite overall: `+0.1694 [+0.1300, +0.2115]`
- Qwen-14B pooled-vs-rewrite overall: `+0.1084 [+0.0694, +0.1458]`

## Transfer Asymmetry

| model_name                         | direction             | scope          | policy            |   utility |   intervention_rate |   rewrite_delta |
|:-----------------------------------|:----------------------|:---------------|:------------------|----------:|--------------------:|----------------:|
| Qwen/Qwen2.5-7B-Instruct           | math_to_format        | format:overall | MATH_TUNED_RULE   |  0.541322 |            0.53719  |       0.0409979 |
| Qwen/Qwen2.5-7B-Instruct           | format_to_math        | math:overall   | FORMAT_TUNED_RULE |  0.77381  |            0.699405 |       0.294326  |
| Qwen/Qwen2.5-7B-Instruct           | pooled_to_both_math   | math:overall   | POOLED_RULE_BEST  |  0.77381  |            0.699405 |       0.294326  |
| Qwen/Qwen2.5-7B-Instruct           | pooled_to_both_format | format:overall | POOLED_RULE_BEST  |  0.61157  |            0.53719  |       0.112043  |
| mistralai/Mistral-7B-Instruct-v0.3 | math_to_format        | format:overall | MATH_TUNED_RULE   |  0.460581 |            0.759336 |       0.0830809 |
| mistralai/Mistral-7B-Instruct-v0.3 | format_to_math        | math:overall   | FORMAT_TUNED_RULE |  0.399061 |            0.929577 |       0.277324  |
| mistralai/Mistral-7B-Instruct-v0.3 | pooled_to_both_math   | math:overall   | POOLED_RULE_BEST  |  0.389671 |            0.929577 |       0.267568  |
| mistralai/Mistral-7B-Instruct-v0.3 | pooled_to_both_format | format:overall | POOLED_RULE_BEST  |  0.460581 |            0.759336 |       0.0832593 |
| Qwen/Qwen2.5-14B-Instruct          | math_to_format        | format:overall | MATH_TUNED_RULE   |  0.62931  |            0.443966 |       0.0306121 |
| Qwen/Qwen2.5-14B-Instruct          | format_to_math        | math:overall   | FORMAT_TUNED_RULE |  0.87     |            0.655    |       0.130627  |
| Qwen/Qwen2.5-14B-Instruct          | pooled_to_both_math   | math:overall   | POOLED_RULE_BEST  |  0.87     |            0.655    |       0.130627  |
| Qwen/Qwen2.5-14B-Instruct          | pooled_to_both_format | format:overall | POOLED_RULE_BEST  |  0.689655 |            0.443966 |       0.0910668 |

## Shared Failure-Bucket Alignment

| module   | shared_failure_bucket         |   n |
|:---------|:------------------------------|----:|
| format   | binding_or_alignment          | 141 |
| format   | direct_correct                | 299 |
| format   | final_requirement_realization | 165 |
| format   | structural_or_broad           | 110 |
| math     | binding_or_alignment          | 340 |
| math     | direct_correct                | 185 |
| math     | executable_relation           | 102 |
| math     | final_requirement_realization |  66 |
| math     | structural_or_broad           |  56 |