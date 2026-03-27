# UNIFY-FULL Qwen/Qwen2.5-7B-Instruct Report

## Setup

- Model: `Qwen/Qwen2.5-7B-Instruct`
- Pooled train/eval split: `train=1001`, `eval=578`.
- Math-tuned simple family in the shared action space: `POOLED_SIMPLE_THRESHOLDED_TREE`.
- Format-tuned simple family in the shared action space: `POOLED_SIMPLE_2FEATURE`.
- Best pooled simple family: `POOLED_SIMPLE_2FEATURE`.

## Overall Read

- `NO_INTERVENTION`: utility `0.369`, intervention `0.000`, false-intervene `0.000`, missed-intervene `0.369`, latency `2.154s`
- `ALWAYS_REWRITE_OR_RESTART`: utility `0.488`, intervention `1.000`, false-intervene `0.822`, missed-intervene `0.000`, latency `2.560s`
- `MATH_TUNED_RULE`: utility `0.676`, intervention `0.631`, false-intervene `0.324`, missed-intervene `0.000`, latency `2.260s`
- `FORMAT_TUNED_RULE`: utility `0.706`, intervention `0.631`, false-intervene `0.294`, missed-intervene `0.000`, latency `2.409s`
- `POOLED_RULE_BEST`: utility `0.706`, intervention `0.631`, false-intervene `0.294`, missed-intervene `0.000`, latency `2.409s`
- `POOLED_LEARNED_GATE`: utility `0.671`, intervention `0.631`, false-intervene `0.329`, missed-intervene `0.000`, latency `2.368s`
- `ORACLE_POLICY`: utility `0.737`, intervention `0.631`, false-intervene `0.263`, missed-intervene `0.000`, latency `2.281s`

## Surface Checks

- math overall pooled-vs-rewrite: `+0.2943 [+0.2351, +0.3512]`
- format overall pooled-vs-rewrite: `+0.1120 [+0.0661, +0.1612]`
- cluster-hard pooled-vs-rewrite: `+0.2937 [+0.2290, +0.3588]`
- generic-hard pooled-vs-rewrite: `+0.2960 [+0.1892, +0.4054]`
- screened IFEval pooled-vs-rewrite: `+0.1025 [+0.0469, +0.1641]`
- IFBench pooled-vs-rewrite: `+0.1222 [+0.0439, +0.2018]`

## Domain-Specific vs Pooled Gap

| model_name               | module   | domain_policy     | pooled_policy    |   domain_utility |   pooled_utility |   utility_gap |
|:-------------------------|:---------|:------------------|:-----------------|-----------------:|-----------------:|--------------:|
| Qwen/Qwen2.5-7B-Instruct | math     | MATH_TUNED_RULE   | POOLED_RULE_BEST |          0.77381 |          0.77381 |             0 |
| Qwen/Qwen2.5-7B-Instruct | format   | FORMAT_TUNED_RULE | POOLED_RULE_BEST |          0.61157 |          0.61157 |             0 |

## Transfer Asymmetry

| model_name               | direction             | scope          | policy            |   utility |   intervention_rate |   rewrite_delta |
|:-------------------------|:----------------------|:---------------|:------------------|----------:|--------------------:|----------------:|
| Qwen/Qwen2.5-7B-Instruct | math_to_format        | format:overall | MATH_TUNED_RULE   |  0.541322 |            0.53719  |       0.0409979 |
| Qwen/Qwen2.5-7B-Instruct | format_to_math        | math:overall   | FORMAT_TUNED_RULE |  0.77381  |            0.699405 |       0.294326  |
| Qwen/Qwen2.5-7B-Instruct | pooled_to_both_math   | math:overall   | POOLED_RULE_BEST  |  0.77381  |            0.699405 |       0.294326  |
| Qwen/Qwen2.5-7B-Instruct | pooled_to_both_format | format:overall | POOLED_RULE_BEST  |  0.61157  |            0.53719  |       0.112043  |

## Pairwise Table

