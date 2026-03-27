# Qwen-14B Report

## Headline

- cluster-hard best frozen CASS variant: `CASS_TARGET_POSTPROCESS_PATCH`
- generic-hard best frozen CASS variant: `CASS_TARGET_POSTPROCESS_PATCH`
- cluster-hard best-vs-RAW: `-0.1594 [-0.2100, -0.1125]`
- cluster-hard best-vs-OPERATOR: `-0.1568 [-0.2025, -0.1125]`

| dataset     | surface              | method                                  |   n |   accuracy |   repair_rate |   corruption_rate |   net_gain |   avg_latency_s | model_name                |
|:------------|:---------------------|:----------------------------------------|----:|-----------:|--------------:|------------------:|-----------:|----------------:|:--------------------------|
| gsm8k_train | hard_cluster_main_r2 | ATLAS_FIELDWISE_SCHEMA_TO_CODE          | 400 |     0.5975 |        0.3525 |            0.0525 |     0.3    |        20.3302  | Qwen/Qwen2.5-14B-Instruct |
| gsm8k_train | hard_cluster_main_r2 | ATLAS_RG_ROLE_REPAIR_ONLY               | 400 |     0.67   |        0.4175 |            0.045  |     0.3725 |        15.8103  | Qwen/Qwen2.5-14B-Instruct |
| gsm8k_train | hard_cluster_main_r2 | CASS_CONSERVATIVE_GATE                  | 400 |     0.625  |        0.38   |            0.0525 |     0.3275 |        19.8946  | Qwen/Qwen2.5-14B-Instruct |
| gsm8k_train | hard_cluster_main_r2 | CASS_TARGET_POSTPROCESS_PATCH           | 400 |     0.705  |        0.4275 |            0.02   |     0.4075 |        14.3284  | Qwen/Qwen2.5-14B-Instruct |
| gsm8k_train | hard_cluster_main_r2 | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH | 400 |     0.625  |        0.38   |            0.0525 |     0.3275 |        19.8946  | Qwen/Qwen2.5-14B-Instruct |
| gsm8k_train | hard_cluster_main_r2 | KEEP                                    | 400 |     0.2975 |        0      |            0      |     0      |         0       | Qwen/Qwen2.5-14B-Instruct |
| gsm8k_train | hard_cluster_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE            | 400 |     0.8625 |        0.5725 |            0.0075 |     0.565  |         5.98133 | Qwen/Qwen2.5-14B-Instruct |
| gsm8k_train | hard_cluster_main_r2 | RAW_PYTHON                              | 400 |     0.865  |        0.585  |            0.0175 |     0.5675 |         3.50394 | Qwen/Qwen2.5-14B-Instruct |
| gsm8k_train | hard_generic_main_r2 | ATLAS_FIELDWISE_SCHEMA_TO_CODE          | 200 |     0.65   |        0.365  |            0.065  |     0.3    |        20.4357  | Qwen/Qwen2.5-14B-Instruct |
| gsm8k_train | hard_generic_main_r2 | ATLAS_RG_ROLE_REPAIR_ONLY               | 200 |     0.68   |        0.385  |            0.055  |     0.33   |        15.8672  | Qwen/Qwen2.5-14B-Instruct |
| gsm8k_train | hard_generic_main_r2 | CASS_CONSERVATIVE_GATE                  | 200 |     0.69   |        0.38   |            0.04   |     0.34   |        19.8452  | Qwen/Qwen2.5-14B-Instruct |
| gsm8k_train | hard_generic_main_r2 | CASS_TARGET_POSTPROCESS_PATCH           | 200 |     0.72   |        0.39   |            0.02   |     0.37   |        14.2749  | Qwen/Qwen2.5-14B-Instruct |
| gsm8k_train | hard_generic_main_r2 | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH | 200 |     0.69   |        0.38   |            0.04   |     0.34   |        19.8452  | Qwen/Qwen2.5-14B-Instruct |
| gsm8k_train | hard_generic_main_r2 | KEEP                                    | 200 |     0.35   |        0      |            0      |     0      |         0       | Qwen/Qwen2.5-14B-Instruct |
| gsm8k_train | hard_generic_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE            | 200 |     0.875  |        0.535  |            0.01   |     0.525  |         6.09127 | Qwen/Qwen2.5-14B-Instruct |
| gsm8k_train | hard_generic_main_r2 | RAW_PYTHON                              | 200 |     0.88   |        0.545  |            0.015  |     0.53   |         3.4781  | Qwen/Qwen2.5-14B-Instruct |

