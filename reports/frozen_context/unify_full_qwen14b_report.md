# UNIFY-FULL Qwen/Qwen2.5-14B-Instruct Report

## Setup

- Model: `Qwen/Qwen2.5-14B-Instruct`
- Pooled train/eval split: `train=849`, `eval=432`.
- Math-tuned simple family in the shared action space: `POOLED_SIMPLE_THRESHOLDED_TREE`.
- Format-tuned simple family in the shared action space: `POOLED_SIMPLE_3FEATURE`.
- Best pooled simple family: `POOLED_SIMPLE_3FEATURE`.

## Overall Read

- `NO_INTERVENTION`: utility `0.458`, intervention `0.000`, false-intervene `0.000`, missed-intervene `0.343`, latency `6.555s`
- `ALWAYS_REWRITE_OR_RESTART`: utility `0.664`, intervention `1.000`, false-intervene `0.773`, missed-intervene `0.000`, latency `6.944s`
- `MATH_TUNED_RULE`: utility `0.738`, intervention `0.542`, false-intervene `0.262`, missed-intervene `0.000`, latency `7.264s`
- `FORMAT_TUNED_RULE`: utility `0.773`, intervention `0.542`, false-intervene `0.227`, missed-intervene `0.000`, latency `7.642s`
- `POOLED_RULE_BEST`: utility `0.773`, intervention `0.542`, false-intervene `0.227`, missed-intervene `0.000`, latency `7.642s`
- `POOLED_LEARNED_GATE`: utility `0.743`, intervention `0.532`, false-intervene `0.248`, missed-intervene `0.000`, latency `7.420s`
- `ORACLE_POLICY`: utility `0.801`, intervention `0.542`, false-intervene `0.199`, missed-intervene `0.000`, latency `7.111s`

## Surface Checks

- math overall pooled-vs-rewrite: `+0.1306 [+0.0700, +0.1900]`
- format overall pooled-vs-rewrite: `+0.0911 [+0.0474, +0.1336]`
- cluster-hard pooled-vs-rewrite: `+0.1051 [+0.0323, +0.1774]`
- generic-hard pooled-vs-rewrite: `+0.1726 [+0.0658, +0.2763]`
- screened IFEval pooled-vs-rewrite: `+0.0898 [+0.0373, +0.1493]`
- IFBench pooled-vs-rewrite: `+0.0912 [+0.0306, +0.1633]`

## Domain-Specific vs Pooled Gap

| model_name                | module   | domain_policy     | pooled_policy    |   domain_utility |   pooled_utility |   utility_gap |
|:--------------------------|:---------|:------------------|:-----------------|-----------------:|-----------------:|--------------:|
| Qwen/Qwen2.5-14B-Instruct | math     | MATH_TUNED_RULE   | POOLED_RULE_BEST |         0.865    |         0.87     |         0.005 |
| Qwen/Qwen2.5-14B-Instruct | format   | FORMAT_TUNED_RULE | POOLED_RULE_BEST |         0.689655 |         0.689655 |         0     |

## Transfer Asymmetry

| model_name                | direction             | scope          | policy            |   utility |   intervention_rate |   rewrite_delta |
|:--------------------------|:----------------------|:---------------|:------------------|----------:|--------------------:|----------------:|
| Qwen/Qwen2.5-14B-Instruct | math_to_format        | format:overall | MATH_TUNED_RULE   |  0.62931  |            0.443966 |       0.0306121 |
| Qwen/Qwen2.5-14B-Instruct | format_to_math        | math:overall   | FORMAT_TUNED_RULE |  0.87     |            0.655    |       0.130627  |
| Qwen/Qwen2.5-14B-Instruct | pooled_to_both_math   | math:overall   | POOLED_RULE_BEST  |  0.87     |            0.655    |       0.130627  |
| Qwen/Qwen2.5-14B-Instruct | pooled_to_both_format | format:overall | POOLED_RULE_BEST  |  0.689655 |            0.443966 |       0.0910668 |

## Pairwise Table

