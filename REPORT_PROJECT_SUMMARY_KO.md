# UNIFY-LIVE-FULL-R2 최종 프로젝트 보고서

## 1. 이 프로젝트는 무엇이었나

이 프로젝트는 추론 시점의 late-stage repair를 다룬 연구였습니다. 핵심 생각은 많은 실패가 “처음부터 새 답을 완전히 다시 쓰는 것”을 요구하지 않는다는 점입니다. 실제로는 마지막 요구사항 실현 단계만 정확히 고치면 되는 경우가 많았습니다.

프로젝트 말기에 이 연구는 두 개의 주된 실험 축으로 정리되었습니다.

- 어려운 산술 / 수학 복구
- validator가 풍부한 출력 제약(output-constraint) 복구

최종 논문 수준의 질문은 다음과 같았습니다.

수학과 출력 제약 과제를, fresh prospective online evidence를 바탕으로 하나의 공통된 late-stage intervention story의 두 사례로 제시할 수 있는가?

## 2. 프로젝트는 어떻게 진행되었나

이 저장소는 매우 많은 브랜치를 거쳐 발전했습니다. 초중기 단계에서는 후보 메커니즘, 진단, validator 사용, 도메인별 복구 연산자가 개발되었습니다. 그 브랜치들은 모두 역사적 증거이고, 이 보관본의 최종 단계는 `UNIFY-LIVE-FULL-R2`입니다.

`UNIFY-LIVE-FULL-R2`는 새로운 방법론 브랜치가 아니었습니다. 이 단계는 더 좁고 명확한 네 가지 일을 했습니다.

- fresh prospective `Qwen-7B`, `Mistral-7B` bank를 무결성 검사로 잠금
- 비어 있던 `Qwen-14B` prospective bank 완주
- pooled policy와 domain-specific policy를 prospective하게 비교
- 두 실험 축을 하나의 논문 본문 서사로 합성

## 3. 최종 개입 구조

최종 추상 action space는 의도적으로 단순하고 고정되어 있었습니다.

- `NO_INTERVENTION`
- `LOCAL_REPAIR`
- `GLOBAL_REWRITE_OR_RESTART`

이 추상 구조는 이미 고정된 도메인 실행기로 매핑되었습니다.

- 수학:
  - 직접 답변
  - frozen postprocess/discretization 중심 local repair
  - frozen restart path
- 포맷:
  - 직접 포맷 답변
  - frozen format-side local repair
  - full rewrite

핵심 주장은 “하나의 보편 규칙이 모든 셀에서 항상 이긴다”가 아닙니다. 핵심은 두 도메인이 같은 late-stage decision geometry로 읽힌다는 점입니다.

## 4. 모델과 평가 표면

필수 모델 계열:

- `Qwen/Qwen2.5-7B-Instruct`
- `mistralai/Mistral-7B-Instruct-v0.3`
- `Qwen/Qwen2.5-14B-Instruct`

주요 표면:

- 수학:
  - `cluster-hard`
  - `generic-hard`
- 포맷:
  - screened `IFEval`
  - `IFBench`

## 5. 실제로 무엇이 완성되었나

최종 `R2` 단계에서는 요구된 fresh prospective coverage가 모두 채워졌습니다.

완성된 prospective bank:

- math raw: `1998 / 1998`
- math replay: `1998 / 1998`
- format: `681 / 681`

표면별 총량:

- `cluster-hard`: `1515`
- `generic-hard`: `483`
- screened `IFEval`: `381`
- `IFBench`: `300`

`Qwen-14B`는 처음에 저활용 경로에서 한 번 정체되었습니다. 최종 완주 경로는 `8`-way sharding과 GPU당 `2` worker slot을 사용했고, 중간 replay checkpoint에서 다시 이어 붙인 뒤 `48 / 48` shard 전체를 완료했습니다.

## 6. 최종 실험 결과

### 6.1 fresh 7B prospective 결과

완성된 두 개의 7B 계열이 최종 주장에 가장 중요합니다.

fresh pooled simple rule 대 always rewrite overall:

- `Qwen-7B`: `+0.2436`, 범위 `[+0.2278, +0.2707]`
- `Mistral-7B`: `+0.2210`, 범위 `[+0.1981, +0.2354]`

이 결과 때문에 output-constraint가 이제 수학과 나란히 놓일 수 있는 진짜 두 번째 메인 축이 되었습니다. 더 이상 retrospective 재분석만으로 서 있는 이야기가 아닙니다.

### 6.2 pooled rule과 domain-specific rule의 차이

pooled simple rule이 모든 domain-tuned rule을 압도할 필요는 없었습니다. 중요한 시험은 naive rewrite보다 분명히 좋으면서도, domain-tuned simple rule에 reasonably close하게 남는가였습니다.

