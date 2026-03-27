# Scale Synthesis

## Family-scale ranking

| model_family   | model_name                          | surface              | method                                  |   rank |   accuracy |   net_gain |   avg_latency_s |
|:---------------|:------------------------------------|:---------------------|:----------------------------------------|-------:|-----------:|-----------:|----------------:|
| Granite-8B     | ibm-granite/granite-3.1-8b-instruct | hard_cluster_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE            |      1 |  0.7325    |  0.6075    |         4.79996 |
| Granite-8B     | ibm-granite/granite-3.1-8b-instruct | hard_cluster_main_r2 | RAW_PYTHON                              |      2 |  0.6075    |  0.4825    |         3.07245 |
| Granite-8B     | ibm-granite/granite-3.1-8b-instruct | hard_cluster_main_r2 | CASS_TARGET_POSTPROCESS_PATCH           |      3 |  0.5075    |  0.3825    |         9.75801 |
| Granite-8B     | ibm-granite/granite-3.1-8b-instruct | hard_cluster_main_r2 | ATLAS_RG_ROLE_REPAIR_ONLY               |      4 |  0.2825    |  0.1575    |        10.4164  |
| Granite-8B     | ibm-granite/granite-3.1-8b-instruct | hard_cluster_main_r2 | ATLAS_FIELDWISE_SCHEMA_TO_CODE          |      5 |  0.2225    |  0.0975    |        13.0033  |
| Granite-8B     | ibm-granite/granite-3.1-8b-instruct | hard_cluster_main_r2 | CASS_CONSERVATIVE_GATE                  |      6 |  0.195     |  0.07      |        12.8236  |
| Granite-8B     | ibm-granite/granite-3.1-8b-instruct | hard_cluster_main_r2 | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH |      7 |  0.195     |  0.07      |        12.8236  |
| Granite-8B     | ibm-granite/granite-3.1-8b-instruct | hard_cluster_main_r2 | KEEP                                    |      8 |  0.125     |  0         |         0       |
| Granite-8B     | ibm-granite/granite-3.1-8b-instruct | hard_generic_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE            |      1 |  0.765     |  0.56      |         4.3125  |
| Granite-8B     | ibm-granite/granite-3.1-8b-instruct | hard_generic_main_r2 | RAW_PYTHON                              |      2 |  0.655     |  0.45      |         2.81624 |
| Granite-8B     | ibm-granite/granite-3.1-8b-instruct | hard_generic_main_r2 | CASS_TARGET_POSTPROCESS_PATCH           |      3 |  0.64      |  0.435     |         9.06521 |
| Granite-8B     | ibm-granite/granite-3.1-8b-instruct | hard_generic_main_r2 | ATLAS_RG_ROLE_REPAIR_ONLY               |      4 |  0.325     |  0.12      |         9.67933 |
| Granite-8B     | ibm-granite/granite-3.1-8b-instruct | hard_generic_main_r2 | CASS_CONSERVATIVE_GATE                  |      5 |  0.305     |  0.1       |        11.9152  |
| Granite-8B     | ibm-granite/granite-3.1-8b-instruct | hard_generic_main_r2 | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH |      6 |  0.305     |  0.1       |        11.9152  |
| Granite-8B     | ibm-granite/granite-3.1-8b-instruct | hard_generic_main_r2 | ATLAS_FIELDWISE_SCHEMA_TO_CODE          |      7 |  0.24      |  0.035     |        12.1169  |
| Granite-8B     | ibm-granite/granite-3.1-8b-instruct | hard_generic_main_r2 | KEEP                                    |      8 |  0.205     |  0         |         0       |
| Mistral-7B     | mistralai/Mistral-7B-Instruct-v0.3  | hard_cluster_main_r2 | CASS_TARGET_POSTPROCESS_PATCH           |      1 |  0.358416  |  0.29637   |         6.70991 |
| Mistral-7B     | mistralai/Mistral-7B-Instruct-v0.3  | hard_cluster_main_r2 | CASS_CONSERVATIVE_GATE                  |      2 |  0.358416  |  0.29637   |         8.9478  |
| Mistral-7B     | mistralai/Mistral-7B-Instruct-v0.3  | hard_cluster_main_r2 | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH |      3 |  0.358416  |  0.29637   |         8.9478  |
| Mistral-7B     | mistralai/Mistral-7B-Instruct-v0.3  | hard_cluster_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE            |      4 |  0.331353  |  0.269307  |         2.80575 |
| Mistral-7B     | mistralai/Mistral-7B-Instruct-v0.3  | hard_cluster_main_r2 | RAW_PYTHON                              |      5 |  0.209901  |  0.147855  |         2.42918 |
| Mistral-7B     | mistralai/Mistral-7B-Instruct-v0.3  | hard_cluster_main_r2 | ATLAS_FIELDWISE_SCHEMA_TO_CODE          |      6 |  0.173597  |  0.111551  |         9.72576 |
| Mistral-7B     | mistralai/Mistral-7B-Instruct-v0.3  | hard_cluster_main_r2 | ATLAS_RG_ROLE_REPAIR_ONLY               |      7 |  0.153795  |  0.0917492 |         6.91266 |
| Mistral-7B     | mistralai/Mistral-7B-Instruct-v0.3  | hard_cluster_main_r2 | KEEP                                    |      8 |  0.0620462 |  0         |         0       |
| Mistral-7B     | mistralai/Mistral-7B-Instruct-v0.3  | hard_generic_main_r2 | CASS_TARGET_POSTPROCESS_PATCH           |      1 |  0.42029   |  0.360248  |         6.97602 |
| Mistral-7B     | mistralai/Mistral-7B-Instruct-v0.3  | hard_generic_main_r2 | CASS_CONSERVATIVE_GATE                  |      2 |  0.42029   |  0.360248  |         9.24735 |
| Mistral-7B     | mistralai/Mistral-7B-Instruct-v0.3  | hard_generic_main_r2 | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH |      3 |  0.42029   |  0.360248  |         9.24735 |
| Mistral-7B     | mistralai/Mistral-7B-Instruct-v0.3  | hard_generic_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE            |      4 |  0.391304  |  0.331263  |         2.86292 |
| Mistral-7B     | mistralai/Mistral-7B-Instruct-v0.3  | hard_generic_main_r2 | RAW_PYTHON                              |      5 |  0.200828  |  0.140787  |         2.45843 |
| Mistral-7B     | mistralai/Mistral-7B-Instruct-v0.3  | hard_generic_main_r2 | ATLAS_FIELDWISE_SCHEMA_TO_CODE          |      6 |  0.178054  |  0.118012  |        10.0934  |
| Mistral-7B     | mistralai/Mistral-7B-Instruct-v0.3  | hard_generic_main_r2 | ATLAS_RG_ROLE_REPAIR_ONLY               |      7 |  0.15942   |  0.0993789 |         7.14991 |
| Mistral-7B     | mistralai/Mistral-7B-Instruct-v0.3  | hard_generic_main_r2 | KEEP                                    |      8 |  0.0600414 |  0         |         0       |
| Qwen-14B       | Qwen/Qwen2.5-14B-Instruct           | hard_cluster_main_r2 | RAW_PYTHON                              |      1 |  0.865     |  0.5675    |         3.50394 |
| Qwen-14B       | Qwen/Qwen2.5-14B-Instruct           | hard_cluster_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE            |      2 |  0.8625    |  0.565     |         5.98133 |
| Qwen-14B       | Qwen/Qwen2.5-14B-Instruct           | hard_cluster_main_r2 | CASS_TARGET_POSTPROCESS_PATCH           |      3 |  0.705     |  0.4075    |        14.3284  |
| Qwen-14B       | Qwen/Qwen2.5-14B-Instruct           | hard_cluster_main_r2 | ATLAS_RG_ROLE_REPAIR_ONLY               |      4 |  0.67      |  0.3725    |        15.8103  |
| Qwen-14B       | Qwen/Qwen2.5-14B-Instruct           | hard_cluster_main_r2 | CASS_CONSERVATIVE_GATE                  |      5 |  0.625     |  0.3275    |        19.8946  |
| Qwen-14B       | Qwen/Qwen2.5-14B-Instruct           | hard_cluster_main_r2 | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH |      6 |  0.625     |  0.3275    |        19.8946  |
| Qwen-14B       | Qwen/Qwen2.5-14B-Instruct           | hard_cluster_main_r2 | ATLAS_FIELDWISE_SCHEMA_TO_CODE          |      7 |  0.5975    |  0.3       |        20.3302  |
| Qwen-14B       | Qwen/Qwen2.5-14B-Instruct           | hard_cluster_main_r2 | KEEP                                    |      8 |  0.2975    |  0         |         0       |
| Qwen-14B       | Qwen/Qwen2.5-14B-Instruct           | hard_generic_main_r2 | RAW_PYTHON                              |      1 |  0.88      |  0.53      |         3.4781  |
| Qwen-14B       | Qwen/Qwen2.5-14B-Instruct           | hard_generic_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE            |      2 |  0.875     |  0.525     |         6.09127 |
| Qwen-14B       | Qwen/Qwen2.5-14B-Instruct           | hard_generic_main_r2 | CASS_TARGET_POSTPROCESS_PATCH           |      3 |  0.72      |  0.37      |        14.2749  |
| Qwen-14B       | Qwen/Qwen2.5-14B-Instruct           | hard_generic_main_r2 | CASS_CONSERVATIVE_GATE                  |      4 |  0.69      |  0.34      |        19.8452  |
| Qwen-14B       | Qwen/Qwen2.5-14B-Instruct           | hard_generic_main_r2 | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH |      5 |  0.69      |  0.34      |        19.8452  |
| Qwen-14B       | Qwen/Qwen2.5-14B-Instruct           | hard_generic_main_r2 | ATLAS_RG_ROLE_REPAIR_ONLY               |      6 |  0.68      |  0.33      |        15.8672  |
| Qwen-14B       | Qwen/Qwen2.5-14B-Instruct           | hard_generic_main_r2 | ATLAS_FIELDWISE_SCHEMA_TO_CODE          |      7 |  0.65      |  0.3       |        20.4357  |
| Qwen-14B       | Qwen/Qwen2.5-14B-Instruct           | hard_generic_main_r2 | KEEP                                    |      8 |  0.35      |  0         |         0       |
| Qwen-7B        | Qwen-7B                             | hard_cluster_main_r2 | CASS_CONSERVATIVE_GATE                  |      1 |  0.746535  |  0.481188  |         6.83312 |
| Qwen-7B        | Qwen-7B                             | hard_cluster_main_r2 | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH |      2 |  0.746535  |  0.481188  |         6.83312 |
| Qwen-7B        | Qwen-7B                             | hard_cluster_main_r2 | CASS_TARGET_POSTPROCESS_PATCH           |      3 |  0.735314  |  0.469967  |         4.31073 |
| Qwen-7B        | Qwen-7B                             | hard_cluster_main_r2 | ATLAS_RG_ROLE_REPAIR_ONLY               |      4 |  0.731353  |  0.466007  |         4.85073 |
| Qwen-7B        | Qwen-7B                             | hard_cluster_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE            |      5 |  0.726073  |  0.460726  |         1.88746 |
| Qwen-7B        | Qwen-7B                             | hard_cluster_main_r2 | ATLAS_FIELDWISE_SCHEMA_TO_CODE          |      6 |  0.716172  |  0.450825  |         6.466   |
| Qwen-7B        | Qwen-7B                             | hard_cluster_main_r2 | RAW_PYTHON                              |      7 |  0.70495   |  0.439604  |         1.36086 |
| Qwen-7B        | Qwen-7B                             | hard_cluster_main_r2 | KEEP                                    |      8 |  0.265347  |  0         |         0       |
| Qwen-7B        | Qwen-7B                             | hard_generic_main_r2 | CASS_CONSERVATIVE_GATE                  |      1 |  0.797101  |  0.482402  |         6.79276 |
| Qwen-7B        | Qwen-7B                             | hard_generic_main_r2 | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH |      2 |  0.797101  |  0.482402  |         6.79276 |
| Qwen-7B        | Qwen-7B                             | hard_generic_main_r2 | CASS_TARGET_POSTPROCESS_PATCH           |      3 |  0.755694  |  0.440994  |         4.24169 |
| Qwen-7B        | Qwen-7B                             | hard_generic_main_r2 | ATLAS_RG_ROLE_REPAIR_ONLY               |      4 |  0.755694  |  0.440994  |         4.90076 |
| Qwen-7B        | Qwen-7B                             | hard_generic_main_r2 | OPERATOR_SCHEMA_TO_CODE_BASE            |      5 |  0.751553  |  0.436853  |         1.86257 |
| Qwen-7B        | Qwen-7B                             | hard_generic_main_r2 | RAW_PYTHON                              |      6 |  0.73499   |  0.42029   |         1.36022 |
| Qwen-7B        | Qwen-7B                             | hard_generic_main_r2 | ATLAS_FIELDWISE_SCHEMA_TO_CODE          |      7 |  0.718427  |  0.403727  |         6.49582 |
| Qwen-7B        | Qwen-7B                             | hard_generic_main_r2 | KEEP                                    |      8 |  0.3147    |  0         |         0       |

