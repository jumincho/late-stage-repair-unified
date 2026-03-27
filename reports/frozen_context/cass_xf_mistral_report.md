# CASS-XF Mistral Report

## Headline

- replicated model family: `mistralai/Mistral-7B-Instruct-v0.3`
- cluster-hard best frozen CASS variant: `CASS_TARGET_POSTPROCESS_PATCH`
- generic-hard best frozen CASS variant: `CASS_TARGET_POSTPROCESS_PATCH`
- cluster-hard directional win vs `RAW_PYTHON`: `1`
- cluster-hard directional win vs `OPERATOR_SCHEMA_TO_CODE_BASE`: `1`

## Mistral reduced replication summary

| dataset     | surface              | method                                  |   n |   accuracy |   repair_rate |   corruption_rate |   net_gain |   avg_latency_s | model_name                         |
|:------------|:---------------------|:----------------------------------------|----:|-----------:|--------------:|------------------:|-----------:|----------------:|:-----------------------------------|
| gsm8k_train | hard_cluster_main_r2 | ATLAS_FIELDWISE_SCHEMA_TO_CODE          | 400 |     0.1975 |        0.135  |            0.0075 |     0.1275 |         9.60522 | mistralai/Mistral-7B-Instruct-v0.3 |
| gsm8k_train | hard_cluster_main_r2 | ATLAS_RG_ROLE_REPAIR_ONLY               | 400 |     0.1775 |        0.115  |            0.0075 |     0.1075 |         6.84063 | mistralai/Mistral-7B-Instruct-v0.3 |
| gsm8k_train | hard_cluster_main_r2 | CASS_CONSERVATIVE_GATE                  | 400 |     0.3325 |        0.2875 |            0.025  |     0.2625 |         8.84677 | mistralai/Mistral-7B-Instruct-v0.3 |
| gsm8k_train | hard_cluster_main_r2 | CASS_TARGET_POSTPROCESS_PATCH           | 400 |     0.3325 |        0.2875 |            0.025  |     0.2625 |         6.68413 | mistralai/Mistral-7B-Instruct-v0.3 |
| gsm8k_train | hard_cluster_main_r2 | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH | 400 |     0.3325 |        0.2875 |            0.025  |     0.2625 |         8.84677 | mistralai/Mistral-7B-Instruct-v0.3 |
| gsm8k_train | hard_cluster_main_r2 | KEEP                                    | 400 |     0.07   |        0      |            0      |     0      |         0       | mistralai/Mistral-7B-Instruct-v0.3 |
| gsm8k_train | hard_cluster_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE            | 400 |     0.3175 |        0.265  |            0.0175 |     0.2475 |         2.78473 | mistralai/Mistral-7B-Instruct-v0.3 |
| gsm8k_train | hard_cluster_main_r2 | RAW_PYTHON                              | 400 |     0.2075 |        0.15   |            0.0125 |     0.1375 |         2.41062 | mistralai/Mistral-7B-Instruct-v0.3 |
| gsm8k_train | hard_generic_main_r2 | ATLAS_FIELDWISE_SCHEMA_TO_CODE          | 200 |     0.175  |        0.135  |            0.015  |     0.12   |        10.0878  | mistralai/Mistral-7B-Instruct-v0.3 |
| gsm8k_train | hard_generic_main_r2 | ATLAS_RG_ROLE_REPAIR_ONLY               | 200 |     0.165  |        0.11   |            0      |     0.11   |         7.21474 | mistralai/Mistral-7B-Instruct-v0.3 |
| gsm8k_train | hard_generic_main_r2 | CASS_CONSERVATIVE_GATE                  | 200 |     0.415  |        0.38   |            0.02   |     0.36   |         9.2187  | mistralai/Mistral-7B-Instruct-v0.3 |
| gsm8k_train | hard_generic_main_r2 | CASS_TARGET_POSTPROCESS_PATCH           | 200 |     0.415  |        0.38   |            0.02   |     0.36   |         6.98537 | mistralai/Mistral-7B-Instruct-v0.3 |
| gsm8k_train | hard_generic_main_r2 | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH | 200 |     0.415  |        0.38   |            0.02   |     0.36   |         9.2187  | mistralai/Mistral-7B-Instruct-v0.3 |
| gsm8k_train | hard_generic_main_r2 | KEEP                                    | 200 |     0.055  |        0      |            0      |     0      |         0       | mistralai/Mistral-7B-Instruct-v0.3 |
| gsm8k_train | hard_generic_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE            | 200 |     0.385  |        0.345  |            0.015  |     0.33   |         2.88642 | mistralai/Mistral-7B-Instruct-v0.3 |
| gsm8k_train | hard_generic_main_r2 | RAW_PYTHON                              | 200 |     0.18   |        0.135  |            0.01   |     0.125  |         2.46933 | mistralai/Mistral-7B-Instruct-v0.3 |

## Pairwise focus