| model_name               | scope                     | module   | surface_name         | base_policy               | alt_policy          |   n |   base_accuracy |   alt_accuracy |     delta |    ci_low |   ci_high |   mcnemar_p |   direction_favorable |
|:-------------------------|:--------------------------|:---------|:---------------------|:--------------------------|:--------------------|----:|----------------:|---------------:|----------:|----------:|----------:|------------:|----------------------:|
| Qwen/Qwen2.5-7B-Instruct | overall                   | pooled   | overall              | ALWAYS_REWRITE_OR_RESTART | MATH_TUNED_RULE     | 578 |        0.487889 |       0.676471 | 0.188054  | 0.150519  | 0.224913  | 3.95445e-22 |                     1 |
| Qwen/Qwen2.5-7B-Instruct | overall                   | pooled   | overall              | ALWAYS_REWRITE_OR_RESTART | FORMAT_TUNED_RULE   | 578 |        0.487889 |       0.705882 | 0.217644  | 0.179931  | 0.257785  | 1.35004e-25 |                     1 |
| Qwen/Qwen2.5-7B-Instruct | overall                   | pooled   | overall              | ALWAYS_REWRITE_OR_RESTART | POOLED_RULE_BEST    | 578 |        0.487889 |       0.705882 | 0.217644  | 0.179931  | 0.257785  | 1.35004e-25 |                     1 |
| Qwen/Qwen2.5-7B-Instruct | overall                   | pooled   | overall              | ALWAYS_REWRITE_OR_RESTART | POOLED_LEARNED_GATE | 578 |        0.487889 |       0.67128  | 0.18274   | 0.148789  | 0.217993  | 4.94811e-24 |                     1 |
| Qwen/Qwen2.5-7B-Instruct | overall                   | pooled   | overall              | NO_INTERVENTION           | MATH_TUNED_RULE     | 578 |        0.368512 |       0.676471 | 0.307402  | 0.269896  | 0.344291  | 5.22024e-54 |                     1 |
| Qwen/Qwen2.5-7B-Instruct | overall                   | pooled   | overall              | NO_INTERVENTION           | FORMAT_TUNED_RULE   | 578 |        0.368512 |       0.705882 | 0.336991  | 0.299308  | 0.377163  | 3.98273e-59 |                     1 |
| Qwen/Qwen2.5-7B-Instruct | overall                   | pooled   | overall              | NO_INTERVENTION           | POOLED_RULE_BEST    | 578 |        0.368512 |       0.705882 | 0.336991  | 0.299308  | 0.377163  | 3.98273e-59 |                     1 |
| Qwen/Qwen2.5-7B-Instruct | overall                   | pooled   | overall              | NO_INTERVENTION           | POOLED_LEARNED_GATE | 578 |        0.368512 |       0.67128  | 0.302087  | 0.264706  | 0.3391    | 4.17619e-53 |                     1 |
| Qwen/Qwen2.5-7B-Instruct | format:overall            | format   | overall              | ALWAYS_REWRITE_OR_RESTART | MATH_TUNED_RULE     | 242 |        0.5      |       0.541322 | 0.0409979 | 0.0123967 | 0.0743802 | 0.0212708   |                     1 |
| Qwen/Qwen2.5-7B-Instruct | format:overall            | format   | overall              | ALWAYS_REWRITE_OR_RESTART | FORMAT_TUNED_RULE   | 242 |        0.5      |       0.61157  | 0.112043  | 0.0661157 | 0.161157  | 7.42753e-06 |                     1 |
| Qwen/Qwen2.5-7B-Instruct | format:overall            | format   | overall              | ALWAYS_REWRITE_OR_RESTART | POOLED_RULE_BEST    | 242 |        0.5      |       0.61157  | 0.112043  | 0.0661157 | 0.161157  | 7.42753e-06 |                     1 |
| Qwen/Qwen2.5-7B-Instruct | format:overall            | format   | overall              | ALWAYS_REWRITE_OR_RESTART | POOLED_LEARNED_GATE | 242 |        0.5      |       0.582645 | 0.0826508 | 0.0413223 | 0.123967  | 8.79765e-05 |                     1 |
| Qwen/Qwen2.5-7B-Instruct | format:overall            | format   | overall              | NO_INTERVENTION           | MATH_TUNED_RULE     | 242 |        0.46281  |       0.541322 | 0.0778161 | 0.0454545 | 0.11157   | 3.8147e-06  |                     1 |
| Qwen/Qwen2.5-7B-Instruct | format:overall            | format   | overall              | NO_INTERVENTION           | FORMAT_TUNED_RULE   | 242 |        0.46281  |       0.61157  | 0.148862  | 0.107438  | 0.194215  | 2.91038e-11 |                     1 |
| Qwen/Qwen2.5-7B-Instruct | format:overall            | format   | overall              | NO_INTERVENTION           | POOLED_RULE_BEST    | 242 |        0.46281  |       0.61157  | 0.148862  | 0.107438  | 0.194215  | 2.91038e-11 |                     1 |
| Qwen/Qwen2.5-7B-Instruct | format:overall            | format   | overall              | NO_INTERVENTION           | POOLED_LEARNED_GATE | 242 |        0.46281  |       0.582645 | 0.119469  | 0.0785124 | 0.161157  | 3.72529e-09 |                     1 |
| Qwen/Qwen2.5-7B-Instruct | format:ifbench            | format   | ifbench              | ALWAYS_REWRITE_OR_RESTART | MATH_TUNED_RULE     | 114 |        0.324561 |       0.412281 | 0.0875    | 0.0175439 | 0.157895  | 0.0212708   |                     1 |
| Qwen/Qwen2.5-7B-Instruct | format:ifbench            | format   | ifbench              | ALWAYS_REWRITE_OR_RESTART | FORMAT_TUNED_RULE   | 114 |        0.324561 |       0.447368 | 0.122171  | 0.0438596 | 0.201754  | 0.00434351  |                     1 |
| Qwen/Qwen2.5-7B-Instruct | format:ifbench            | format   | ifbench              | ALWAYS_REWRITE_OR_RESTART | POOLED_RULE_BEST    | 114 |        0.324561 |       0.447368 | 0.122171  | 0.0438596 | 0.201754  | 0.00434351  |                     1 |
| Qwen/Qwen2.5-7B-Instruct | format:ifbench            | format   | ifbench              | ALWAYS_REWRITE_OR_RESTART | POOLED_LEARNED_GATE | 114 |        0.324561 |       0.412281 | 0.0875    | 0.0175439 | 0.157895  | 0.0212708   |                     1 |
| Qwen/Qwen2.5-7B-Instruct | format:ifbench            | format   | ifbench              | NO_INTERVENTION           | MATH_TUNED_RULE     | 114 |        0.27193  |       0.412281 | 0.140675  | 0.0789474 | 0.210526  | 3.05176e-05 |                     1 |
| Qwen/Qwen2.5-7B-Instruct | format:ifbench            | format   | ifbench              | NO_INTERVENTION           | FORMAT_TUNED_RULE   | 114 |        0.27193  |       0.447368 | 0.175346  | 0.105263  | 0.245614  | 1.90735e-06 |                     1 |
| Qwen/Qwen2.5-7B-Instruct | format:ifbench            | format   | ifbench              | NO_INTERVENTION           | POOLED_RULE_BEST    | 114 |        0.27193  |       0.447368 | 0.175346  | 0.105263  | 0.245614  | 1.90735e-06 |                     1 |
| Qwen/Qwen2.5-7B-Instruct | format:ifbench            | format   | ifbench              | NO_INTERVENTION           | POOLED_LEARNED_GATE | 114 |        0.27193  |       0.412281 | 0.140675  | 0.0789474 | 0.210526  | 3.05176e-05 |                     1 |
| Qwen/Qwen2.5-7B-Instruct | format:ifeval_screened    | format   | ifeval_screened      | ALWAYS_REWRITE_OR_RESTART | MATH_TUNED_RULE     | 128 |        0.65625  |       0.65625  | 0         | 0         | 0         | 1           |                     0 |
| Qwen/Qwen2.5-7B-Instruct | format:ifeval_screened    | format   | ifeval_screened      | ALWAYS_REWRITE_OR_RESTART | FORMAT_TUNED_RULE   | 128 |        0.65625  |       0.757812 | 0.102543  | 0.046875  | 0.164062  | 0.000976562 |                     1 |
| Qwen/Qwen2.5-7B-Instruct | format:ifeval_screened    | format   | ifeval_screened      | ALWAYS_REWRITE_OR_RESTART | POOLED_RULE_BEST    | 128 |        0.65625  |       0.757812 | 0.102543  | 0.046875  | 0.164062  | 0.000976562 |                     1 |
| Qwen/Qwen2.5-7B-Instruct | format:ifeval_screened    | format   | ifeval_screened      | ALWAYS_REWRITE_OR_RESTART | POOLED_LEARNED_GATE | 128 |        0.65625  |       0.734375 | 0.0790742 | 0.0390625 | 0.132812  | 0.00195312  |                     1 |
| Qwen/Qwen2.5-7B-Instruct | format:ifeval_screened    | format   | ifeval_screened      | NO_INTERVENTION           | MATH_TUNED_RULE     | 128 |        0.632812 |       0.65625  | 0.0238945 | 0         | 0.0546875 | 0.25        |                     1 |
| Qwen/Qwen2.5-7B-Instruct | format:ifeval_screened    | format   | ifeval_screened      | NO_INTERVENTION           | FORMAT_TUNED_RULE   | 128 |        0.632812 |       0.757812 | 0.126438  | 0.0703125 | 0.1875    | 3.05176e-05 |                     1 |
| Qwen/Qwen2.5-7B-Instruct | format:ifeval_screened    | format   | ifeval_screened      | NO_INTERVENTION           | POOLED_RULE_BEST    | 128 |        0.632812 |       0.757812 | 0.126438  | 0.0703125 | 0.1875    | 3.05176e-05 |                     1 |
| Qwen/Qwen2.5-7B-Instruct | format:ifeval_screened    | format   | ifeval_screened      | NO_INTERVENTION           | POOLED_LEARNED_GATE | 128 |        0.632812 |       0.734375 | 0.102969  | 0.0546875 | 0.15625   | 0.000244141 |                     1 |
| Qwen/Qwen2.5-7B-Instruct | math:overall              | math     | overall              | ALWAYS_REWRITE_OR_RESTART | MATH_TUNED_RULE     | 336 |        0.479167 |       0.77381  | 0.294326  | 0.235119  | 0.35119   | 8.12435e-21 |                     1 |
| Qwen/Qwen2.5-7B-Instruct | math:overall              | math     | overall              | ALWAYS_REWRITE_OR_RESTART | FORMAT_TUNED_RULE   | 336 |        0.479167 |       0.77381  | 0.294326  | 0.235119  | 0.35119   | 8.12435e-21 |                     1 |
| Qwen/Qwen2.5-7B-Instruct | math:overall              | math     | overall              | ALWAYS_REWRITE_OR_RESTART | POOLED_RULE_BEST    | 336 |        0.479167 |       0.77381  | 0.294326  | 0.235119  | 0.35119   | 8.12435e-21 |                     1 |
| Qwen/Qwen2.5-7B-Instruct | math:overall              | math     | overall              | ALWAYS_REWRITE_OR_RESTART | POOLED_LEARNED_GATE | 336 |        0.479167 |       0.735119 | 0.255821  | 0.205357  | 0.306548  | 2.72614e-20 |                     1 |
| Qwen/Qwen2.5-7B-Instruct | math:overall              | math     | overall              | NO_INTERVENTION           | MATH_TUNED_RULE     | 336 |        0.300595 |       0.77381  | 0.472525  | 0.422619  | 0.526786  | 2.73691e-48 |                     1 |
| Qwen/Qwen2.5-7B-Instruct | math:overall              | math     | overall              | NO_INTERVENTION           | FORMAT_TUNED_RULE   | 336 |        0.300595 |       0.77381  | 0.472525  | 0.422619  | 0.526786  | 2.73691e-48 |                     1 |
| Qwen/Qwen2.5-7B-Instruct | math:overall              | math     | overall              | NO_INTERVENTION           | POOLED_RULE_BEST    | 336 |        0.300595 |       0.77381  | 0.472525  | 0.422619  | 0.526786  | 2.73691e-48 |                     1 |
| Qwen/Qwen2.5-7B-Instruct | math:overall              | math     | overall              | NO_INTERVENTION           | POOLED_LEARNED_GATE | 336 |        0.300595 |       0.735119 | 0.434021  | 0.380952  | 0.488095  | 2.24208e-44 |                     1 |
| Qwen/Qwen2.5-7B-Instruct | math:hard_cluster_main_r2 | math     | hard_cluster_main_r2 | ALWAYS_REWRITE_OR_RESTART | MATH_TUNED_RULE     | 262 |        0.461832 |       0.755725 | 0.293656  | 0.229008  | 0.358779  | 1.08272e-15 |                     1 |
| Qwen/Qwen2.5-7B-Instruct | math:hard_cluster_main_r2 | math     | hard_cluster_main_r2 | ALWAYS_REWRITE_OR_RESTART | FORMAT_TUNED_RULE   | 262 |        0.461832 |       0.755725 | 0.293656  | 0.229008  | 0.358779  | 1.08272e-15 |                     1 |
| Qwen/Qwen2.5-7B-Instruct | math:hard_cluster_main_r2 | math     | hard_cluster_main_r2 | ALWAYS_REWRITE_OR_RESTART | POOLED_RULE_BEST    | 262 |        0.461832 |       0.755725 | 0.293656  | 0.229008  | 0.358779  | 1.08272e-15 |                     1 |
| Qwen/Qwen2.5-7B-Instruct | math:hard_cluster_main_r2 | math     | hard_cluster_main_r2 | ALWAYS_REWRITE_OR_RESTART | POOLED_LEARNED_GATE | 262 |        0.461832 |       0.709924 | 0.248156  | 0.19084   | 0.305344  | 3.41832e-15 |                     1 |
| Qwen/Qwen2.5-7B-Instruct | math:hard_cluster_main_r2 | math     | hard_cluster_main_r2 | NO_INTERVENTION           | MATH_TUNED_RULE     | 262 |        0.293893 |       0.755725 | 0.460718  | 0.400763  | 0.519084  | 7.52316e-37 |                     1 |
| Qwen/Qwen2.5-7B-Instruct | math:hard_cluster_main_r2 | math     | hard_cluster_main_r2 | NO_INTERVENTION           | FORMAT_TUNED_RULE   | 262 |        0.293893 |       0.755725 | 0.460718  | 0.400763  | 0.519084  | 7.52316e-37 |                     1 |
| Qwen/Qwen2.5-7B-Instruct | math:hard_cluster_main_r2 | math     | hard_cluster_main_r2 | NO_INTERVENTION           | POOLED_RULE_BEST    | 262 |        0.293893 |       0.755725 | 0.460718  | 0.400763  | 0.519084  | 7.52316e-37 |                     1 |
| Qwen/Qwen2.5-7B-Instruct | math:hard_cluster_main_r2 | math     | hard_cluster_main_r2 | NO_INTERVENTION           | POOLED_LEARNED_GATE | 262 |        0.293893 |       0.709924 | 0.415218  | 0.354962  | 0.473282  | 3.08149e-33 |                     1 |
| Qwen/Qwen2.5-7B-Instruct | math:hard_generic_main_r2 | math     | hard_generic_main_r2 | ALWAYS_REWRITE_OR_RESTART | MATH_TUNED_RULE     |  74 |        0.540541 |       0.837838 | 0.296047  | 0.189189  | 0.405405  | 2.98023e-06 |                     1 |
| Qwen/Qwen2.5-7B-Instruct | math:hard_generic_main_r2 | math     | hard_generic_main_r2 | ALWAYS_REWRITE_OR_RESTART | FORMAT_TUNED_RULE   |  74 |        0.540541 |       0.837838 | 0.296047  | 0.189189  | 0.405405  | 2.98023e-06 |                     1 |
| Qwen/Qwen2.5-7B-Instruct | math:hard_generic_main_r2 | math     | hard_generic_main_r2 | ALWAYS_REWRITE_OR_RESTART | POOLED_RULE_BEST    |  74 |        0.540541 |       0.837838 | 0.296047  | 0.189189  | 0.405405  | 2.98023e-06 |                     1 |
| Qwen/Qwen2.5-7B-Instruct | math:hard_generic_main_r2 | math     | hard_generic_main_r2 | ALWAYS_REWRITE_OR_RESTART | POOLED_LEARNED_GATE |  74 |        0.540541 |       0.824324 | 0.282561  | 0.175676  | 0.391892  | 5.72205e-06 |                     1 |
| Qwen/Qwen2.5-7B-Instruct | math:hard_generic_main_r2 | math     | hard_generic_main_r2 | NO_INTERVENTION           | MATH_TUNED_RULE     |  74 |        0.324324 |       0.837838 | 0.512628  | 0.405405  | 0.635135  | 7.27596e-12 |                     1 |
| Qwen/Qwen2.5-7B-Instruct | math:hard_generic_main_r2 | math     | hard_generic_main_r2 | NO_INTERVENTION           | FORMAT_TUNED_RULE   |  74 |        0.324324 |       0.837838 | 0.512628  | 0.405405  | 0.635135  | 7.27596e-12 |                     1 |
| Qwen/Qwen2.5-7B-Instruct | math:hard_generic_main_r2 | math     | hard_generic_main_r2 | NO_INTERVENTION           | POOLED_RULE_BEST    |  74 |        0.324324 |       0.837838 | 0.512628  | 0.405405  | 0.635135  | 7.27596e-12 |                     1 |
| Qwen/Qwen2.5-7B-Instruct | math:hard_generic_main_r2 | math     | hard_generic_main_r2 | NO_INTERVENTION           | POOLED_LEARNED_GATE |  74 |        0.324324 |       0.824324 | 0.499142  | 0.391892  | 0.621622  | 1.45519e-11 |                     1 |