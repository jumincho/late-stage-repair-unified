<div align="center">

# late-stage-repair-unified

**同一套简单的决策空间在数学和输出约束两个领域上都能成立吗**

![Status](https://img.shields.io/badge/status-dormant-lightgrey)
![Language](https://img.shields.io/badge/language-Python-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-CC%20BY--NC%204.0-lightgrey)
![Closure](https://img.shields.io/badge/closure-2026--03-blue)

[한국어](./README.md) · [English](./README.md#english) · **中文**

</div>

> 🧊 **休眠中的研究试点。**

## 这项研究想看什么

语言模型在解难题、要给出最终答案的时候,经常在最后一步上犯小错。
为了修这个错而让它把整份答案从头重写,成本高,而且常常把本来没问题的部分一起弄坏。

本项目的核心假设非常简单:

> 很多失败并不需要把整个答案重写一遍,**只要把最后一步的小问题修掉就够了**。

所以我们刻意把决策空间收窄到只有三种选择:

- 什么都不做
- 只修最后一步(local repair)
- 从头重写(global rewrite)

然后在两个表面看起来非常不同的领域里验证这套相同的决策空间是否都成立:

- 较难的数学 / 算术题
- 输出格式约束较严格的题目(必须精确遵守某种格式与条件的输出)

在多个尺度的模型(两个 7B、一个 14B)上,用全新收集的样例做了完整验证。

## 发现了什么

- **"只修最后一步" 一直比 "从头重写" 表现更好。** 在数学上、在输出格式约束上、甚至把两个领域合在一起用同一条规则时,差距都很显著。
- **两个领域的行为出乎意料地相似。** 按领域分别精调的规则,与不分领域统一适用的同一条规则,差距非常小。也就是说,看似不同的 "数学" 与 "守住输出格式",在 **"修掉最后一步的小错"** 这个层面上,可以被理解为同一个问题。
- **模型越大,这种增益的绝对幅度越小**,但模式仍然保持。
- **不过不能说 "一条普适规则在所有领域、所有尺度上都是最佳"。** 在更难的约束问题上,按领域定制的规则在边缘上仍然有帮助。

详细结果请见:

- 🇰🇷 [`REPORT_PROJECT_SUMMARY_KO.md`](REPORT_PROJECT_SUMMARY_KO.md)
- 🇬🇧 [`REPORT_PROJECT_SUMMARY_EN.md`](REPORT_PROJECT_SUMMARY_EN.md)

## 为什么暂停

结论是清楚的,把两个领域串成一个故事的叙事也已经成型。
但最初想要的 "唯一普适规则" 这一步没能走到,只走到了 "共享的决策几何 + 接近普适的单一规则"。
要重启的时候,自然的做法不是去强行追那个 "唯一规则",而是等下一个外部刺激出现(更大的尺度,或者一个新的、有挑战性的约束领域),
再在这个 framing 上把项目重新唤醒。

## 重启时先看哪里

- 📖 [`GLOSSARY.md`](GLOSSARY.md) —— 把代码与关闭报告里出现的内部术语(`cass_r4`、`last_pack`、`unify_live_full_r2`、`DART_REPO_ROOT`、三个动作名,以及 `frozen_context/` 与 `final/` 目录的区别等)翻成日常用语的对照表
- 🇰🇷 [`REPORT_PROJECT_SUMMARY_KO.md`](REPORT_PROJECT_SUMMARY_KO.md) —— 韩语版完整最终报告
- 🇬🇧 [`REPORT_PROJECT_SUMMARY_EN.md`](REPORT_PROJECT_SUMMARY_EN.md) —— 英语版完整最终报告,建议第一个看
- [`reports/final/`](reports/final/) —— 按领域分的最终报告,以及把两个领域合到一起的统一报告
- [`reports/frozen_context/`](reports/frozen_context/) —— 在合并到一起之前的语境(数学侧、格式侧)
- [`logs/research_log.md`](logs/research_log.md)、[`logs/decision_log.md`](logs/decision_log.md) —— 决策与思路演化的时间线

## 代码地图

| 文件 | 做什么 |
|---|---|
| [`code/scripts/unify_live_full_r2_prepare.py`](code/scripts/unify_live_full_r2_prepare.py) | 准备最终一轮的输入数据 |
| [`code/scripts/unify_live_full_run_family.sh`](code/scripts/unify_live_full_run_family.sh) | 按模型批量跑实验 |
| [`code/scripts/unify_live_full_r2_watch_qwen14.py`](code/scripts/unify_live_full_r2_watch_qwen14.py) | 大模型分多卡跑时的看门狗 |
| [`code/scripts/unify_live_full_r2_integrity.py`](code/scripts/unify_live_full_r2_integrity.py) | 已收集数据的完整性校验 |
| [`code/scripts/unify_live_full_r2_make_reports.py`](code/scripts/unify_live_full_r2_make_reports.py) | 生成最终报告、表格、图 |
| [`code/scripts/last_pack_collect_format.py`](code/scripts/last_pack_collect_format.py) | 输出格式约束领域的样例收集 |
| [`code/scripts/cass_r4_collect.py`](code/scripts/cass_r4_collect.py) | 数学领域的样例收集 |
| [`code/src/dart_research/`](code/src/dart_research/) | 按领域组织的运行器模块(数学 / 格式两侧) |

## 目录概览

```
.
├── code/                       实验代码(收集 / 执行 / 汇总 / 合并)
├── configs/                    模型与数据配置
├── prompts/                    提示资产
├── tests/                      回归测试
├── reports/frozen_context/     合并前的语境报告
├── reports/final/              最终综合报告
├── tables/                     写作用表格(CSV)
├── figures/                    写作用图(PNG)
├── results_compact/            按模型的紧凑结果摘要
├── manifests/                  运行清单
├── logs/                       研究日志 / 决策日志
├── GLOSSARY.md                 内部术语词典
├── REPORT_PROJECT_SUMMARY_KO.md
└── REPORT_PROJECT_SUMMARY_EN.md
```

## 环境

```bash
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install -U -e .
export HF_TOKEN=...   # 仅在需要时
```

原始运行环境的绝对路径(`/workspace/project`)可以用环境变量
`DART_REPO_ROOT` 覆写。脚本与模块里所有默认路径
(`data/`、`results/`、`reports/`、`tables/`、`figures/`、`external/`)
都以这个变量为基准:

```bash
export DART_REPO_ROOT="$(pwd)"   # 或任意绝对路径
```

## 状态

🧊 **休眠中** —— 在两个领域可以被串成一个叙事的结论上停了下来。

## 许可证

以 [CC BY-NC 4.0](./LICENSE) 发布。
