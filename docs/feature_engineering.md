# 피처 엔지니어링 설계 문서

## 슬라이딩 윈도우
- 크기: 6시간
- 간격: 1시간
- 목적: 재원기간 편차(중앙값 2.37일 ~ 최대 226일) 정규화

## 결측치 처리 원칙
- 결측치를 '측정 실패'가 아닌 '해당 처치가 미시행'으로 해석
- lactate 미측정 → `lactate_missing` 플래그 생성
- ABGA 미시행 → `abga_checked` 플래그 생성

## 추세 변수 (Delta & Slope)
같은 수치라도 안정적 유지 vs 급격한 하락은 위험도가 다름
- Delta: 윈도우 내 최댓값 - 최솟값
- Slope: 선형회귀 기울기

적용 대상: HR, SBP, SpO2, Lactate, GCS Total

## 임상 복합지표
- Shock Index = HR / SBP
- MEWS (Modified Early Warning Score)
- NEWS (National Early Warning Score)

## 최종 피처 (41개)
Vitals 7 + Vitals 통계 4 + Labs 6 + GCS 4 + Urine 3 + 파생 4 + Flags 3 + Delta 5 + Slope 5
