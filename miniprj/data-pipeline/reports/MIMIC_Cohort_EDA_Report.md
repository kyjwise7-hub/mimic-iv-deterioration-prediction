# MIMIC-IV 코호트 탐색적 데이터 분석(EDA) 보고서

**분석 일시:** 2026-01-09 22:51:57

---

## 1. 데이터셋 기본 정보

- **총 레코드 수:** 54,551
- **고유 환자 수(subject_id):** 54,551
- **피처(컬럼) 수:** 20

### 컬럼별 데이터 타입
```
subject_id                : int64
hadm_id                   : int64
stay_id                   : int64
intime                    : object
outtime                   : object
los                       : float64
first_careunit            : object
last_careunit             : object
anchor_age                : int64
gender                    : object
dod                       : object
admittime                 : object
dischtime                 : object
deathtime                 : object
hospital_expire_flag      : int64
icu_mortality             : int64
hospital_mortality        : int64
dnr_time                  : object
vent_start_time           : object
pressor_start_time        : object
```

## 2. 기술 통계량

### 수치형 변수 요약
```
         subject_id       hadm_id       stay_id           los    anchor_age  hospital_expire_flag  icu_mortality  hospital_mortality
count  5.455100e+04  5.455100e+04  5.455100e+04  54551.000000  54551.000000          54551.000000   54551.000000        54551.000000
mean   1.500495e+07  2.498014e+07  3.497754e+07      4.254281     63.798116              0.107807       0.070338            0.107807
std    2.891260e+06  2.883410e+06  2.892244e+06      5.689087     16.607906              0.310140       0.255718            0.310140
min    1.000069e+07  2.000015e+07  3.000015e+07      1.000000     18.000000              0.000000       0.000000            0.000000
25%    1.250780e+07  2.248656e+07  3.246635e+07      1.539288     54.000000              0.000000       0.000000            0.000000
50%    1.500952e+07  2.496850e+07  3.496116e+07      2.373958     65.000000              0.000000       0.000000            0.000000
75%    1.752550e+07  2.746583e+07  3.747288e+07      4.461140     76.000000              0.000000       0.000000            0.000000
max    1.999999e+07  2.999983e+07  3.999986e+07    226.403079     91.000000              1.000000       1.000000            1.000000
```

### 주요 의료 지표
- **환자당 평균 입원 횟수:** 1.00
- **연령 중앙값:** 65.0 세
- **재원 기간(LOS) 중앙값:** 2.37 일

## 3. 결측치 분석

| 컬럼명 | 결측치 수 | 비율 |
|:---|:---:|:---:|
| dod | 35,749 | 65.53% |
| deathtime | 48,677 | 89.23% |
| dnr_time | 28,922 | 53.02% |
| vent_start_time | 31,631 | 57.98% |
| pressor_start_time | 42,873 | 78.59% |

## 4. 범주형 변수 분석

### 성별 분포 (고유 환자 기준)

| 성별 | 인원 수 | 비율 |
|:---:|:---:|:---:|
| M | 31,056 | 56.93% |
| F | 23,495 | 43.07% |

### ICU 병동(Unit) 분포

| ICU 병동 | 환자 수 | 비율 |
|:---|:---:|:---:|
| Cardiac Vascular Intensive Care Unit (CVICU) | 11,008 | 20.18% |
| Medical Intensive Care Unit (MICU) | 9,942 | 18.23% |
| Medical/Surgical Intensive Care Unit (MICU/SICU) | 7,957 | 14.59% |
| Surgical Intensive Care Unit (SICU) | 7,458 | 13.67% |
| Trauma SICU (TSICU) | 6,149 | 11.27% |
| Coronary Care Unit (CCU) | 6,059 | 11.11% |
| Neuro Intermediate | 3,779 | 6.93% |
| Neuro Surgical Intensive Care Unit (Neuro SICU) | 1,130 | 2.07% |
| Neuro Stepdown | 865 | 1.59% |
| Surgery/Vascular/Intermediate | 102 | 0.19% |

## 5. 수치형 변수 분석

### 연령대별 분포

| 연령 그룹 | 인원 수 | 비율 |
|:---:|:---:|:---:|
| <30 | 2,619 | 4.80% |
| 30-50 | 8,162 | 14.96% |
| 50-65 | 16,534 | 30.31% |
| 65-80 | 18,171 | 33.31% |
| 80+ | 9,065 | 16.62% |

### 재원 기간(LOS) 상세 분포 (Percentiles)

- 상위 25%: 1.54 일
- 상위 50%: 2.37 일
- 상위 75%: 4.46 일
- 상위 90%: 8.99 일
- 상위 95%: 13.89 일
- 상위 99%: 28.09 일

## 6. 상관관계 분석

```
            anchor_age     los
anchor_age      1.0000 -0.0371
los            -0.0371  1.0000
```

## 7. 슬라이딩 윈도우 및 클리핑 결정 근거

재원 기간(LOS) 분포를 통해 시간 기반 시퀀스 데이터 생성 시의 상한선을 검토합니다.

- 90% 환자의 LOS: 8.99 일 이내
- 95% 환자의 LOS: 13.89 일 이내
- 99% 환자의 LOS: 28.09 일 이내

> **결론:** LOS 이상치에 의한 모델 왜곡을 방지하기 위해, 슬라이딩 윈도우 생성 시 상위 5% 수준에서 시간축 상한(Clipping)을 두는 것을 권장합니다.

## 8. 시각화 자료
![EDA Plots](EDA_Visualizations.png)
