# 데이터 설명

## 데이터 출처
MIMIC-IV (Medical Information Mart for Intensive Care IV)
- PhysioNet DUA 계약 하 사용
- 원본 재배포 금지

## 코호트 구성
| 구분 | 수 |
|------|-----|
| 전체 ICU 입실 | 74,829건 |
| 성인 환자 (≥18세) | 74,829명 |
| Sepsis-3 충족 (최종 코호트) | 18,001명 (33.0%) |
| 초회 입실 | 54,551명 (72.9%) |
| 재입실 | 20,278명 (27.1%) |
| 생존 | 65,899명 (88.1%) |
| 사망 | 8,930명 (11.9%) |

## 피처 소스
| 분류 | 항목 | 집계 방식 |
|------|------|----------|
| Vital | HR, RR, SpO2, Temp, BP | MEDIAN/MIN/Latest |
| Lab | Lactate, Creatinine, WBC, Platelets 등 | MAX/MEDIAN |
| Intervention | 기계환기, 승압제, 소변량 | FLAG/MAX |
| GCS | Eye, Verbal, Motor, Total | Hourly & MIN |

> ⚠️ 원본 데이터는 PhysioNet DUA 계약에 따라 이 레포에 포함되어 있지 않습니다.
> 데이터 접근은 https://physionet.org/content/mimiciv/ 에서 승인 후 가능합니다.