## Portable-core table

| model_family   | model_name                          | surface              | method                                  |   rank |   accuracy |   net_gain |   avg_latency_s |   portable_core_family_win |
|:---------------|:------------------------------------|:---------------------|:----------------------------------------|-------:|-----------:|-----------:|----------------:|---------------------------:|
| Granite-8B     | ibm-granite/granite-3.1-8b-instruct | hard_cluster_main_r2 | CASS_TARGET_POSTPROCESS_PATCH           |      3 |   0.5075   |  0.3825    |         9.75801 |                          1 |
| Granite-8B     | ibm-granite/granite-3.1-8b-instruct | hard_cluster_main_r2 | ATLAS_RG_ROLE_REPAIR_ONLY               |      4 |   0.2825   |  0.1575    |        10.4164  |                          0 |
| Granite-8B     | ibm-granite/granite-3.1-8b-instruct | hard_cluster_main_r2 | CASS_CONSERVATIVE_GATE                  |      6 |   0.195    |  0.07      |        12.8236  |                          0 |
| Granite-8B     | ibm-granite/granite-3.1-8b-instruct | hard_cluster_main_r2 | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH |      7 |   0.195    |  0.07      |        12.8236  |                          0 |
| Granite-8B     | ibm-granite/granite-3.1-8b-instruct | hard_generic_main_r2 | CASS_TARGET_POSTPROCESS_PATCH           |      3 |   0.64     |  0.435     |         9.06521 |                          1 |
| Granite-8B     | ibm-granite/granite-3.1-8b-instruct | hard_generic_main_r2 | ATLAS_RG_ROLE_REPAIR_ONLY               |      4 |   0.325    |  0.12      |         9.67933 |                          0 |
| Granite-8B     | ibm-granite/granite-3.1-8b-instruct | hard_generic_main_r2 | CASS_CONSERVATIVE_GATE                  |      5 |   0.305    |  0.1       |        11.9152  |                          0 |
| Granite-8B     | ibm-granite/granite-3.1-8b-instruct | hard_generic_main_r2 | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH |      6 |   0.305    |  0.1       |        11.9152  |                          0 |
| Mistral-7B     | mistralai/Mistral-7B-Instruct-v0.3  | hard_cluster_main_r2 | CASS_TARGET_POSTPROCESS_PATCH           |      1 |   0.358416 |  0.29637   |         6.70991 |                          1 |
| Mistral-7B     | mistralai/Mistral-7B-Instruct-v0.3  | hard_cluster_main_r2 | CASS_CONSERVATIVE_GATE                  |      2 |   0.358416 |  0.29637   |         8.9478  |                          0 |
| Mistral-7B     | mistralai/Mistral-7B-Instruct-v0.3  | hard_cluster_main_r2 | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH |      3 |   0.358416 |  0.29637   |         8.9478  |                          0 |
| Mistral-7B     | mistralai/Mistral-7B-Instruct-v0.3  | hard_cluster_main_r2 | ATLAS_RG_ROLE_REPAIR_ONLY               |      7 |   0.153795 |  0.0917492 |         6.91266 |                          0 |
| Mistral-7B     | mistralai/Mistral-7B-Instruct-v0.3  | hard_generic_main_r2 | CASS_TARGET_POSTPROCESS_PATCH           |      1 |   0.42029  |  0.360248  |         6.97602 |                          1 |
| Mistral-7B     | mistralai/Mistral-7B-Instruct-v0.3  | hard_generic_main_r2 | CASS_CONSERVATIVE_GATE                  |      2 |   0.42029  |  0.360248  |         9.24735 |                          0 |
| Mistral-7B     | mistralai/Mistral-7B-Instruct-v0.3  | hard_generic_main_r2 | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH |      3 |   0.42029  |  0.360248  |         9.24735 |                          0 |
| Mistral-7B     | mistralai/Mistral-7B-Instruct-v0.3  | hard_generic_main_r2 | ATLAS_RG_ROLE_REPAIR_ONLY               |      7 |   0.15942  |  0.0993789 |         7.14991 |                          0 |
| Qwen-14B       | Qwen/Qwen2.5-14B-Instruct           | hard_cluster_main_r2 | CASS_TARGET_POSTPROCESS_PATCH           |      3 |   0.705    |  0.4075    |        14.3284  |                          1 |
| Qwen-14B       | Qwen/Qwen2.5-14B-Instruct           | hard_cluster_main_r2 | ATLAS_RG_ROLE_REPAIR_ONLY               |      4 |   0.67     |  0.3725    |        15.8103  |                          0 |
| Qwen-14B       | Qwen/Qwen2.5-14B-Instruct           | hard_cluster_main_r2 | CASS_CONSERVATIVE_GATE                  |      5 |   0.625    |  0.3275    |        19.8946  |                          0 |
| Qwen-14B       | Qwen/Qwen2.5-14B-Instruct           | hard_cluster_main_r2 | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH |      6 |   0.625    |  0.3275    |        19.8946  |                          0 |
| Qwen-14B       | Qwen/Qwen2.5-14B-Instruct           | hard_generic_main_r2 | CASS_TARGET_POSTPROCESS_PATCH           |      3 |   0.72     |  0.37      |        14.2749  |                          1 |
| Qwen-14B       | Qwen/Qwen2.5-14B-Instruct           | hard_generic_main_r2 | CASS_CONSERVATIVE_GATE                  |      4 |   0.69     |  0.34      |        19.8452  |                          0 |
| Qwen-14B       | Qwen/Qwen2.5-14B-Instruct           | hard_generic_main_r2 | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH |      5 |   0.69     |  0.34      |        19.8452  |                          0 |
| Qwen-14B       | Qwen/Qwen2.5-14B-Instruct           | hard_generic_main_r2 | ATLAS_RG_ROLE_REPAIR_ONLY               |      6 |   0.68     |  0.33      |        15.8672  |                          0 |
| Qwen-7B        | Qwen-7B                             | hard_cluster_main_r2 | CASS_CONSERVATIVE_GATE                  |      1 |   0.746535 |  0.481188  |         6.83312 |                          1 |
| Qwen-7B        | Qwen-7B                             | hard_cluster_main_r2 | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH |      2 |   0.746535 |  0.481188  |         6.83312 |                          0 |
| Qwen-7B        | Qwen-7B                             | hard_cluster_main_r2 | CASS_TARGET_POSTPROCESS_PATCH           |      3 |   0.735314 |  0.469967  |         4.31073 |                          0 |
| Qwen-7B        | Qwen-7B                             | hard_cluster_main_r2 | ATLAS_RG_ROLE_REPAIR_ONLY               |      4 |   0.731353 |  0.466007  |         4.85073 |                          0 |
| Qwen-7B        | Qwen-7B                             | hard_generic_main_r2 | CASS_CONSERVATIVE_GATE                  |      1 |   0.797101 |  0.482402  |         6.79276 |                          1 |
| Qwen-7B        | Qwen-7B                             | hard_generic_main_r2 | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH |      2 |   0.797101 |  0.482402  |         6.79276 |                          0 |
| Qwen-7B        | Qwen-7B                             | hard_generic_main_r2 | CASS_TARGET_POSTPROCESS_PATCH           |      3 |   0.755694 |  0.440994  |         4.24169 |                          0 |
| Qwen-7B        | Qwen-7B                             | hard_generic_main_r2 | ATLAS_RG_ROLE_REPAIR_ONLY               |      4 |   0.755694 |  0.440994  |         4.90076 |                          0 |