| surface              | base_method                  | alt_method                              |   n |   base_accuracy |   alt_accuracy |     delta |   ci_low |   ci_high |   mcnemar_p |   direction_favorable |
|:---------------------|:-----------------------------|:----------------------------------------|----:|----------------:|---------------:|----------:|---------:|----------:|------------:|----------------------:|
| hard_cluster_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE | ATLAS_FIELDWISE_SCHEMA_TO_CODE          | 400 |          0.8625 |         0.5975 | -0.26448  |  -0.3175 |   -0.2125 | 3.54431e-22 |                     0 |
| hard_cluster_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE | ATLAS_RG_ROLE_REPAIR_ONLY               | 400 |          0.8625 |         0.67   | -0.191053 |  -0.24   |   -0.1425 | 4.2635e-14  |                     0 |
| hard_cluster_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE | CASS_CONSERVATIVE_GATE                  | 400 |          0.8625 |         0.625  | -0.236183 |  -0.2875 |   -0.185  | 2.44514e-18 |                     0 |
| hard_cluster_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE | CASS_TARGET_POSTPROCESS_PATCH           | 400 |          0.8625 |         0.705  | -0.156771 |  -0.2025 |   -0.1125 | 5.4468e-12  |                     0 |
| hard_cluster_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH | 400 |          0.8625 |         0.625  | -0.236183 |  -0.2875 |   -0.185  | 2.44514e-18 |                     0 |
| hard_cluster_main_r2 | RAW_PYTHON                   | ATLAS_FIELDWISE_SCHEMA_TO_CODE          | 400 |          0.865  |         0.5975 | -0.267105 |  -0.32   |   -0.2125 | 1.24488e-21 |                     0 |
| hard_cluster_main_r2 | RAW_PYTHON                   | ATLAS_RG_ROLE_REPAIR_ONLY               | 400 |          0.865  |         0.67   | -0.193678 |  -0.2425 |   -0.1475 | 1.28977e-14 |                     0 |
| hard_cluster_main_r2 | RAW_PYTHON                   | CASS_CONSERVATIVE_GATE                  | 400 |          0.865  |         0.625  | -0.238808 |  -0.29   |   -0.1825 | 4.48879e-17 |                     0 |
| hard_cluster_main_r2 | RAW_PYTHON                   | CASS_TARGET_POSTPROCESS_PATCH           | 400 |          0.865  |         0.705  | -0.159396 |  -0.21   |   -0.1125 | 6.04117e-10 |                     0 |
| hard_cluster_main_r2 | RAW_PYTHON                   | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH | 400 |          0.865  |         0.625  | -0.238808 |  -0.29   |   -0.1825 | 4.48879e-17 |                     0 |
| hard_generic_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE | ATLAS_FIELDWISE_SCHEMA_TO_CODE          | 200 |          0.875  |         0.65   | -0.224222 |  -0.29   |   -0.16   | 2.13584e-10 |                     0 |
| hard_generic_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE | ATLAS_RG_ROLE_REPAIR_ONLY               | 200 |          0.875  |         0.68   | -0.19516  |  -0.26   |   -0.13   | 1.83236e-08 |                     0 |
| hard_generic_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE | CASS_CONSERVATIVE_GATE                  | 200 |          0.875  |         0.69   | -0.185265 |  -0.255  |   -0.115  | 2.36835e-07 |                     0 |
| hard_generic_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE | CASS_TARGET_POSTPROCESS_PATCH           | 200 |          0.875  |         0.72   | -0.15489  |  -0.22   |   -0.085  | 2.24756e-05 |                     0 |
| hard_generic_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH | 200 |          0.875  |         0.69   | -0.185265 |  -0.255  |   -0.115  | 2.36835e-07 |                     0 |
| hard_generic_main_r2 | RAW_PYTHON                   | ATLAS_FIELDWISE_SCHEMA_TO_CODE          | 200 |          0.88   |         0.65   | -0.22927  |  -0.3    |   -0.16   | 3.54222e-09 |                     0 |
| hard_generic_main_r2 | RAW_PYTHON                   | ATLAS_RG_ROLE_REPAIR_ONLY               | 200 |          0.88   |         0.68   | -0.200208 |  -0.27   |   -0.13   | 8.9594e-08  |                     0 |
| hard_generic_main_r2 | RAW_PYTHON                   | CASS_CONSERVATIVE_GATE                  | 200 |          0.88   |         0.69   | -0.190313 |  -0.26   |   -0.12   | 2.57157e-07 |                     0 |
| hard_generic_main_r2 | RAW_PYTHON                   | CASS_TARGET_POSTPROCESS_PATCH           | 200 |          0.88   |         0.72   | -0.159938 |  -0.225  |   -0.095  | 9.06327e-06 |                     0 |
| hard_generic_main_r2 | RAW_PYTHON                   | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH | 200 |          0.88   |         0.69   | -0.190313 |  -0.26   |   -0.12   | 2.57157e-07 |                     0 |