# UNIFY-FULL mistralai/Mistral-7B-Instruct-v0.3 Report

## Setup

- Model: `mistralai/Mistral-7B-Instruct-v0.3`
- Pooled train/eval split: `train=827`, `eval=454`.
- Math-tuned simple family in the shared action space: `POOLED_SIMPLE_2FEATURE`.
- Format-tuned simple family in the shared action space: `POOLED_SIMPLE_3FEATURE`.
- Best pooled simple family: `POOLED_SIMPLE_3FEATURE`.

## Overall Read

- `NO_INTERVENTION`: utility `0.161`, intervention `0.000`, false-intervene `0.000`, missed-intervene `0.317`, latency `3.352s`
- `ALWAYS_REWRITE_OR_RESTART`: utility `0.258`, intervention `1.000`, false-intervene `0.877`, missed-intervene `0.000`, latency `4.008s`
- `MATH_TUNED_RULE`: utility `0.427`, intervention `0.839`, false-intervene `0.573`, missed-intervene `0.000`, latency `4.157s`
- `FORMAT_TUNED_RULE`: utility `0.432`, intervention `0.839`, false-intervene `0.568`, missed-intervene `0.000`, latency `4.174s`
- `POOLED_RULE_BEST`: utility `0.427`, intervention `0.839`, false-intervene `0.573`, missed-intervene `0.000`, latency `4.329s`
- `POOLED_LEARNED_GATE`: utility `0.390`, intervention `0.806`, false-intervene `0.577`, missed-intervene `0.007`, latency `3.908s`
- `ORACLE_POLICY`: utility `0.478`, intervention `0.839`, false-intervene `0.522`, missed-intervene `0.000`, latency `3.959s`

## Surface Checks

- math overall pooled-vs-rewrite: `+0.2676 [+0.2019, +0.3286]`
- format overall pooled-vs-rewrite: `+0.0833 [+0.0290, +0.1369]`
- cluster-hard pooled-vs-rewrite: `+0.2468 [+0.1739, +0.3261]`
- generic-hard pooled-vs-rewrite: `+0.3065 [+0.2000, +0.4267]`
- screened IFEval pooled-vs-rewrite: `+0.1112 [+0.0296, +0.1926]`
- IFBench pooled-vs-rewrite: `+0.0467 [-0.0189, +0.1226]`

## Domain-Specific vs Pooled Gap

| model_name                         | module   | domain_policy     | pooled_policy    |   domain_utility |   pooled_utility |   utility_gap |
|:-----------------------------------|:---------|:------------------|:-----------------|-----------------:|-----------------:|--------------:|
| mistralai/Mistral-7B-Instruct-v0.3 | math     | MATH_TUNED_RULE   | POOLED_RULE_BEST |         0.389671 |         0.389671 |             0 |
| mistralai/Mistral-7B-Instruct-v0.3 | format   | FORMAT_TUNED_RULE | POOLED_RULE_BEST |         0.460581 |         0.460581 |             0 |

## Transfer Asymmetry

| model_name                         | direction             | scope          | policy            |   utility |   intervention_rate |   rewrite_delta |
|:-----------------------------------|:----------------------|:---------------|:------------------|----------:|--------------------:|----------------:|
| mistralai/Mistral-7B-Instruct-v0.3 | math_to_format        | format:overall | MATH_TUNED_RULE   |  0.460581 |            0.759336 |       0.0830809 |
| mistralai/Mistral-7B-Instruct-v0.3 | format_to_math        | math:overall   | FORMAT_TUNED_RULE |  0.399061 |            0.929577 |       0.277324  |
| mistralai/Mistral-7B-Instruct-v0.3 | pooled_to_both_math   | math:overall   | POOLED_RULE_BEST  |  0.389671 |            0.929577 |       0.267568  |
| mistralai/Mistral-7B-Instruct-v0.3 | pooled_to_both_format | format:overall | POOLED_RULE_BEST  |  0.460581 |            0.759336 |       0.0832593 |

## Pairwise Table

