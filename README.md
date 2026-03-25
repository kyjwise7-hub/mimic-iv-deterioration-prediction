> **팀 프로젝트 안내**
> 이 프로젝트는 오라클 아카데미 6인 팀으로 개발한 중환자 조기 악화 예측 시스템 **Early Deterioration Command Center**의 ML/데이터 모듈입니다.
> 팀 공용 레포는 Private이므로, 본 레포에 제가 담당한 코드·설계문서·실험결과를 별도로 정리했습니다.
>
> - **전체 시스템**: 위험도 실시간 예측 → SHAP 기반 AI 요약 → RAG 가이드라인 제안 → 임상 의사결정 지원
> - **나의 역할**: ML Team — Data Lead / ML Engineer
> - **팀 구성**: 총 6명 (ML 2명, NLP 2명, Frontend 1명, Backend 1명)

---

# MIMIC-IV 기반 ICU 환자 다중 악화 예측 및 임상 의사결정 지원 시스템

**팀 프로젝트 | 2026 | 사망 예측 AUROC 0.914**

## 요약

PhysioNet의 MIMIC-IV 데이터를 기반으로 ICU 입원 패혈증 환자의 단기 악화를 예측하고, 의료진에게 실시간 위험도·AI 요약·가이드라인을 제공하는 임상 의사결정 지원 시스템(CDSS)입니다. 6시간 슬라이딩 윈도우 기반 피처 엔지니어링과 XGBoost 다중 타겟 분류기를 핵심으로, React 대시보드·Flask ML 서비스·RAG 가이드라인 엔진까지 포함한 풀스택 시스템입니다.

---

## 문제 정의

ICU 환자의 조기 악화 감지는 의료진의 선제적 개입을 가능하게 합니다. 패혈증(Sepsis-3 기준)은 ICU 사망의 주요 원인 중 하나로, 사망뿐 아니라 기계환기 시작·승압제 투여 등 처치 개입 시점을 사전에 예측하면 임상적 대응 속도를 높일 수 있습니다. 기존 단일 타겟 모델과 달리, 본 시스템은 4가지 악화 이벤트를 동시에 예측하고 그 결과를 자연어와 가이드라인으로 변환하여 제공합니다.

---

## 데이터

| 구분 | 수 |
|------|----|
| 전체 ICU 입실 | 74,829건 |
| Sepsis-3 충족 (최종 코호트) | 18,001명 |
| 생존 | 65,899명 (88.1%) |
| 사망 | 8,930명 (11.9%) |

- **출처:** MIMIC-IV (PhysioNet DUA 계약 하 사용, 원본 재배포 금지)
- **피처 소스:** Vitals, Labs, Interventions, GCS, Urine Output (총 41개 피처)

---

## 방법론

### 피처 엔지니어링

- **슬라이딩 윈도우:** 크기 6시간, 간격 1시간
- **결측치:** 측정 미시행으로 임상적 재해석 → `lactate_missing`, `abga_checked` 플래그 생성
- **추세 변수:** Delta(최댓값-최솟값), Slope(선형 기울기) — HR, SBP, SpO2, Lactate, GCS 대상
- **임상 복합지표:** Shock Index, MEWS, NEWS
- **기타:** oliguria_flag, is_readmission

### 모델

- **알고리즘:** XGBoost (v3, gradient boosting)
- **예측 타겟:** 사망(24h), 기계환기 시작(12h), 승압제 시작(12h), 복합 이벤트(24h)
- **불균형 처리:** scale_pos_weight
- **임계값 전략:** recall >= 0.80 조건 하 F1 최대화
- **평가 지표:** AUROC, AUPRC, Sensitivity, Specificity

### 시스템 구성

| 컴포넌트 | 기술 |
|----------|------|
| Frontend | React, Chart.js |
| Backend | Express (Node.js) |
| ML Service | Flask (Python) |
| Database | Oracle DB |
| Vector DB | Supabase (pgvector) |

---

