# Portable Core Report

- family-surface win counts: `{'POSTPROCESS_ONLY_PATCH': 4, 'TARGET_PLUS_POSTPROCESS_PATCH': 2, 'CASS_TARGET_POSTPROCESS_PATCH': 1, 'TARGET_ONLY_PATCH': 1}`

| model_family   | model_name   | surface              | method                                  |   rank |   accuracy |   net_gain |   avg_latency_s |
|:---------------|:-------------|:---------------------|:----------------------------------------|-------:|-----------:|-----------:|----------------:|
| Granite-8B     | Granite-8B   | hard_cluster_main_r2 | POSTPROCESS_ONLY_PATCH                  |      1 |   0.7075   |   0.5825   |         4.67873 |
| Granite-8B     | Granite-8B   | hard_cluster_main_r2 | DISCRETIZATION_ONLY_PATCH               |      2 |   0.7025   |   0.5775   |         4.62414 |
| Granite-8B     | Granite-8B   | hard_cluster_main_r2 | TARGET_ONLY_PATCH                       |      3 |   0.515    |   0.39     |         4.94418 |
| Granite-8B     | Granite-8B   | hard_cluster_main_r2 | CASS_TARGET_POSTPROCESS_PATCH           |      4 |   0.5075   |   0.3825   |         9.75801 |
| Granite-8B     | Granite-8B   | hard_cluster_main_r2 | TARGET_PLUS_POSTPROCESS_PATCH           |      5 |   0.5025   |   0.3775   |         4.96003 |
| Granite-8B     | Granite-8B   | hard_cluster_main_r2 | ROLE_ONLY_REPLAY                        |      6 |   0.305    |   0.18     |         5.0868  |
| Granite-8B     | Granite-8B   | hard_cluster_main_r2 | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH |      7 |   0.195    |   0.07     |        12.8236  |
| Granite-8B     | Granite-8B   | hard_generic_main_r2 | POSTPROCESS_ONLY_PATCH                  |      1 |   0.715    |   0.51     |         4.63205 |
| Granite-8B     | Granite-8B   | hard_generic_main_r2 | DISCRETIZATION_ONLY_PATCH               |      2 |   0.71     |   0.505    |         4.56832 |
| Granite-8B     | Granite-8B   | hard_generic_main_r2 | CASS_TARGET_POSTPROCESS_PATCH           |      3 |   0.64     |   0.435    |         9.06521 |
| Granite-8B     | Granite-8B   | hard_generic_main_r2 | TARGET_PLUS_POSTPROCESS_PATCH           |      4 |   0.635    |   0.43     |         4.8127  |
| Granite-8B     | Granite-8B   | hard_generic_main_r2 | TARGET_ONLY_PATCH                       |      5 |   0.625    |   0.42     |         4.78767 |
| Granite-8B     | Granite-8B   | hard_generic_main_r2 | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH |      6 |   0.305    |   0.1      |        11.9152  |
| Granite-8B     | Granite-8B   | hard_generic_main_r2 | ROLE_ONLY_REPLAY                        |      7 |   0.295    |   0.09     |         4.91421 |
| Mistral-7B     | Mistral-7B   | hard_cluster_main_r2 | TARGET_PLUS_POSTPROCESS_PATCH           |      1 |   0.3325   |   0.2625   |         2.74153 |
| Mistral-7B     | Mistral-7B   | hard_cluster_main_r2 | TARGET_ONLY_PATCH                       |      2 |   0.3325   |   0.2625   |         2.7506  |
| Mistral-7B     | Mistral-7B   | hard_cluster_main_r2 | CASS_TARGET_POSTPROCESS_PATCH           |      3 |   0.3325   |   0.2625   |         6.68413 |
| Mistral-7B     | Mistral-7B   | hard_cluster_main_r2 | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH |      4 |   0.3325   |   0.2625   |         8.84677 |
| Mistral-7B     | Mistral-7B   | hard_cluster_main_r2 | POSTPROCESS_ONLY_PATCH                  |      5 |   0.3175   |   0.2475   |         2.63034 |
| Mistral-7B     | Mistral-7B   | hard_cluster_main_r2 | DISCRETIZATION_ONLY_PATCH               |      6 |   0.3175   |   0.2475   |         2.6342  |
| Mistral-7B     | Mistral-7B   | hard_cluster_main_r2 | ROLE_ONLY_REPLAY                        |      7 |   0.1675   |   0.0975   |         2.92232 |
| Mistral-7B     | Mistral-7B   | hard_generic_main_r2 | TARGET_PLUS_POSTPROCESS_PATCH           |      1 |   0.415    |   0.36     |         2.652   |
| Mistral-7B     | Mistral-7B   | hard_generic_main_r2 | TARGET_ONLY_PATCH                       |      2 |   0.415    |   0.36     |         2.67164 |
| Mistral-7B     | Mistral-7B   | hard_generic_main_r2 | CASS_TARGET_POSTPROCESS_PATCH           |      3 |   0.415    |   0.36     |         6.98537 |
| Mistral-7B     | Mistral-7B   | hard_generic_main_r2 | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH |      4 |   0.415    |   0.36     |         9.2187  |
| Mistral-7B     | Mistral-7B   | hard_generic_main_r2 | DISCRETIZATION_ONLY_PATCH               |      5 |   0.405    |   0.35     |         2.47514 |
| Mistral-7B     | Mistral-7B   | hard_generic_main_r2 | POSTPROCESS_ONLY_PATCH                  |      6 |   0.405    |   0.35     |         2.47719 |
| Mistral-7B     | Mistral-7B   | hard_generic_main_r2 | ROLE_ONLY_REPLAY                        |      7 |   0.18     |   0.125    |         2.77976 |
| Qwen-14B       | Qwen-14B     | hard_cluster_main_r2 | POSTPROCESS_ONLY_PATCH                  |      1 |   0.8425   |   0.545    |         6.3053  |
| Qwen-14B       | Qwen-14B     | hard_cluster_main_r2 | DISCRETIZATION_ONLY_PATCH               |      2 |   0.825    |   0.5275   |         6.26441 |
| Qwen-14B       | Qwen-14B     | hard_cluster_main_r2 | TARGET_PLUS_POSTPROCESS_PATCH           |      3 |   0.72     |   0.4225   |         7.98436 |
| Qwen-14B       | Qwen-14B     | hard_cluster_main_r2 | TARGET_ONLY_PATCH                       |      4 |   0.7075   |   0.41     |         7.85607 |
| Qwen-14B       | Qwen-14B     | hard_cluster_main_r2 | CASS_TARGET_POSTPROCESS_PATCH           |      5 |   0.705    |   0.4075   |        14.3284  |
| Qwen-14B       | Qwen-14B     | hard_cluster_main_r2 | ROLE_ONLY_REPLAY                        |      6 |   0.68     |   0.3825   |         7.84137 |
| Qwen-14B       | Qwen-14B     | hard_cluster_main_r2 | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH |      7 |   0.625    |   0.3275   |        19.8946  |
| Qwen-14B       | Qwen-14B     | hard_generic_main_r2 | POSTPROCESS_ONLY_PATCH                  |      1 |   0.88     |   0.53     |         5.98843 |
| Qwen-14B       | Qwen-14B     | hard_generic_main_r2 | DISCRETIZATION_ONLY_PATCH               |      2 |   0.86     |   0.51     |         6.10249 |
| Qwen-14B       | Qwen-14B     | hard_generic_main_r2 | TARGET_ONLY_PATCH                       |      3 |   0.73     |   0.38     |         7.81468 |
| Qwen-14B       | Qwen-14B     | hard_generic_main_r2 | TARGET_PLUS_POSTPROCESS_PATCH           |      4 |   0.72     |   0.37     |         7.84393 |
| Qwen-14B       | Qwen-14B     | hard_generic_main_r2 | CASS_TARGET_POSTPROCESS_PATCH           |      5 |   0.72     |   0.37     |        14.2749  |
| Qwen-14B       | Qwen-14B     | hard_generic_main_r2 | ROLE_ONLY_REPLAY                        |      6 |   0.705    |   0.355    |         7.51127 |
| Qwen-14B       | Qwen-14B     | hard_generic_main_r2 | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH |      7 |   0.69     |   0.34     |        19.8452  |
| Qwen-7B        | Qwen-7B      | hard_cluster_main_r2 | CASS_TARGET_POSTPROCESS_PATCH           |      1 |   0.751049 |   0.472727 |         4.29576 |
| Qwen-7B        | Qwen-7B      | hard_cluster_main_r2 | TARGET_ONLY_PATCH                       |      2 |   0.746853 |   0.468531 |         1.82563 |
| Qwen-7B        | Qwen-7B      | hard_cluster_main_r2 | TARGET_PLUS_POSTPROCESS_PATCH           |      3 |   0.745455 |   0.467133 |         1.8276  |
| Qwen-7B        | Qwen-7B      | hard_cluster_main_r2 | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH |      4 |   0.744056 |   0.465734 |         6.80539 |
| Qwen-7B        | Qwen-7B      | hard_cluster_main_r2 | POSTPROCESS_ONLY_PATCH                  |      5 |   0.732867 |   0.454545 |         1.59965 |
| Qwen-7B        | Qwen-7B      | hard_cluster_main_r2 | DISCRETIZATION_ONLY_PATCH               |      6 |   0.73007  |   0.451748 |         1.59617 |
| Qwen-7B        | Qwen-7B      | hard_cluster_main_r2 | ROLE_ONLY_REPLAY                        |      7 |   0.727273 |   0.448951 |         1.72995 |
| Qwen-7B        | Qwen-7B      | hard_generic_main_r2 | CASS_TARGET_POSTPROCESS_PLUS_ROLE_PATCH |      1 |   0.819672 |   0.497268 |         6.68552 |
| Qwen-7B        | Qwen-7B      | hard_generic_main_r2 | TARGET_ONLY_PATCH                       |      2 |   0.786885 |   0.464481 |         1.59467 |
| Qwen-7B        | Qwen-7B      | hard_generic_main_r2 | TARGET_PLUS_POSTPROCESS_PATCH           |      3 |   0.781421 |   0.459016 |         1.59069 |
| Qwen-7B        | Qwen-7B      | hard_generic_main_r2 | CASS_TARGET_POSTPROCESS_PATCH           |      4 |   0.775956 |   0.453552 |         4.1072  |
| Qwen-7B        | Qwen-7B      | hard_generic_main_r2 | ROLE_ONLY_REPLAY                        |      5 |   0.770492 |   0.448087 |         1.49604 |
| Qwen-7B        | Qwen-7B      | hard_generic_main_r2 | DISCRETIZATION_ONLY_PATCH               |      6 |   0.765027 |   0.442623 |         1.43379 |
| Qwen-7B        | Qwen-7B      | hard_generic_main_r2 | POSTPROCESS_ONLY_PATCH                  |      7 |   0.765027 |   0.442623 |         1.44152 |

