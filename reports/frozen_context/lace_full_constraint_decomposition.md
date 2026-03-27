# LACE-FULL Constraint Decomposition

## Main read

- Constraint categories are coarse but reproducible prompt-level buckets, not post-hoc manual re-labeling.
- They are intended to show where local repair is most friendly, not to redefine the benchmark.

## Category highlights

- `Qwen/Qwen2.5-14B-Instruct` / `ifbench` / `json_or_structural_formatting`: best policy `HEURISTIC_GATE` at utility `0.654` over `n=26`.
- `Qwen/Qwen2.5-14B-Instruct` / `ifbench` / `keyword_inclusion`: best policy `LEARNED_GATE` at utility `0.400` over `n=5`.
- `Qwen/Qwen2.5-14B-Instruct` / `ifbench` / `list_length_or_count`: best policy `ALWAYS_FULL_REWRITE` at utility `0.000` over `n=1`.
- `Qwen/Qwen2.5-14B-Instruct` / `ifbench` / `multi_part_instructions`: best policy `HEURISTIC_GATE` at utility `0.250` over `n=16`.
- `Qwen/Qwen2.5-14B-Instruct` / `ifbench` / `ordering_or_position`: best policy `ALWAYS_SOLVE_THEN_FORMAT` at utility `0.261` over `n=23`.
- `Qwen/Qwen2.5-14B-Instruct` / `ifbench` / `other_constraint`: best policy `HEURISTIC_GATE` at utility `0.367` over `n=30`.
- `Qwen/Qwen2.5-14B-Instruct` / `ifbench` / `punctuation_comma`: best policy `ALWAYS_FULL_REWRITE` at utility `0.000` over `n=2`.
- `Qwen/Qwen2.5-14B-Instruct` / `ifeval_screened` / `json_or_structural_formatting`: best policy `HEURISTIC_GATE` at utility `0.889` over `n=18`.
- `Qwen/Qwen2.5-14B-Instruct` / `ifeval_screened` / `keyword_inclusion`: best policy `ALWAYS_SOLVE_THEN_FORMAT` at utility `0.938` over `n=16`.
- `Qwen/Qwen2.5-14B-Instruct` / `ifeval_screened` / `list_length_or_count`: best policy `HEURISTIC_GATE` at utility `0.867` over `n=15`.
- `Qwen/Qwen2.5-14B-Instruct` / `ifeval_screened` / `multi_part_instructions`: best policy `HEURISTIC_GATE` at utility `0.786` over `n=56`.
- `Qwen/Qwen2.5-14B-Instruct` / `ifeval_screened` / `ordering_or_position`: best policy `ALWAYS_SOLVE_THEN_FORMAT` at utility `0.857` over `n=7`.
- `Qwen/Qwen2.5-14B-Instruct` / `ifeval_screened` / `other_constraint`: best policy `HEURISTIC_GATE` at utility `0.960` over `n=25`.
- `Qwen/Qwen2.5-14B-Instruct` / `ifeval_screened` / `punctuation_comma`: best policy `ALWAYS_FULL_REWRITE` at utility `1.000` over `n=4`.
- `Qwen/Qwen2.5-7B-Instruct` / `ifbench` / `json_or_structural_formatting`: best policy `HEURISTIC_GATE` at utility `0.692` over `n=26`.
- `Qwen/Qwen2.5-7B-Instruct` / `ifbench` / `keyword_inclusion`: best policy `LEARNED_GATE` at utility `0.200` over `n=5`.
- `Qwen/Qwen2.5-7B-Instruct` / `ifbench` / `list_length_or_count`: best policy `ALWAYS_FULL_REWRITE` at utility `0.000` over `n=1`.
- `Qwen/Qwen2.5-7B-Instruct` / `ifbench` / `multi_part_instructions`: best policy `ALWAYS_FULL_REWRITE` at utility `0.188` over `n=16`.
- `Qwen/Qwen2.5-7B-Instruct` / `ifbench` / `ordering_or_position`: best policy `HEURISTIC_GATE` at utility `0.348` over `n=23`.
- `Qwen/Qwen2.5-7B-Instruct` / `ifbench` / `other_constraint`: best policy `HEURISTIC_GATE` at utility `0.367` over `n=30`.
- `Qwen/Qwen2.5-7B-Instruct` / `ifbench` / `punctuation_comma`: best policy `ALWAYS_FULL_REWRITE` at utility `0.000` over `n=2`.
- `Qwen/Qwen2.5-7B-Instruct` / `ifeval_screened` / `json_or_structural_formatting`: best policy `ALWAYS_SOLVE_THEN_FORMAT` at utility `1.000` over `n=18`.
- `Qwen/Qwen2.5-7B-Instruct` / `ifeval_screened` / `keyword_inclusion`: best policy `HEURISTIC_GATE` at utility `0.938` over `n=16`.
- `Qwen/Qwen2.5-7B-Instruct` / `ifeval_screened` / `list_length_or_count`: best policy `HEURISTIC_GATE` at utility `0.800` over `n=15`.
- `Qwen/Qwen2.5-7B-Instruct` / `ifeval_screened` / `multi_part_instructions`: best policy `HEURISTIC_GATE` at utility `0.643` over `n=56`.
- `Qwen/Qwen2.5-7B-Instruct` / `ifeval_screened` / `ordering_or_position`: best policy `ALWAYS_SOLVE_THEN_FORMAT` at utility `0.714` over `n=7`.
- `Qwen/Qwen2.5-7B-Instruct` / `ifeval_screened` / `other_constraint`: best policy `HEURISTIC_GATE` at utility `0.880` over `n=25`.
- `Qwen/Qwen2.5-7B-Instruct` / `ifeval_screened` / `punctuation_comma`: best policy `ALWAYS_FULL_REWRITE` at utility `1.000` over `n=4`.
- `mistralai/Mistral-7B-Instruct-v0.3` / `ifbench` / `json_or_structural_formatting`: best policy `HEURISTIC_GATE` at utility `0.423` over `n=26`.
- `mistralai/Mistral-7B-Instruct-v0.3` / `ifbench` / `keyword_inclusion`: best policy `ALWAYS_FULL_REWRITE` at utility `0.200` over `n=5`.
- `mistralai/Mistral-7B-Instruct-v0.3` / `ifbench` / `list_length_or_count`: best policy `ALWAYS_FULL_REWRITE` at utility `0.000` over `n=1`.
- `mistralai/Mistral-7B-Instruct-v0.3` / `ifbench` / `multi_part_instructions`: best policy `ALWAYS_FULL_REWRITE` at utility `0.000` over `n=16`.
- `mistralai/Mistral-7B-Instruct-v0.3` / `ifbench` / `ordering_or_position`: best policy `HEURISTIC_GATE` at utility `0.261` over `n=23`.
- `mistralai/Mistral-7B-Instruct-v0.3` / `ifbench` / `other_constraint`: best policy `HEURISTIC_GATE` at utility `0.200` over `n=30`.
- `mistralai/Mistral-7B-Instruct-v0.3` / `ifbench` / `punctuation_comma`: best policy `ALWAYS_FULL_REWRITE` at utility `0.000` over `n=2`.
- `mistralai/Mistral-7B-Instruct-v0.3` / `ifeval_screened` / `json_or_structural_formatting`: best policy `HEURISTIC_GATE` at utility `0.833` over `n=18`.
- `mistralai/Mistral-7B-Instruct-v0.3` / `ifeval_screened` / `keyword_inclusion`: best policy `ALWAYS_FULL_REWRITE` at utility `0.812` over `n=16`.
- `mistralai/Mistral-7B-Instruct-v0.3` / `ifeval_screened` / `list_length_or_count`: best policy `HEURISTIC_GATE` at utility `0.667` over `n=15`.
- `mistralai/Mistral-7B-Instruct-v0.3` / `ifeval_screened` / `multi_part_instructions`: best policy `SIMPLE_BEST_GATE` at utility `0.464` over `n=56`.
- `mistralai/Mistral-7B-Instruct-v0.3` / `ifeval_screened` / `ordering_or_position`: best policy `ALWAYS_SOLVE_THEN_FORMAT` at utility `0.714` over `n=7`.
- `mistralai/Mistral-7B-Instruct-v0.3` / `ifeval_screened` / `other_constraint`: best policy `HEURISTIC_GATE` at utility `0.640` over `n=25`.
- `mistralai/Mistral-7B-Instruct-v0.3` / `ifeval_screened` / `punctuation_comma`: best policy `SIMPLE_BEST_GATE` at utility `0.750` over `n=4`.