## 핵심 결과

| 타겟 | AUROC | AUPRC | Recall (운용 임계값) | Specificity |
|------|-------|-------|----------------------|-------------|
| 사망 (24h) | **0.914** | 0.273 | 0.80 | 0.863 |
| 기계환기 (12h) | 0.770 | 0.081 | 0.81 | 0.570 |
| 승압제 (12h) | 0.799 | 0.050 | 0.80 | 0.646 |
| 복합 이벤트 (24h) | 0.779 | 0.219 | 0.80 | 0.579 |

임계값은 임상 환경에서 민감도 우선(recall >= 0.80)을 기준으로 설정하였습니다.

---

## 나의 주요 기여

| 영역 | 상세 |
|------|------|
| 코호트 정의 | Sepsis-3 기준 적용, 74,829건 → 18,001명 필터링 |
| 전처리 파이프라인 | SQL 기반 피처 추출, DuckDB 활용 중간 처리 |
| 피처 엔지니어링 | 6시간 슬라이딩 윈도우, Delta/Slope 추세변수, Shock Index·NEWS·MEWS 복합지표 |
| 결측치 전략 | 임상적 재해석 기반 결측치 처리 (단순 imputation 아님) |
| 모델링 | XGBoost 기반 4개 타겟 동시 예측, 임계값 최적화 |
| 해석 | SHAP 기반 변수 중요도 분석 |
| 데모 설계 | 3-레이어 아키텍처 기반 데모 데이터 레이어 설계 (Raw → Feature → Presentation) |

---

## 프로젝트 구조

```
miniprj/
├── data-pipeline/
│   ├── scripts/        # 코호트 정의 ~ 피처 엔지니어링 노트북 (01~10)
│   ├── sql/            # cohort.sql, features.sql
│   ├── eda/            # 탐색적 데이터 분석 노트북
│   └── reports/        # EDA 리포트
├── ml-training/
│   ├── notebooks/      # 모델 훈련 노트북 (01~04)
│   ├── configs/        # XGBoost v3 학습 설정
│   └── models/         # 학습 결과 JSON
├── demo_data/
│   └── ARCHITECTURE.md # 데모 데이터 레이어 설계
├── old-backup/         # 초기 실험 코드 및 v1/v2 모델 결과
├── utils/              # 공용 유틸리티
└── docs/               # 문서
```

---

## 실행 방법

**환경:** Python >= 3.10

**필요 패키지:**
```bash
pip install -r requirements.txt
```

**데이터 접근:**
- MIMIC-IV 데이터는 PhysioNet 계정 및 DUA 승인이 필요합니다
- 접근: https://physionet.org/content/mimiciv/

**실행 순서:**
1. 이 레포를 클론합니다
2. PhysioNet에서 MIMIC-IV 데이터를 다운로드하여 `miniprj/data-pipeline/data/raw/` 에 배치합니다
3. `miniprj/data-pipeline/scripts/` 내 노트북을 01번부터 순서대로 실행합니다
4. `miniprj/ml-training/notebooks/` 내 노트북을 순서대로 실행합니다

---

## 데이터 보안

MIMIC-IV 원본 데이터는 PhysioNet DUA 계약에 따라 이 레포에 포함되어 있지 않습니다. 환자 식별 정보를 포함하는 파일은 `.gitignore`로 추적에서 제외되어 있습니다.

---

## Team
**Oracle Academy 2기 - 4조** 불사조
**김예지** (정보통계학과) — 데이터 전처리, 피처 엔지니어링, 모델링

- GitHub: [kyjwise7-hub](https://github.com/kyjwise7-hub)
- Portfolio: [kyjwise7.oopy.io](https://kyjwise7.oopy.io)

---

## 관련 프로젝트

이 시스템의 Sepsis ML 모듈은 최종 프로젝트 LOOK에 통합·발전되었습니다.
→ [clinical-nlp-look](https://github.com/kyjwise7-hub/clinical-nlp-look)