관측된 pooled-minus-domain utility gap:

- `Qwen-7B`
  - 수학: `-0.0010`
  - 포맷: `-0.0121`
- `Mistral-7B`
  - 수학: `-0.0034`
  - 포맷: `-0.0096`

이 정도면 “완전한 보편성”을 주장하지 않으면서도 하나의 논문 서사를 세우기에는 충분히 가깝습니다.

### 6.3 Qwen-14B scale check

`Qwen-14B`를 완주한 뒤에도 같은 geometry는 유지되었습니다.

fresh pooled simple rule 대 always rewrite overall:

- `Qwen-14B`: `+0.1000`, 범위 `[+0.0859, +0.1105]`

pooled-minus-domain utility gap:

- 수학: `-0.0038`
- 포맷: `0.0000`

해석:

- scale이 올라가면 gain은 압축됩니다
- 그래도 positive geometry는 남습니다
- 완성된 scale cell에서는 포맷 쪽 pooled rule이 best domain-tuned simple rule과 정확히 같았습니다

### 6.4 transfer asymmetry

프로젝트는 도메인 간 비대칭성도 확인했습니다.

최종 해석은 부정적이라기보다 건설적입니다.

- domain-specific rule은 여전히 유용합니다
- pooled rule은 예상보다 더 잘 transfer됩니다
- 수학과 포맷은 동일한 과제는 아니지만, late-stage repair 영역에서는 하나의 논문 서사로 묶일 만큼 충분히 강하게 정렬됩니다

### 6.5 공통 failure bucket

가장 강한 교차 도메인 정렬은 계속해서 다음 bucket이었습니다.

- `final_requirement_realization`

이 점이 중요한 이유는, 바로 이 영역에서 두 도메인 모두 즉시 full rewrite보다 targeted local repair의 혜택을 보기 때문입니다.

## 7. 이제 무엇을 주장할 수 있나

가장 안전한 최종 문장은 다음과 같습니다.

fresh prospective `Qwen-7B`, `Mistral-7B`, 그리고 완성된 `Qwen-14B` scale check 전반에서, 어려운 산술 복구와 validator-rich output-constraint 복구는 targeted local repair가 naive full rewrite를 일관되게 이기고 pooled simple policy가 domain-tuned rule에 가깝게 유지되는 하나의 late-stage requirement-realization 문제의 두 사례로 읽힌다.

쉽게 말하면:

- 수학은 확실한 메인 축입니다
- output-constraint도 이제 확실한 메인 축입니다
- 두 축을 묶는 shared geometry는 fresh online evidence로 뒷받침됩니다
- pooled simple rule은 이 서사를 지탱할 만큼 충분히 좋고, 다만 domain-tuned rule이 가장자리에서는 아직 도움이 됩니다

## 8. 무엇은 아직 입증되지 않았나

이 프로젝트가 입증하지 않은 것은 다음과 같습니다.

- 하나의 보편 규칙이 모든 도메인, 모든 scale에서 항상 최선이라는 점
- output-constraint가 수학만큼 쉽다는 점
- `IFBench`가 이미 해결되었거나 parity 수준이라는 점

정직한 단서는 다음과 같습니다.

- `IFBench`는 여전히 더 어려운 boundary surface입니다
- domain-tuned simple criterion은 가장자리에서 여전히 도움이 됩니다
- 따라서 가장 강한 주장은 “완전한 정책 보편성”이 아니라 “공유된 개입 기하”에 관한 것입니다

## 9. 이 보관본에서 무엇부터 읽으면 되나

최종 결론부터 보려면:

- `reports/final/unify_live_full_r2_summary_memo.md`
- `reports/final/unify_live_full_r2_synthesis.md`
- `reports/final/unify_live_full_r2_qwen14b_report.md`

최종 단계 이전의 frozen context를 보려면:

- `reports/frozen_context/cass_r4_main_report.md`
- `reports/frozen_context/cass_fi_portable_core_report.md`
- `reports/frozen_context/lace_full_synthesis.md`
- `reports/frozen_context/unify_full_synthesis.md`

프로젝트 진행 경과를 보려면:

- `logs/research_log.md`
- `logs/decision_log.md`

## 10. 한 줄 결론

이 프로젝트는 분명한 종료 상태에 도달했습니다.

최종 답은 예입니다.

- 수학과 validator-rich output-constraint 과제는 하나의 shared late-stage requirement-realization story의 두 개의 메인 실험 축으로 제시할 수 있습니다
- 그 주장은 두 개의 7B 계열 fresh prospective evidence와 완성된 14B scale check로 지지됩니다

이 보관본은 전체 원본 저장소를 열지 않아도 그 결론을 이해할 수 있도록 만든 최종 압축본입니다.