| model_name                | scope                     | module   | surface_name         | base_policy               | alt_policy          |   n |   base_accuracy |   alt_accuracy |     delta |      ci_low |   ci_high |   mcnemar_p |   direction_favorable |
|:--------------------------|:--------------------------|:---------|:---------------------|:--------------------------|:--------------------|----:|----------------:|---------------:|----------:|------------:|----------:|------------:|----------------------:|
| Qwen/Qwen2.5-14B-Instruct | overall                   | pooled   | overall              | ALWAYS_REWRITE_OR_RESTART | MATH_TUNED_RULE     | 432 |        0.664352 |       0.738426 | 0.0738449 |  0.0416667  | 0.106481  | 9.06327e-06 |                     1 |
| Qwen/Qwen2.5-14B-Instruct | overall                   | pooled   | overall              | ALWAYS_REWRITE_OR_RESTART | FORMAT_TUNED_RULE   | 432 |        0.664352 |       0.773148 | 0.108374  |  0.0694444  | 0.145833  | 1.34777e-08 |                     1 |
| Qwen/Qwen2.5-14B-Instruct | overall                   | pooled   | overall              | ALWAYS_REWRITE_OR_RESTART | POOLED_RULE_BEST    | 432 |        0.664352 |       0.773148 | 0.108374  |  0.0694444  | 0.145833  | 1.34777e-08 |                     1 |
| Qwen/Qwen2.5-14B-Instruct | overall                   | pooled   | overall              | ALWAYS_REWRITE_OR_RESTART | POOLED_LEARNED_GATE | 432 |        0.664352 |       0.743056 | 0.078081  |  0.0462963  | 0.111111  | 1.16356e-06 |                     1 |
| Qwen/Qwen2.5-14B-Instruct | overall                   | pooled   | overall              | NO_INTERVENTION           | MATH_TUNED_RULE     | 432 |        0.458333 |       0.738426 | 0.279569  |  0.238426   | 0.321759  | 7.52316e-37 |                     1 |
| Qwen/Qwen2.5-14B-Instruct | overall                   | pooled   | overall              | NO_INTERVENTION           | FORMAT_TUNED_RULE   | 432 |        0.458333 |       0.773148 | 0.314098  |  0.268519   | 0.358796  | 2.29589e-41 |                     1 |
| Qwen/Qwen2.5-14B-Instruct | overall                   | pooled   | overall              | NO_INTERVENTION           | POOLED_RULE_BEST    | 432 |        0.458333 |       0.773148 | 0.314098  |  0.268519   | 0.358796  | 2.29589e-41 |                     1 |
| Qwen/Qwen2.5-14B-Instruct | overall                   | pooled   | overall              | NO_INTERVENTION           | POOLED_LEARNED_GATE | 432 |        0.458333 |       0.743056 | 0.283806  |  0.240741   | 0.326389  | 1.88079e-37 |                     1 |
| Qwen/Qwen2.5-14B-Instruct | format:overall            | format   | overall              | ALWAYS_REWRITE_OR_RESTART | MATH_TUNED_RULE     | 232 |        0.599138 |       0.62931  | 0.0306121 |  0.00431034 | 0.0603448 | 0.0654297   |                     1 |
| Qwen/Qwen2.5-14B-Instruct | format:overall            | format   | overall              | ALWAYS_REWRITE_OR_RESTART | FORMAT_TUNED_RULE   | 232 |        0.599138 |       0.689655 | 0.0910668 |  0.0474138  | 0.133621  | 0.000103716 |                     1 |
| Qwen/Qwen2.5-14B-Instruct | format:overall            | format   | overall              | ALWAYS_REWRITE_OR_RESTART | POOLED_RULE_BEST    | 232 |        0.599138 |       0.689655 | 0.0910668 |  0.0474138  | 0.133621  | 0.000103716 |                     1 |
| Qwen/Qwen2.5-14B-Instruct | format:overall            | format   | overall              | ALWAYS_REWRITE_OR_RESTART | POOLED_LEARNED_GATE | 232 |        0.599138 |       0.689655 | 0.0910668 |  0.0474138  | 0.133621  | 0.000103716 |                     1 |
| Qwen/Qwen2.5-14B-Instruct | format:overall            | format   | overall              | NO_INTERVENTION           | MATH_TUNED_RULE     | 232 |        0.556034 |       0.62931  | 0.0740129 |  0.0431034  | 0.107759  | 1.52588e-05 |                     1 |
| Qwen/Qwen2.5-14B-Instruct | format:overall            | format   | overall              | NO_INTERVENTION           | FORMAT_TUNED_RULE   | 232 |        0.556034 |       0.689655 | 0.134468  |  0.0905172  | 0.176724  | 9.31323e-10 |                     1 |
| Qwen/Qwen2.5-14B-Instruct | format:overall            | format   | overall              | NO_INTERVENTION           | POOLED_RULE_BEST    | 232 |        0.556034 |       0.689655 | 0.134468  |  0.0905172  | 0.176724  | 9.31323e-10 |                     1 |
| Qwen/Qwen2.5-14B-Instruct | format:overall            | format   | overall              | NO_INTERVENTION           | POOLED_LEARNED_GATE | 232 |        0.556034 |       0.689655 | 0.134468  |  0.0905172  | 0.176724  | 9.31323e-10 |                     1 |
| Qwen/Qwen2.5-14B-Instruct | format:ifbench            | format   | ifbench              | ALWAYS_REWRITE_OR_RESTART | MATH_TUNED_RULE     |  98 |        0.367347 |       0.367347 | 0         |  0          | 0         | 1           |                     0 |
| Qwen/Qwen2.5-14B-Instruct | format:ifbench            | format   | ifbench              | ALWAYS_REWRITE_OR_RESTART | FORMAT_TUNED_RULE   |  98 |        0.367347 |       0.459184 | 0.0912296 |  0.0306122  | 0.163265  | 0.0224609   |                     1 |
| Qwen/Qwen2.5-14B-Instruct | format:ifbench            | format   | ifbench              | ALWAYS_REWRITE_OR_RESTART | POOLED_RULE_BEST    |  98 |        0.367347 |       0.459184 | 0.0912296 |  0.0306122  | 0.163265  | 0.0224609   |                     1 |
| Qwen/Qwen2.5-14B-Instruct | format:ifbench            | format   | ifbench              | ALWAYS_REWRITE_OR_RESTART | POOLED_LEARNED_GATE |  98 |        0.367347 |       0.459184 | 0.0912296 |  0.0306122  | 0.163265  | 0.0224609   |                     1 |
| Qwen/Qwen2.5-14B-Instruct | format:ifbench            | format   | ifbench              | NO_INTERVENTION           | MATH_TUNED_RULE     |  98 |        0.316327 |       0.367347 | 0.0517653 |  0.0102041  | 0.102041  | 0.0625      |                     1 |
| Qwen/Qwen2.5-14B-Instruct | format:ifbench            | format   | ifbench              | NO_INTERVENTION           | FORMAT_TUNED_RULE   |  98 |        0.316327 |       0.459184 | 0.142995  |  0.0816327  | 0.214286  | 0.00012207  |                     1 |
| Qwen/Qwen2.5-14B-Instruct | format:ifbench            | format   | ifbench              | NO_INTERVENTION           | POOLED_RULE_BEST    |  98 |        0.316327 |       0.459184 | 0.142995  |  0.0816327  | 0.214286  | 0.00012207  |                     1 |
| Qwen/Qwen2.5-14B-Instruct | format:ifbench            | format   | ifbench              | NO_INTERVENTION           | POOLED_LEARNED_GATE |  98 |        0.316327 |       0.459184 | 0.142995  |  0.0816327  | 0.214286  | 0.00012207  |                     1 |
| Qwen/Qwen2.5-14B-Instruct | format:ifeval_screened    | format   | ifeval_screened      | ALWAYS_REWRITE_OR_RESTART | MATH_TUNED_RULE     | 134 |        0.768657 |       0.820896 | 0.0526604 |  0.00746269 | 0.104478  | 0.0654297   |                     1 |
| Qwen/Qwen2.5-14B-Instruct | format:ifeval_screened    | format   | ifeval_screened      | ALWAYS_REWRITE_OR_RESTART | FORMAT_TUNED_RULE   | 134 |        0.768657 |       0.858209 | 0.0897985 |  0.0373134  | 0.149254  | 0.00418091  |                     1 |
| Qwen/Qwen2.5-14B-Instruct | format:ifeval_screened    | format   | ifeval_screened      | ALWAYS_REWRITE_OR_RESTART | POOLED_RULE_BEST    | 134 |        0.768657 |       0.858209 | 0.0897985 |  0.0373134  | 0.149254  | 0.00418091  |                     1 |
| Qwen/Qwen2.5-14B-Instruct | format:ifeval_screened    | format   | ifeval_screened      | ALWAYS_REWRITE_OR_RESTART | POOLED_LEARNED_GATE | 134 |        0.768657 |       0.858209 | 0.0897985 |  0.0373134  | 0.149254  | 0.00418091  |                     1 |
| Qwen/Qwen2.5-14B-Instruct | format:ifeval_screened    | format   | ifeval_screened      | NO_INTERVENTION           | MATH_TUNED_RULE     | 134 |        0.731343 |       0.820896 | 0.0897463 |  0.0447761  | 0.141791  | 0.000488281 |                     1 |
| Qwen/Qwen2.5-14B-Instruct | format:ifeval_screened    | format   | ifeval_screened      | NO_INTERVENTION           | FORMAT_TUNED_RULE   | 134 |        0.731343 |       0.858209 | 0.126884  |  0.0746269  | 0.186567  | 1.52588e-05 |                     1 |
| Qwen/Qwen2.5-14B-Instruct | format:ifeval_screened    | format   | ifeval_screened      | NO_INTERVENTION           | POOLED_RULE_BEST    | 134 |        0.731343 |       0.858209 | 0.126884  |  0.0746269  | 0.186567  | 1.52588e-05 |                     1 |
| Qwen/Qwen2.5-14B-Instruct | format:ifeval_screened    | format   | ifeval_screened      | NO_INTERVENTION           | POOLED_LEARNED_GATE | 134 |        0.731343 |       0.858209 | 0.126884  |  0.0746269  | 0.186567  | 1.52588e-05 |                     1 |
| Qwen/Qwen2.5-14B-Instruct | math:overall              | math     | overall              | ALWAYS_REWRITE_OR_RESTART | MATH_TUNED_RULE     | 200 |        0.74     |       0.865    | 0.125607  |  0.065      | 0.185     | 0.000112221 |                     1 |
| Qwen/Qwen2.5-14B-Instruct | math:overall              | math     | overall              | ALWAYS_REWRITE_OR_RESTART | FORMAT_TUNED_RULE   | 200 |        0.74     |       0.87     | 0.130627  |  0.07       | 0.19      | 6.87711e-05 |                     1 |
| Qwen/Qwen2.5-14B-Instruct | math:overall              | math     | overall              | ALWAYS_REWRITE_OR_RESTART | POOLED_RULE_BEST    | 200 |        0.74     |       0.87     | 0.130627  |  0.07       | 0.19      | 6.87711e-05 |                     1 |
| Qwen/Qwen2.5-14B-Instruct | math:overall              | math     | overall              | ALWAYS_REWRITE_OR_RESTART | POOLED_LEARNED_GATE | 200 |        0.74     |       0.805    | 0.065135  |  0.02       | 0.11      | 0.00719738  |                     1 |
| Qwen/Qwen2.5-14B-Instruct | math:overall              | math     | overall              | NO_INTERVENTION           | MATH_TUNED_RULE     | 200 |        0.345    |       0.865    | 0.52056   |  0.455      | 0.59      | 9.86076e-32 |                     1 |
| Qwen/Qwen2.5-14B-Instruct | math:overall              | math     | overall              | NO_INTERVENTION           | FORMAT_TUNED_RULE   | 200 |        0.345    |       0.87     | 0.52558   |  0.46       | 0.595     | 4.93038e-32 |                     1 |
| Qwen/Qwen2.5-14B-Instruct | math:overall              | math     | overall              | NO_INTERVENTION           | POOLED_RULE_BEST    | 200 |        0.345    |       0.87     | 0.52558   |  0.46       | 0.595     | 4.93038e-32 |                     1 |
| Qwen/Qwen2.5-14B-Instruct | math:overall              | math     | overall              | NO_INTERVENTION           | POOLED_LEARNED_GATE | 200 |        0.345    |       0.805    | 0.460087  |  0.39       | 0.53      | 4.03897e-28 |                     1 |
| Qwen/Qwen2.5-14B-Instruct | math:hard_cluster_main_r2 | math     | hard_cluster_main_r2 | ALWAYS_REWRITE_OR_RESTART | MATH_TUNED_RULE     | 124 |        0.75     |       0.854839 | 0.105109  |  0.0322581  | 0.177419  | 0.010622    |                     1 |
| Qwen/Qwen2.5-14B-Instruct | math:hard_cluster_main_r2 | math     | hard_cluster_main_r2 | ALWAYS_REWRITE_OR_RESTART | FORMAT_TUNED_RULE   | 124 |        0.75     |       0.854839 | 0.105109  |  0.0322581  | 0.177419  | 0.010622    |                     1 |
| Qwen/Qwen2.5-14B-Instruct | math:hard_cluster_main_r2 | math     | hard_cluster_main_r2 | ALWAYS_REWRITE_OR_RESTART | POOLED_RULE_BEST    | 124 |        0.75     |       0.854839 | 0.105109  |  0.0322581  | 0.177419  | 0.010622    |                     1 |
| Qwen/Qwen2.5-14B-Instruct | math:hard_cluster_main_r2 | math     | hard_cluster_main_r2 | ALWAYS_REWRITE_OR_RESTART | POOLED_LEARNED_GATE | 124 |        0.75     |       0.790323 | 0.0405444 | -0.016129   | 0.0967742 | 0.226562    |                     1 |
| Qwen/Qwen2.5-14B-Instruct | math:hard_cluster_main_r2 | math     | hard_cluster_main_r2 | NO_INTERVENTION           | MATH_TUNED_RULE     | 124 |        0.306452 |       0.854839 | 0.547274  |  0.459677   | 0.629032  | 6.77626e-21 |                     1 |
| Qwen/Qwen2.5-14B-Instruct | math:hard_cluster_main_r2 | math     | hard_cluster_main_r2 | NO_INTERVENTION           | FORMAT_TUNED_RULE   | 124 |        0.306452 |       0.854839 | 0.547274  |  0.459677   | 0.629032  | 6.77626e-21 |                     1 |
| Qwen/Qwen2.5-14B-Instruct | math:hard_cluster_main_r2 | math     | hard_cluster_main_r2 | NO_INTERVENTION           | POOLED_RULE_BEST    | 124 |        0.306452 |       0.854839 | 0.547274  |  0.459677   | 0.629032  | 6.77626e-21 |                     1 |
| Qwen/Qwen2.5-14B-Instruct | math:hard_cluster_main_r2 | math     | hard_cluster_main_r2 | NO_INTERVENTION           | POOLED_LEARNED_GATE | 124 |        0.306452 |       0.790323 | 0.48271   |  0.395161   | 0.572581  | 1.73472e-18 |                     1 |
| Qwen/Qwen2.5-14B-Instruct | math:hard_generic_main_r2 | math     | hard_generic_main_r2 | ALWAYS_REWRITE_OR_RESTART | MATH_TUNED_RULE     |  76 |        0.723684 |       0.881579 | 0.159368  |  0.0657895  | 0.263158  | 0.00753784  |                     1 |
| Qwen/Qwen2.5-14B-Instruct | math:hard_generic_main_r2 | math     | hard_generic_main_r2 | ALWAYS_REWRITE_OR_RESTART | FORMAT_TUNED_RULE   |  76 |        0.723684 |       0.894737 | 0.172566  |  0.0657895  | 0.276316  | 0.00442505  |                     1 |
| Qwen/Qwen2.5-14B-Instruct | math:hard_generic_main_r2 | math     | hard_generic_main_r2 | ALWAYS_REWRITE_OR_RESTART | POOLED_RULE_BEST    |  76 |        0.723684 |       0.894737 | 0.172566  |  0.0657895  | 0.276316  | 0.00442505  |                     1 |
| Qwen/Qwen2.5-14B-Instruct | math:hard_generic_main_r2 | math     | hard_generic_main_r2 | ALWAYS_REWRITE_OR_RESTART | POOLED_LEARNED_GATE |  76 |        0.723684 |       0.828947 | 0.107197  |  0.0394737  | 0.184211  | 0.0214844   |                     1 |
| Qwen/Qwen2.5-14B-Instruct | math:hard_generic_main_r2 | math     | hard_generic_main_r2 | NO_INTERVENTION           | MATH_TUNED_RULE     |  76 |        0.407895 |       0.881579 | 0.473566  |  0.355263   | 0.578947  | 2.91038e-11 |                     1 |
| Qwen/Qwen2.5-14B-Instruct | math:hard_generic_main_r2 | math     | hard_generic_main_r2 | NO_INTERVENTION           | FORMAT_TUNED_RULE   |  76 |        0.407895 |       0.894737 | 0.486763  |  0.381579   | 0.605263  | 1.45519e-11 |                     1 |
| Qwen/Qwen2.5-14B-Instruct | math:hard_generic_main_r2 | math     | hard_generic_main_r2 | NO_INTERVENTION           | POOLED_RULE_BEST    |  76 |        0.407895 |       0.894737 | 0.486763  |  0.381579   | 0.605263  | 1.45519e-11 |                     1 |
| Qwen/Qwen2.5-14B-Instruct | math:hard_generic_main_r2 | math     | hard_generic_main_r2 | NO_INTERVENTION           | POOLED_LEARNED_GATE |  76 |        0.407895 |       0.828947 | 0.421395  |  0.315789   | 0.539474  | 4.65661e-10 |                     1 |