| model_name                         | scope                     | module   | surface_name         | base_policy               | alt_policy          |   n |   base_accuracy |   alt_accuracy |     delta |     ci_low |   ci_high |   mcnemar_p |   direction_favorable |
|:-----------------------------------|:--------------------------|:---------|:---------------------|:--------------------------|:--------------------|----:|----------------:|---------------:|----------:|-----------:|----------:|------------:|----------------------:|
| mistralai/Mistral-7B-Instruct-v0.3 | overall                   | pooled   | overall              | ALWAYS_REWRITE_OR_RESTART | MATH_TUNED_RULE     | 454 |       0.257709  |       0.427313 | 0.16937   |  0.129956  | 0.211454  | 1.10519e-14 |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | overall                   | pooled   | overall              | ALWAYS_REWRITE_OR_RESTART | FORMAT_TUNED_RULE   | 454 |       0.257709  |       0.431718 | 0.173763  |  0.132159  | 0.218062  | 1.60631e-13 |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | overall                   | pooled   | overall              | ALWAYS_REWRITE_OR_RESTART | POOLED_RULE_BEST    | 454 |       0.257709  |       0.427313 | 0.169362  |  0.129956  | 0.211454  | 2.20892e-14 |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | overall                   | pooled   | overall              | ALWAYS_REWRITE_OR_RESTART | POOLED_LEARNED_GATE | 454 |       0.257709  |       0.389868 | 0.131597  |  0.0991189 | 0.167401  | 1.38128e-12 |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | overall                   | pooled   | overall              | NO_INTERVENTION           | MATH_TUNED_RULE     | 454 |       0.160793  |       0.427313 | 0.266307  |  0.226872  | 0.30837   | 7.52316e-37 |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | overall                   | pooled   | overall              | NO_INTERVENTION           | FORMAT_TUNED_RULE   | 454 |       0.160793  |       0.431718 | 0.2707    |  0.231278  | 0.310573  | 1.88079e-37 |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | overall                   | pooled   | overall              | NO_INTERVENTION           | POOLED_RULE_BEST    | 454 |       0.160793  |       0.427313 | 0.2663    |  0.226872  | 0.30837   | 7.52316e-37 |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | overall                   | pooled   | overall              | NO_INTERVENTION           | POOLED_LEARNED_GATE | 454 |       0.160793  |       0.389868 | 0.228534  |  0.19163   | 0.26652   | 9.86076e-32 |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | format:overall            | format   | overall              | ALWAYS_REWRITE_OR_RESTART | MATH_TUNED_RULE     | 241 |       0.377593  |       0.460581 | 0.0830809 |  0.0290456 | 0.136929  | 0.00365777  |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | format:overall            | format   | overall              | ALWAYS_REWRITE_OR_RESTART | FORMAT_TUNED_RULE   | 241 |       0.377593  |       0.460581 | 0.0832593 |  0.0290456 | 0.136929  | 0.00453386  |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | format:overall            | format   | overall              | ALWAYS_REWRITE_OR_RESTART | POOLED_RULE_BEST    | 241 |       0.377593  |       0.460581 | 0.0832593 |  0.0290456 | 0.136929  | 0.00453386  |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | format:overall            | format   | overall              | ALWAYS_REWRITE_OR_RESTART | POOLED_LEARNED_GATE | 241 |       0.377593  |       0.39834  | 0.0206909 | -0.0124481 | 0.0539419 | 0.301758    |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | format:overall            | format   | overall              | NO_INTERVENTION           | MATH_TUNED_RULE     | 241 |       0.240664  |       0.460581 | 0.220712  |  0.170124  | 0.273859  | 2.22045e-16 |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | format:overall            | format   | overall              | NO_INTERVENTION           | FORMAT_TUNED_RULE   | 241 |       0.240664  |       0.460581 | 0.22089   |  0.170124  | 0.273859  | 2.22045e-16 |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | format:overall            | format   | overall              | NO_INTERVENTION           | POOLED_RULE_BEST    | 241 |       0.240664  |       0.460581 | 0.22089   |  0.170124  | 0.273859  | 2.22045e-16 |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | format:overall            | format   | overall              | NO_INTERVENTION           | POOLED_LEARNED_GATE | 241 |       0.240664  |       0.39834  | 0.158322  |  0.116183  | 0.20332   | 7.27596e-12 |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | format:ifbench            | format   | ifbench              | ALWAYS_REWRITE_OR_RESTART | MATH_TUNED_RULE     | 106 |       0.245283  |       0.292453 | 0.0466698 | -0.0188679 | 0.122642  | 0.301758    |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | format:ifbench            | format   | ifbench              | ALWAYS_REWRITE_OR_RESTART | FORMAT_TUNED_RULE   | 106 |       0.245283  |       0.292453 | 0.0466698 | -0.0188679 | 0.122642  | 0.301758    |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | format:ifbench            | format   | ifbench              | ALWAYS_REWRITE_OR_RESTART | POOLED_RULE_BEST    | 106 |       0.245283  |       0.292453 | 0.0466698 | -0.0188679 | 0.122642  | 0.301758    |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | format:ifbench            | format   | ifbench              | ALWAYS_REWRITE_OR_RESTART | POOLED_LEARNED_GATE | 106 |       0.245283  |       0.292453 | 0.0466698 | -0.0188679 | 0.122642  | 0.301758    |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | format:ifbench            | format   | ifbench              | NO_INTERVENTION           | MATH_TUNED_RULE     | 106 |       0.160377  |       0.292453 | 0.132264  |  0.0754717 | 0.198113  | 0.00012207  |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | format:ifbench            | format   | ifbench              | NO_INTERVENTION           | FORMAT_TUNED_RULE   | 106 |       0.160377  |       0.292453 | 0.132264  |  0.0754717 | 0.198113  | 0.00012207  |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | format:ifbench            | format   | ifbench              | NO_INTERVENTION           | POOLED_RULE_BEST    | 106 |       0.160377  |       0.292453 | 0.132264  |  0.0754717 | 0.198113  | 0.00012207  |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | format:ifbench            | format   | ifbench              | NO_INTERVENTION           | POOLED_LEARNED_GATE | 106 |       0.160377  |       0.292453 | 0.132264  |  0.0754717 | 0.198113  | 0.00012207  |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | format:ifeval_screened    | format   | ifeval_screened      | ALWAYS_REWRITE_OR_RESTART | MATH_TUNED_RULE     | 135 |       0.481481  |       0.592593 | 0.111496  |  0.037037  | 0.192593  | 0.00813006  |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | format:ifeval_screened    | format   | ifeval_screened      | ALWAYS_REWRITE_OR_RESTART | FORMAT_TUNED_RULE   | 135 |       0.481481  |       0.592593 | 0.111248  |  0.0296296 | 0.192593  | 0.0106738   |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | format:ifeval_screened    | format   | ifeval_screened      | ALWAYS_REWRITE_OR_RESTART | POOLED_RULE_BEST    | 135 |       0.481481  |       0.592593 | 0.111248  |  0.0296296 | 0.192593  | 0.0106738   |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | format:ifeval_screened    | format   | ifeval_screened      | ALWAYS_REWRITE_OR_RESTART | POOLED_LEARNED_GATE | 135 |       0.481481  |       0.481481 | 0         |  0         | 0         | 1           |                     0 |
| mistralai/Mistral-7B-Instruct-v0.3 | format:ifeval_screened    | format   | ifeval_screened      | NO_INTERVENTION           | MATH_TUNED_RULE     | 135 |       0.303704  |       0.592593 | 0.288978  |  0.214815  | 0.37037   | 3.63798e-12 |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | format:ifeval_screened    | format   | ifeval_screened      | NO_INTERVENTION           | FORMAT_TUNED_RULE   | 135 |       0.303704  |       0.592593 | 0.28873   |  0.214815  | 0.37037   | 3.63798e-12 |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | format:ifeval_screened    | format   | ifeval_screened      | NO_INTERVENTION           | POOLED_RULE_BEST    | 135 |       0.303704  |       0.592593 | 0.28873   |  0.214815  | 0.37037   | 3.63798e-12 |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | format:ifeval_screened    | format   | ifeval_screened      | NO_INTERVENTION           | POOLED_LEARNED_GATE | 135 |       0.303704  |       0.481481 | 0.177481  |  0.118519  | 0.244444  | 1.19209e-07 |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | math:overall              | math     | overall              | ALWAYS_REWRITE_OR_RESTART | MATH_TUNED_RULE     | 213 |       0.122066  |       0.389671 | 0.267568  |  0.201878  | 0.328638  | 9.04832e-15 |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | math:overall              | math     | overall              | ALWAYS_REWRITE_OR_RESTART | FORMAT_TUNED_RULE   | 213 |       0.122066  |       0.399061 | 0.277324  |  0.206573  | 0.347418  | 1.00986e-12 |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | math:overall              | math     | overall              | ALWAYS_REWRITE_OR_RESTART | POOLED_RULE_BEST    | 213 |       0.122066  |       0.389671 | 0.267568  |  0.201878  | 0.328638  | 9.04832e-15 |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | math:overall              | math     | overall              | ALWAYS_REWRITE_OR_RESTART | POOLED_LEARNED_GATE | 213 |       0.122066  |       0.380282 | 0.25839   |  0.192488  | 0.323944  | 1.38213e-13 |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | math:overall              | math     | overall              | NO_INTERVENTION           | MATH_TUNED_RULE     | 213 |       0.0704225 |       0.389671 | 0.319369  |  0.258216  | 0.384977  | 6.77626e-21 |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | math:overall              | math     | overall              | NO_INTERVENTION           | FORMAT_TUNED_RULE   | 213 |       0.0704225 |       0.399061 | 0.329124  |  0.267606  | 0.394366  | 1.69407e-21 |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | math:overall              | math     | overall              | NO_INTERVENTION           | POOLED_RULE_BEST    | 213 |       0.0704225 |       0.389671 | 0.319369  |  0.258216  | 0.384977  | 6.77626e-21 |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | math:overall              | math     | overall              | NO_INTERVENTION           | POOLED_LEARNED_GATE | 213 |       0.0704225 |       0.380282 | 0.31019   |  0.253521  | 0.370892  | 2.71051e-20 |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | math:hard_cluster_main_r2 | math     | hard_cluster_main_r2 | ALWAYS_REWRITE_OR_RESTART | MATH_TUNED_RULE     | 138 |       0.123188  |       0.369565 | 0.246783  |  0.173913  | 0.326087  | 5.39876e-09 |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | math:hard_cluster_main_r2 | math     | hard_cluster_main_r2 | ALWAYS_REWRITE_OR_RESTART | FORMAT_TUNED_RULE   | 138 |       0.123188  |       0.384058 | 0.261598  |  0.173913  | 0.347826  | 4.40594e-08 |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | math:hard_cluster_main_r2 | math     | hard_cluster_main_r2 | ALWAYS_REWRITE_OR_RESTART | POOLED_RULE_BEST    | 138 |       0.123188  |       0.369565 | 0.246783  |  0.173913  | 0.326087  | 5.39876e-09 |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | math:hard_cluster_main_r2 | math     | hard_cluster_main_r2 | ALWAYS_REWRITE_OR_RESTART | POOLED_LEARNED_GATE | 138 |       0.123188  |       0.369565 | 0.247109  |  0.173913  | 0.326087  | 1.07684e-09 |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | math:hard_cluster_main_r2 | math     | hard_cluster_main_r2 | NO_INTERVENTION           | MATH_TUNED_RULE     | 138 |       0.0869565 |       0.369565 | 0.282967  |  0.210145  | 0.362319  | 3.63798e-12 |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | math:hard_cluster_main_r2 | math     | hard_cluster_main_r2 | NO_INTERVENTION           | FORMAT_TUNED_RULE   | 138 |       0.0869565 |       0.384058 | 0.297783  |  0.224638  | 0.376812  | 9.09495e-13 |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | math:hard_cluster_main_r2 | math     | hard_cluster_main_r2 | NO_INTERVENTION           | POOLED_RULE_BEST    | 138 |       0.0869565 |       0.369565 | 0.282967  |  0.210145  | 0.362319  | 3.63798e-12 |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | math:hard_cluster_main_r2 | math     | hard_cluster_main_r2 | NO_INTERVENTION           | POOLED_LEARNED_GATE | 138 |       0.0869565 |       0.369565 | 0.283293  |  0.210145  | 0.355072  | 3.63798e-12 |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | math:hard_generic_main_r2 | math     | hard_generic_main_r2 | ALWAYS_REWRITE_OR_RESTART | MATH_TUNED_RULE     |  75 |       0.12      |       0.426667 | 0.3065    |  0.2       | 0.426667  | 1.54972e-06 |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | math:hard_generic_main_r2 | math     | hard_generic_main_r2 | ALWAYS_REWRITE_OR_RESTART | FORMAT_TUNED_RULE   |  75 |       0.12      |       0.426667 | 0.305547  |  0.186667  | 0.426667  | 1.52364e-05 |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | math:hard_generic_main_r2 | math     | hard_generic_main_r2 | ALWAYS_REWRITE_OR_RESTART | POOLED_RULE_BEST    |  75 |       0.12      |       0.426667 | 0.3065    |  0.2       | 0.426667  | 1.54972e-06 |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | math:hard_generic_main_r2 | math     | hard_generic_main_r2 | ALWAYS_REWRITE_OR_RESTART | POOLED_LEARNED_GATE |  75 |       0.12      |       0.4      | 0.27904   |  0.16      | 0.4       | 4.92334e-05 |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | math:hard_generic_main_r2 | math     | hard_generic_main_r2 | NO_INTERVENTION           | MATH_TUNED_RULE     |  75 |       0.04      |       0.426667 | 0.387473  |  0.28      | 0.493333  | 3.72529e-09 |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | math:hard_generic_main_r2 | math     | hard_generic_main_r2 | NO_INTERVENTION           | FORMAT_TUNED_RULE   |  75 |       0.04      |       0.426667 | 0.38652   |  0.28      | 0.493333  | 3.72529e-09 |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | math:hard_generic_main_r2 | math     | hard_generic_main_r2 | NO_INTERVENTION           | POOLED_RULE_BEST    |  75 |       0.04      |       0.426667 | 0.387473  |  0.28      | 0.493333  | 3.72529e-09 |                     1 |
| mistralai/Mistral-7B-Instruct-v0.3 | math:hard_generic_main_r2 | math     | hard_generic_main_r2 | NO_INTERVENTION           | POOLED_LEARNED_GATE |  75 |       0.04      |       0.4      | 0.360013  |  0.253333  | 0.466667  | 1.49012e-08 |                     1 |