| surface              | base_method                  | alt_method                              |   n |   base_accuracy |   alt_accuracy |       delta |   ci_low |   ci_high |   mcnemar_p |   direction_favorable |
|:---------------------|:-----------------------------|:----------------------------------------|----:|----------------:|---------------:|------------:|---------:|----------:|------------:|----------------------:|
| hard_cluster_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE | ATLAS_FIELDWISE_SCHEMA_TO_CODE          | 400 |          0.3175 |         0.1975 | -0.11994    |  -0.165  |   -0.0725 | 5.34814e-07 |                     0 |
| hard_cluster_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE | ATLAS_RG_ROLE_REPAIR_ONLY               | 400 |          0.3175 |         0.1775 | -0.140908   |  -0.1825 |   -0.1    | 1.19152e-09 |                     0 |
| hard_cluster_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE | CASS_CONSERVATIVE_GATE                  | 400 |          0.3175 |         0.3325 |  0.01446    |  -0.0225 |    0.0525 | 0.525773    |                     1 |
| hard_cluster_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE | CASS_TARGET_POSTPROCESS_PATCH           | 400 |          0.3175 |         0.3325 |  0.01446    |  -0.0225 |    0.0525 | 0.525773    |                     1 |
| hard_cluster_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH | 400 |          0.3175 |         0.3325 |  0.01446    |  -0.0225 |    0.0525 | 0.525773    |                     1 |
| hard_cluster_main_r2 | RAW_PYTHON                   | ATLAS_FIELDWISE_SCHEMA_TO_CODE          | 400 |          0.2075 |         0.1975 | -0.00999125 |  -0.0525 |    0.03   | 0.727547    |                     0 |
| hard_cluster_main_r2 | RAW_PYTHON                   | ATLAS_RG_ROLE_REPAIR_ONLY               | 400 |          0.2075 |         0.1775 | -0.0309588  |  -0.0675 |    0.0025 | 0.140895    |                     0 |
| hard_cluster_main_r2 | RAW_PYTHON                   | CASS_CONSERVATIVE_GATE                  | 400 |          0.2075 |         0.3325 |  0.124409   |   0.08   |    0.1675 | 1.61681e-07 |                     1 |
| hard_cluster_main_r2 | RAW_PYTHON                   | CASS_TARGET_POSTPROCESS_PATCH           | 400 |          0.2075 |         0.3325 |  0.124409   |   0.08   |    0.1675 | 1.61681e-07 |                     1 |
| hard_cluster_main_r2 | RAW_PYTHON                   | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH | 400 |          0.2075 |         0.3325 |  0.124409   |   0.08   |    0.1675 | 1.61681e-07 |                     1 |
| hard_generic_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE | ATLAS_FIELDWISE_SCHEMA_TO_CODE          | 200 |          0.385  |         0.175  | -0.20993    |  -0.28   |   -0.14   | 3.08504e-08 |                     0 |
| hard_generic_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE | ATLAS_RG_ROLE_REPAIR_ONLY               | 200 |          0.385  |         0.165  | -0.220017   |  -0.29   |   -0.15   | 5.20569e-09 |                     0 |
| hard_generic_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE | CASS_CONSERVATIVE_GATE                  | 200 |          0.385  |         0.415  |  0.0299425  |  -0.03   |    0.09   | 0.417692    |                     1 |
| hard_generic_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE | CASS_TARGET_POSTPROCESS_PATCH           | 200 |          0.385  |         0.415  |  0.0299425  |  -0.03   |    0.09   | 0.417692    |                     1 |
| hard_generic_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH | 200 |          0.385  |         0.415  |  0.0299425  |  -0.03   |    0.09   | 0.417692    |                     1 |
| hard_generic_main_r2 | RAW_PYTHON                   | ATLAS_FIELDWISE_SCHEMA_TO_CODE          | 200 |          0.18   |         0.175  | -0.0050325  |  -0.06   |    0.05   | 1           |                     0 |
| hard_generic_main_r2 | RAW_PYTHON                   | ATLAS_RG_ROLE_REPAIR_ONLY               | 200 |          0.18   |         0.165  | -0.01512    |  -0.07   |    0.04   | 0.7201      |                     0 |
| hard_generic_main_r2 | RAW_PYTHON                   | CASS_CONSERVATIVE_GATE                  | 200 |          0.18   |         0.415  |  0.23484    |   0.16   |    0.31   | 4.0421e-09  |                     1 |
| hard_generic_main_r2 | RAW_PYTHON                   | CASS_TARGET_POSTPROCESS_PATCH           | 200 |          0.18   |         0.415  |  0.23484    |   0.16   |    0.31   | 4.0421e-09  |                     1 |
| hard_generic_main_r2 | RAW_PYTHON                   | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH | 200 |          0.18   |         0.415  |  0.23484    |   0.16   |    0.31   | 4.0421e-09  |                     1 |