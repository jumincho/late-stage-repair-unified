<div align="center">

# late-stage-repair-unified

**같은 단순 결정 공간이 수학과 출력제약 두 도메인 모두에서 통하는가**
**Does the same simple decision space work across math and output-constraint domains?**

![Status](https://img.shields.io/badge/status-dormant-lightgrey)
![Language](https://img.shields.io/badge/language-Python-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-CC%20BY--NC%204.0-lightgrey)
![Closure](https://img.shields.io/badge/closure-2026--03-blue)

**한국어** · [English](#english) · [中文](./README.zh-CN.md)

</div>

> 🧊 **휴면(dormant) 중인 연구 파일럿입니다.**

## ⭐ 핵심 결과 (TL;DR)

- **"마지막 단계만 살짝 고치기"가 "처음부터 다시 쓰기"를 일관되게 이겼습니다** — 수학·출력제약 두 도메인 모두에서.
- **두 도메인은 거의 같은 결정 규칙을 공유**했습니다 — 도메인별 맞춤 규칙과 단일 공유 규칙의 격차가 매우 작았습니다.
- 단 **"단 하나의 보편 규칙이 항상 최선"까지는 아니었고**, 모델이 커질수록 이득의 절대 크기는 줄었습니다.

## 무엇을 보려던 연구였나

언어모델이 어려운 문제를 풀다가 마지막에 답을 만들 때 종종 작은 실수를 합니다. 그 실수를 고치려고 답을 처음부터 다시 쓰게 하는 건 비싸고 종종 멀쩡한 부분까지 망가뜨립니다.

이 프로젝트의 핵심 가설은 단순했습니다.

> 많은 실패는 답 전체를 다시 쓸 필요 없이, **마지막 단계의 작은 부분만 고치면 된다**.

그래서 다음 세 가지 선택지로만 이루어진 아주 단순한 결정 공간을 만들었습니다.

- 아무것도 안 한다
- 마지막 단계만 살짝 고친다 (local repair)
- 처음부터 다시 쓴다 (global rewrite)

그리고 성격이 매우 다른 두 도메인에서 이 똑같은 결정 공간이 통하는지를 봤습니다.

- 어려운 수학 / 산술 문제
- 출력 형식이 까다로운 제약 만족 문제 (예: 특정 포맷·조건을 정확히 지켜야 하는 출력)

여러 크기의 모델(7B 두 가지, 14B 한 가지) 위에서 새로 모은 사례들로 검증했습니다.

## 무엇을 알아냈나

- **"마지막만 살짝 고친다" 가 "처음부터 다시 쓴다" 보다 일관되게 더 좋았습니다.** 수학에서도, 출력 제약에서도, 두 도메인을 합쳐 하나의 규칙으로 적용해도 차이가 컸습니다.
- **두 도메인이 의외로 비슷하게 움직였습니다.** 도메인별로 별도로 규칙을 다듬은 것과, 도메인 구분 없이 한 규칙으로 적용한 것의 격차가 매우 작았습니다. 즉 "수학" 과 "출력 형식 지키기" 가 겉보기엔 다르지만, **마지막 단계의 실수를 고친다** 라는 같은 문제로 묶일 수 있다는 증거가 모였습니다.
- **모델이 커질수록 이득의 절대 크기는 줄어들지만**, 같은 패턴은 유지됐습니다.
- **다만 "단 하나의 보편 규칙이 모든 도메인·모든 모델에서 항상 최선이다" 까지는 말할 수 없습니다.** 더 어려운 제약 문제에서는 도메인 맞춤 규칙이 가장자리에서 여전히 도움이 됐습니다.

자세한 결과가 궁금하시면:

- 🇰🇷 [`REPORT_PROJECT_SUMMARY_KO.md`](REPORT_PROJECT_SUMMARY_KO.md)
- 🇬🇧 [`REPORT_PROJECT_SUMMARY_EN.md`](REPORT_PROJECT_SUMMARY_EN.md)

## 왜 잠시 멈춰 두는가

결론은 분명하고, 두 도메인을 묶는 서사도 정리됐습니다. 다만 처음에 노렸던 "보편 단일 규칙" 까지는 안 가고 "공유되는 결정 기하 + 가까운 단일 규칙" 으로 좁아졌습니다. 다음 자극(더 큰 스케일, 새로운 까다로운 제약 도메인)이 생기면 그 framing 위에서 다시 깨우는 편이 자연스럽다고 판단했습니다.

## 다시 들여다볼 때는 어디부터

- 📖 [`GLOSSARY.md`](GLOSSARY.md) — 코드와 종료 보고서에 흘러 들어간 내부 용어(`cass_r4`, `last_pack`, `unify_live_full_r2`, `DART_REPO_ROOT`, 세 가지 액션 이름 등)를 일반어로 정리한 사전
- 🇰🇷 [`REPORT_PROJECT_SUMMARY_KO.md`](REPORT_PROJECT_SUMMARY_KO.md) — 한 편 분량의 최종 보고서. 가장 먼저 읽으면 좋은 글
- [`reports/final/`](reports/final/) — 도메인별 최종 보고서와 두 도메인을 묶은 통합 보고서
- [`reports/frozen_context/`](reports/frozen_context/) — 그 전 단계까지의 맥락(수학 쪽, 포맷 쪽)
- [`logs/research_log.md`](logs/research_log.md), [`logs/decision_log.md`](logs/decision_log.md) — 의사결정의 흐름

## 코드 어디에 뭐가 있나

| 파일 | 하는 일 |
|---|---|
| [`code/scripts/unify_live_full_r2_prepare.py`](code/scripts/unify_live_full_r2_prepare.py) | 마지막 라운드의 입력 데이터를 준비 |
| [`code/scripts/unify_live_full_run_family.sh`](code/scripts/unify_live_full_run_family.sh) | 모델 단위로 실험을 일괄 실행 |
| [`code/scripts/unify_live_full_r2_watch_qwen14.py`](code/scripts/unify_live_full_r2_watch_qwen14.py) | 큰 모델을 여러 GPU 로 나눠 돌릴 때의 워치독 |
| [`code/scripts/unify_live_full_r2_integrity.py`](code/scripts/unify_live_full_r2_integrity.py) | 모은 데이터의 무결성 확인 |
| [`code/scripts/unify_live_full_r2_make_reports.py`](code/scripts/unify_live_full_r2_make_reports.py) | 최종 보고서, 표, 그림을 만든다 |
| [`code/scripts/last_pack_collect_format.py`](code/scripts/last_pack_collect_format.py) | 출력 형식 도메인 쪽 사례 수집 |
| [`code/scripts/cass_r4_collect.py`](code/scripts/cass_r4_collect.py) | 수학 도메인 쪽 사례 수집 |
| [`code/src/dart_research/`](code/src/dart_research/) | 도메인별 실행기 모듈들 (수학 / 포맷 양쪽) |

## 폴더 지도

```
.
├── code/                       실험 코드 (수집·실행·집계·통합)
├── configs/                    모델·데이터 설정
├── prompts/                    프롬프트 자산
├── tests/                      회귀 테스트
├── reports/frozen_context/     이전 단계 맥락 보고서
├── reports/final/              최종 종합 보고서
├── tables/                     글쓰기용 표 (CSV)
├── figures/                    글쓰기용 그림 (PNG)
├── results_compact/            모델별 요약 결과
├── manifests/                  실행 매니페스트
├── logs/                       연구일지 / 의사결정 기록
├── GLOSSARY.md                 내부 용어 사전
├── REPORT_PROJECT_SUMMARY_KO.md
└── REPORT_PROJECT_SUMMARY_EN.md
```

## 환경

```bash
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install -U -e .
export HF_TOKEN=...   # 필요한 경우에만
```

원본 실행 환경의 절대 경로(`/workspace/project`)는 `DART_REPO_ROOT` 환경변수로
재정의할 수 있습니다. 스크립트와 모듈의 모든 기본 경로(`data/`, `results/`,
`reports/`, `tables/`, `figures/`, `external/`)가 이 변수를 기준으로 잡힙니다.

```bash
export DART_REPO_ROOT="$(pwd)"   # 또는 원하는 절대 경로
```

## 상태

🧊 **휴면 중** — 두 도메인을 하나의 이야기로 묶는 결론이 정리된 상태에서 멈춰 있습니다.

---

<a name="english"></a>

## English

> 🧊 **Dormant research pilot.**

### ⭐ Key result (TL;DR)

- **Patching just the last step beat full rewrites — consistently, in both the math and output-constraint domains.**
- The **two domains shared nearly the same decision rule**; per-domain tuning barely improved on one shared rule.
- But it's **not a single universal best rule** — and the absolute gain shrinks as models scale up.

### What this set out to test

When a language model produces a final answer, it often makes small mistakes at the last step. Asking it to rewrite the whole answer is expensive and frequently breaks otherwise-good parts.

The core hypothesis was simple:

> Many failures need only a **small patch at the last step**, not a full rewrite.

So we built a deliberately narrow three-option decision space:

- Do nothing.
- Local repair — patch only the last step.
- Global rewrite — start over.

And asked whether the same decision space holds across two domains with very different surface features:

- Hard math / arithmetic problems.
- Output-constraint satisfaction problems (outputs that must precisely respect a tricky format).

Evaluated on freshly collected cases across multiple model sizes (two 7B models, one 14B).

### What it found

- **"Local repair" consistently beat "global rewrite"** — in math, in output-constraint problems, and even when one unified rule was applied across both.
- **The two domains moved more similarly than expected.** Per-domain rule tuning barely improved on a single shared rule. The visually different surface ("math" vs "format-keeping") collapses onto the same underlying problem when reframed as **patching the last-step mistake**.
- **As models scale, the absolute gain shrinks** but the pattern persists.
- **Not strong enough to claim "one universal rule is always best."** On harder constraint problems, domain-tailored rules still helped at the margin.

Full results:

- 🇰🇷 [`REPORT_PROJECT_SUMMARY_KO.md`](REPORT_PROJECT_SUMMARY_KO.md)
- 🇬🇧 [`REPORT_PROJECT_SUMMARY_EN.md`](REPORT_PROJECT_SUMMARY_EN.md)

### Why it's on hold

The conclusion stands clearly and the cross-domain narrative is in place. What didn't land is the original "single universal rule" — it narrowed to "shared decision geometry + a near-universal rule." A natural restart waits for the next angle (larger scale, a new tricky constraint domain) rather than pushing further now.

### Where to look first when revisiting

- 📖 [`GLOSSARY.md`](GLOSSARY.md) — Decoder ring for the internal vocabulary that leaked into source and closure reports (`cass_r4`, `last_pack`, `unify_live_full_r2`, `DART_REPO_ROOT`, the three action names, and the `frozen_context/` vs `final/` split).
- 🇬🇧 [`REPORT_PROJECT_SUMMARY_EN.md`](REPORT_PROJECT_SUMMARY_EN.md) — single-essay final report.
- [`reports/final/`](reports/final/) — per-domain and unified final reports.
- [`reports/frozen_context/`](reports/frozen_context/) — pre-unification context (math side, format side).
- [`logs/research_log.md`](logs/research_log.md), [`logs/decision_log.md`](logs/decision_log.md) — decision flow over time.

### Code map

| File | What it does |
|---|---|
| [`code/scripts/unify_live_full_r2_prepare.py`](code/scripts/unify_live_full_r2_prepare.py) | Prepares the last-round input data |
| [`code/scripts/unify_live_full_run_family.sh`](code/scripts/unify_live_full_run_family.sh) | Per-model batch experiment runner |
| [`code/scripts/unify_live_full_r2_watch_qwen14.py`](code/scripts/unify_live_full_r2_watch_qwen14.py) | Watchdog for the larger model split across GPUs |
| [`code/scripts/unify_live_full_r2_integrity.py`](code/scripts/unify_live_full_r2_integrity.py) | Integrity check on collected data |
| [`code/scripts/unify_live_full_r2_make_reports.py`](code/scripts/unify_live_full_r2_make_reports.py) | Builds the final reports, tables, figures |
| [`code/scripts/last_pack_collect_format.py`](code/scripts/last_pack_collect_format.py) | Case collection for the output-format domain |
| [`code/scripts/cass_r4_collect.py`](code/scripts/cass_r4_collect.py) | Case collection for the math domain |
| [`code/src/dart_research/`](code/src/dart_research/) | Per-domain runner modules (math / format) |

### Folder map

```
.
├── code/                       experiment code (collect / run / aggregate / unify)
├── configs/                    model and data configs
├── prompts/                    prompt assets
├── tests/                      regression tests
├── reports/frozen_context/     pre-unification context reports
├── reports/final/              final unified reports
├── tables/                     writeup tables (CSV)
├── figures/                    writeup figures (PNG)
├── results_compact/            per-model summary results
├── manifests/                  run manifests
├── logs/                       research / decision logs
├── GLOSSARY.md                 internal-terminology dictionary
├── REPORT_PROJECT_SUMMARY_KO.md
└── REPORT_PROJECT_SUMMARY_EN.md
```

### Environment

```bash
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install -U -e .
export HF_TOKEN=...   # only if needed
```

The original execution environment's absolute path (`/workspace/project`) can be
overridden via the `DART_REPO_ROOT` environment variable. All script and module
defaults for `data/`, `results/`, `reports/`, `tables/`, `figures/`, and
`external/` are anchored to it.

```bash
export DART_REPO_ROOT="$(pwd)"   # or any absolute path
```

### Status

🧊 **Dormant** — the cross-domain unifying conclusion is in place; paused at that point.

### License

Released under [CC BY-NC 4.0](./LICENSE).
