# 🏥 MIMIC-IV 기반 패혈증 환자 24시간 내 사망 예측

**팀 프로젝트 | 2024 | AUROC 0.916**

## 📌 요약

PhysioNet의 MIMIC-IV 데이터를 활용하여 ICU 입원 패혈증 환자(18,001명)의 24시간 내 사망을 예측하는 모델을 개발했습니다. 6시간 슬라이딩 윈도우 기반 피처 엔지니어링과 XGBoost 분류기를 사용하였으며, AUROC 0.916을 달성했습니다.

---

## 🎯 문제 정의

ICU 환자의 조기 악화 감지는 의료진의 선제적 개입을 가능하게 합니다. 패혈증(Sepsis-3 기준)은 ICU 사망의 주요 원인 중 하나로, 활력 징후·검사 수치·처치 기록을 통합하여 사망 위험을 조기에 예측하는 모델의 임상적 필요성이 높습니다.

---

## 📊 데이터

| 구분 | 수 |
|------|-----|
| 전체 ICU 입실 | 74,829건 |
| Sepsis-3 충족 (최종 코호트) | 18,001명 (33.0%) |
| 생존 | 65,899명 (88.1%) |
| 사망 | 8,930명 (11.9%) |

- **출처:** MIMIC-IV (PhysioNet DUA 계약 하 사용, 원본 재배포 금지)
- **피처 소스:** Vitals, Labs, Interventions, GCS (총 41개 피처)

자세한 변수 구성은 [data/data_description.md](data/data_description.md) 참고

---

## 🔍 방법론

### 피처 엔지니어링
- **슬라이딩 윈도우:** 크기 6시간, 간격 1시간
- **결측치:** 측정 미시행으로 해석 → `lactate_missing`, `abga_checked` 플래그 생성
- **추세 변수:** Delta(최댓값-최솟값), Slope(선형 기울기)
- **임상 복합지표:** Shock Index, MEWS, NEWS

자세한 설계는 [docs/feature_engineering.md](docs/feature_engineering.md) 참고

### 모델
- **알고리즘:** XGBoost (gradient boosting)
- **불균형 처리:** scale_pos_weight
- **평가 지표:** AUROC, AUPRC, Sensitivity, Specificity

---

## 📈 핵심 결과

| 지표 | 값 |
|------|----|
| AUROC | **0.916** |
| AUPRC | - |

<!-- 👉 outputs/ 에 이미지 추가 후 아래 주석을 교체:
![ROC Curve](outputs/roc_curve.png)
![Feature Importance](outputs/feature_importance.png)
-->

---

## 📁 프로젝트 구조

```
mimic-iv-deterioration-prediction/
├── README.md
├── .gitignore
├── data/
│   └── data_description.md      # 코호트·피처 설명 (원본 미포함)
├── src/
│   └── (분석 코드)
└── docs/
    └── feature_engineering.md   # 피처 엔지니어링 설계 문서
```

---

## ▶️ 실행 방법

**환경:** Python >= 3.8

**필요 패키지:**
```bash
pip install pandas numpy scikit-learn xgboost matplotlib seaborn
```

**데이터 접근:**
- MIMIC-IV 데이터는 PhysioNet 계정 및 DUA 승인이 필요합니다
- 접근: https://physionet.org/content/mimiciv/

**실행:**
1. 이 레포를 클론합니다
2. PhysioNet에서 MIMIC-IV 데이터를 다운로드하여 `data/raw/` 에 배치합니다
3. `src/` 내 노트북을 순서대로 실행합니다

---

## ⚠️ 데이터 보안

MIMIC-IV 원본 데이터는 PhysioNet DUA 계약에 따라 이 레포에 포함되어 있지 않습니다. 환자 식별 정보를 포함하는 파일은 `.gitignore`로 추적에서 제외되어 있습니다.

---

## 👥 Team

**김예지** (강원대학교 정보통계학과) — 데이터 전처리, 피처 엔지니어링, 모델링

- GitHub: [kyjwise7-hub](https://github.com/kyjwise7-hub)
- Portfolio: [kyjwise7.oopy.io](https://kyjwise7.oopy.io)
