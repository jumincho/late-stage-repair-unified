# late-stage-repair-unified

> 🧊 **휴면(dormant) 중인 연구 파일럿입니다.**

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

## 상태

🧊 **휴면 중** — 두 도메인을 하나의 이야기로 묶는 결론이 정리된 상태에서 멈춰 있습니다.