| model_family   | model_name   | surface              | method                        |   rank |   accuracy |   net_gain |   avg_latency_s |   portable_core_family_win |
|:---------------|:-------------|:---------------------|:------------------------------|-------:|-----------:|-----------:|----------------:|---------------------------:|
| Granite-8B     | Granite-8B   | hard_cluster_main_r2 | POSTPROCESS_ONLY_PATCH        |      1 |   0.7075   |   0.5825   |         4.67873 |                          1 |
| Granite-8B     | Granite-8B   | hard_cluster_main_r2 | DISCRETIZATION_ONLY_PATCH     |      2 |   0.7025   |   0.5775   |         4.62414 |                          0 |
| Granite-8B     | Granite-8B   | hard_cluster_main_r2 | TARGET_ONLY_PATCH             |      3 |   0.515    |   0.39     |         4.94418 |                          0 |
| Granite-8B     | Granite-8B   | hard_cluster_main_r2 | CASS_TARGET_POSTPROCESS_PATCH |      4 |   0.5075   |   0.3825   |         9.75801 |                          0 |
| Granite-8B     | Granite-8B   | hard_cluster_main_r2 | TARGET_PLUS_POSTPROCESS_PATCH |      5 |   0.5025   |   0.3775   |         4.96003 |                          0 |
| Granite-8B     | Granite-8B   | hard_cluster_main_r2 | ROLE_ONLY_REPLAY              |      6 |   0.305    |   0.18     |         5.0868  |                          0 |
| Granite-8B     | Granite-8B   | hard_generic_main_r2 | POSTPROCESS_ONLY_PATCH        |      1 |   0.715    |   0.51     |         4.63205 |                          1 |
| Granite-8B     | Granite-8B   | hard_generic_main_r2 | DISCRETIZATION_ONLY_PATCH     |      2 |   0.71     |   0.505    |         4.56832 |                          0 |
| Granite-8B     | Granite-8B   | hard_generic_main_r2 | CASS_TARGET_POSTPROCESS_PATCH |      3 |   0.64     |   0.435    |         9.06521 |                          0 |
| Granite-8B     | Granite-8B   | hard_generic_main_r2 | TARGET_PLUS_POSTPROCESS_PATCH |      4 |   0.635    |   0.43     |         4.8127  |                          0 |
| Granite-8B     | Granite-8B   | hard_generic_main_r2 | TARGET_ONLY_PATCH             |      5 |   0.625    |   0.42     |         4.78767 |                          0 |
| Granite-8B     | Granite-8B   | hard_generic_main_r2 | ROLE_ONLY_REPLAY              |      7 |   0.295    |   0.09     |         4.91421 |                          0 |
| Mistral-7B     | Mistral-7B   | hard_cluster_main_r2 | TARGET_PLUS_POSTPROCESS_PATCH |      1 |   0.3325   |   0.2625   |         2.74153 |                          1 |
| Mistral-7B     | Mistral-7B   | hard_cluster_main_r2 | TARGET_ONLY_PATCH             |      2 |   0.3325   |   0.2625   |         2.7506  |                          0 |
| Mistral-7B     | Mistral-7B   | hard_cluster_main_r2 | CASS_TARGET_POSTPROCESS_PATCH |      3 |   0.3325   |   0.2625   |         6.68413 |                          0 |
| Mistral-7B     | Mistral-7B   | hard_cluster_main_r2 | POSTPROCESS_ONLY_PATCH        |      5 |   0.3175   |   0.2475   |         2.63034 |                          0 |
| Mistral-7B     | Mistral-7B   | hard_cluster_main_r2 | DISCRETIZATION_ONLY_PATCH     |      6 |   0.3175   |   0.2475   |         2.6342  |                          0 |
| Mistral-7B     | Mistral-7B   | hard_cluster_main_r2 | ROLE_ONLY_REPLAY              |      7 |   0.1675   |   0.0975   |         2.92232 |                          0 |
| Mistral-7B     | Mistral-7B   | hard_generic_main_r2 | TARGET_PLUS_POSTPROCESS_PATCH |      1 |   0.415    |   0.36     |         2.652   |                          1 |
| Mistral-7B     | Mistral-7B   | hard_generic_main_r2 | TARGET_ONLY_PATCH             |      2 |   0.415    |   0.36     |         2.67164 |                          0 |
| Mistral-7B     | Mistral-7B   | hard_generic_main_r2 | CASS_TARGET_POSTPROCESS_PATCH |      3 |   0.415    |   0.36     |         6.98537 |                          0 |
| Mistral-7B     | Mistral-7B   | hard_generic_main_r2 | DISCRETIZATION_ONLY_PATCH     |      5 |   0.405    |   0.35     |         2.47514 |                          0 |
| Mistral-7B     | Mistral-7B   | hard_generic_main_r2 | POSTPROCESS_ONLY_PATCH        |      6 |   0.405    |   0.35     |         2.47719 |                          0 |
| Mistral-7B     | Mistral-7B   | hard_generic_main_r2 | ROLE_ONLY_REPLAY              |      7 |   0.18     |   0.125    |         2.77976 |                          0 |
| Qwen-14B       | Qwen-14B     | hard_cluster_main_r2 | POSTPROCESS_ONLY_PATCH        |      1 |   0.8425   |   0.545    |         6.3053  |                          1 |
| Qwen-14B       | Qwen-14B     | hard_cluster_main_r2 | DISCRETIZATION_ONLY_PATCH     |      2 |   0.825    |   0.5275   |         6.26441 |                          0 |
| Qwen-14B       | Qwen-14B     | hard_cluster_main_r2 | TARGET_PLUS_POSTPROCESS_PATCH |      3 |   0.72     |   0.4225   |         7.98436 |                          0 |
| Qwen-14B       | Qwen-14B     | hard_cluster_main_r2 | TARGET_ONLY_PATCH             |      4 |   0.7075   |   0.41     |         7.85607 |                          0 |
| Qwen-14B       | Qwen-14B     | hard_cluster_main_r2 | CASS_TARGET_POSTPROCESS_PATCH |      5 |   0.705    |   0.4075   |        14.3284  |                          0 |
| Qwen-14B       | Qwen-14B     | hard_cluster_main_r2 | ROLE_ONLY_REPLAY              |      6 |   0.68     |   0.3825   |         7.84137 |                          0 |
| Qwen-14B       | Qwen-14B     | hard_generic_main_r2 | POSTPROCESS_ONLY_PATCH        |      1 |   0.88     |   0.53     |         5.98843 |                          1 |
| Qwen-14B       | Qwen-14B     | hard_generic_main_r2 | DISCRETIZATION_ONLY_PATCH     |      2 |   0.86     |   0.51     |         6.10249 |                          0 |
| Qwen-14B       | Qwen-14B     | hard_generic_main_r2 | TARGET_ONLY_PATCH             |      3 |   0.73     |   0.38     |         7.81468 |                          0 |
| Qwen-14B       | Qwen-14B     | hard_generic_main_r2 | TARGET_PLUS_POSTPROCESS_PATCH |      4 |   0.72     |   0.37     |         7.84393 |                          0 |
| Qwen-14B       | Qwen-14B     | hard_generic_main_r2 | CASS_TARGET_POSTPROCESS_PATCH |      5 |   0.72     |   0.37     |        14.2749  |                          0 |
| Qwen-14B       | Qwen-14B     | hard_generic_main_r2 | ROLE_ONLY_REPLAY              |      6 |   0.705    |   0.355    |         7.51127 |                          0 |
| Qwen-7B        | Qwen-7B      | hard_cluster_main_r2 | CASS_TARGET_POSTPROCESS_PATCH |      1 |   0.751049 |   0.472727 |         4.29576 |                          1 |
| Qwen-7B        | Qwen-7B      | hard_cluster_main_r2 | TARGET_ONLY_PATCH             |      2 |   0.746853 |   0.468531 |         1.82563 |                          0 |
| Qwen-7B        | Qwen-7B      | hard_cluster_main_r2 | TARGET_PLUS_POSTPROCESS_PATCH |      3 |   0.745455 |   0.467133 |         1.8276  |                          0 |
| Qwen-7B        | Qwen-7B      | hard_cluster_main_r2 | POSTPROCESS_ONLY_PATCH        |      5 |   0.732867 |   0.454545 |         1.59965 |                          0 |
| Qwen-7B        | Qwen-7B      | hard_cluster_main_r2 | DISCRETIZATION_ONLY_PATCH     |      6 |   0.73007  |   0.451748 |         1.59617 |                          0 |
| Qwen-7B        | Qwen-7B      | hard_cluster_main_r2 | ROLE_ONLY_REPLAY              |      7 |   0.727273 |   0.448951 |         1.72995 |                          0 |
| Qwen-7B        | Qwen-7B      | hard_generic_main_r2 | TARGET_ONLY_PATCH             |      2 |   0.786885 |   0.464481 |         1.59467 |                          1 |
| Qwen-7B        | Qwen-7B      | hard_generic_main_r2 | TARGET_PLUS_POSTPROCESS_PATCH |      3 |   0.781421 |   0.459016 |         1.59069 |                          0 |
| Qwen-7B        | Qwen-7B      | hard_generic_main_r2 | CASS_TARGET_POSTPROCESS_PATCH |      4 |   0.775956 |   0.453552 |         4.1072  |                          0 |
| Qwen-7B        | Qwen-7B      | hard_generic_main_r2 | ROLE_ONLY_REPLAY              |      5 |   0.770492 |   0.448087 |         1.49604 |                          0 |
| Qwen-7B        | Qwen-7B      | hard_generic_main_r2 | DISCRETIZATION_ONLY_PATCH     |      6 |   0.765027 |   0.442623 |         1.43379 |                          0 |
| Qwen-7B        | Qwen-7B      | hard_generic_main_r2 | POSTPROCESS_ONLY_PATCH        |      7 |   0.765027 |   0.442623 |         1.44152 |                          0 |