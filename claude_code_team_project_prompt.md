# Claude Code 실행 프롬프트 — 팀 프로젝트 포트폴리오 레포 구성

## 📌 상황 설명

나는 김예지(kyjwise7-hub)이고, 데이터 분석 신입 취업 준비 중이야.

오라클 아카데미에서 6인 팀 프로젝트로 감염병 모니터링 시스템 **LOOK**을 개발했어.
팀 공용 레포는 **Private**(Seungmin-L 소유)이라 외부에서 접근 불가해.

팀 레포 폴더 구조는 이렇게 생겼어:
```
팀 레포 (Private, Seungmin-L 소유)
├── backend/
├── data/
├── deployment/
├── emr-generator/
├── frontend/
├── ml/          ← 내가 참여한 모듈
├── nlp/         ← 내가 참여한 모듈
├── rag/
└── .env.example
```

나는 이 중에서 **ml/** 과 **nlp/** 모듈에 참여했고,
내 개인 GitHub에 포트폴리오용 레포 2개를 만들어서 **내 기여분만** 정리하려고 해.

---

## 🎯 해야 할 작업

### 작업 1: `mimic-iv-deterioration-prediction` 레포 README 수정

이 레포는 이미 로컬에 폴더가 있고 README.md 초안도 작성되어 있어.
README 상단에 아래 "팀 프로젝트 컨텍스트" 섹션을 **기존 내용 위에** 추가해줘.

**추가할 내용:**

```markdown
> **📢 팀 프로젝트 안내**
> 이 프로젝트는 오라클 아카데미 6인 팀으로 개발한 감염병 모니터링 시스템 **LOOK**의 ML 모듈입니다.
> 팀 공용 레포는 Private이므로, 본 레포에 제가 담당한 코드·설계문서·실험결과를 별도로 정리했습니다.
>
> - 🏥 **전체 시스템**: WATCH(위험 필터링) → EXPLAIN(타임라인·AI 요약·Sepsis ML) → ACT(병상배치·체크리스트·RAG·문서자동화)
> - 🧑‍💻 **나의 역할**: ML Team — Data Lead / Scientist
> - 👥 **팀 구성**: 총 6명 (ML 2명, NLP 2명, Frontend 1명, Backend 1명)
```

그리고 README 안에 "나의 주요 기여" 섹션이 없으면 아래 내용으로 추가해줘 (있으면 병합):

```markdown
## 🎯 나의 주요 기여

| 영역 | 상세 |
|------|------|
| 전처리 파이프라인 | Sepsis-3 코호트 정의, 54,551명 → 18,001명 필터링 |
| 피처 엔지니어링 | 6시간 슬라이딩 윈도우, Delta/Slope 추세변수, Shock Index·NEWS·MEWS 복합지표 |
| 결측치 전략 | 임상적 재해석 기반 결측치 처리 (단순 imputation 아님) |
| 모델링 | XGBoost 기반 4개 타겟 예측 (사망 AUROC 0.916) |
| 해석 | SHAP 기반 변수 중요도 분석 |
```

---

### 작업 2: `clinical-nlp-look` 레포 README 수정

마찬가지로 이미 로컬에 폴더가 있고 README.md 초안도 있어.
README 상단에 아래 "팀 프로젝트 컨텍스트" 섹션을 **기존 내용 위에** 추가해줘.

**추가할 내용:**

```markdown
> **📢 팀 프로젝트 안내**
> 이 프로젝트는 오라클 아카데미 6인 팀으로 개발한 감염병 모니터링 시스템 **LOOK**의 NLP 모듈입니다.
> 팀 공용 레포는 Private이므로, 본 레포에 제가 담당한 코드·설계문서·실험결과를 별도로 정리했습니다.
>
> - 🏥 **전체 시스템**: WATCH(위험 필터링) → EXPLAIN(타임라인·AI 요약·Sepsis ML) → ACT(병상배치·체크리스트·RAG·문서자동화)
> - 🧑‍💻 **나의 역할**: AI Researcher · Data Scientist
> - 👥 **팀 구성**: 총 6명 (ML 2명, NLP 2명, Frontend 1명, Backend 1명)
```

그리고 "나의 주요 기여" 섹션이 없으면 추가 (있으면 병합):

```markdown
## 🎯 나의 주요 기여

| 영역 | 상세 |
|------|------|
| NLP 파이프라인 설계 | 5단계 구조 (Document Parser → Rule-Based Extractor → KM-BERT NER → Norm & Validation → Axis Snapshot & Trajectory) |
| 합성데이터 설계 | MIMIC-IV 10명 + 순수합성 3명 = 13명, 558개 문서, 52종 슬롯 |
| 정보추출 로직 | KM-BERT NER + Rule-Based 하이브리드 방식 구현 |
| 성능 | 전체 F1 0.86 달성 |
| 현장 검증 | 의료진 5명 평가 — 환자안전 기여 100%, 도입의향 80% |
```

---

### 작업 3: 두 레포 모두에 `src/` 폴더 준비

각 레포에 `src/` 폴더가 없으면 만들고, 안에 `README.md`를 넣어줘:

**`mimic-iv-deterioration-prediction/src/README.md`:**
```markdown
# 소스 코드

팀 공용 레포(Private)에서 본인 기여분 코드를 정리하여 업로드 예정입니다.

## 업로드 예정 파일
- 전처리 파이프라인 코드
- 피처 엔지니어링 코드
- 모델 학습 및 평가 코드
- SHAP 분석 코드
```

**`clinical-nlp-look/src/README.md`:**
```markdown
# 소스 코드

팀 공용 레포(Private)에서 본인 기여분 코드를 정리하여 업로드 예정입니다.

## 업로드 예정 파일
- NLP 파이프라인 코드 (5단계)
- 합성데이터 생성 스크립트
- 평가 및 검증 코드
```

---

### 작업 4: 두 레포의 프로젝트 간 연결 명시

**`mimic-iv-deterioration-prediction/README.md`** 하단에 추가:
```markdown
## 🔗 관련 프로젝트

이 미니프로젝트의 Sepsis ML 모듈은 최종 프로젝트 LOOK에 통합·발전되었습니다.
→ [clinical-nlp-look](https://github.com/kyjwise7-hub/clinical-nlp-look)
```

**`clinical-nlp-look/README.md`** 하단에 추가:
```markdown
## 🔗 관련 프로젝트

LOOK의 Sepsis ML 모듈은 아래 미니프로젝트에서 시작되어 발전한 것입니다.
→ [mimic-iv-deterioration-prediction](https://github.com/kyjwise7-hub/mimic-iv-deterioration-prediction)
```

---

## ⚙️ 실행 조건

- 이미 존재하는 README.md 내용은 **삭제하지 말고**, 위 내용을 적절한 위치에 **삽입/병합**해줘
- 기존 `docs/` 폴더(feature_engineering.md, pipeline_design.md 등)는 건드리지 마
- git add + commit 해줘. 커밋 메시지:
  - `mimic-iv-deterioration-prediction`: `docs: add team project context and contribution summary`
  - `clinical-nlp-look`: `docs: add team project context and contribution summary`
- **push는 하지 마** (내가 확인 후 수동으로 push할게)

---

## ✅ 완료 후 체크리스트

작업 끝나면 아래 항목 확인해서 알려줘:
- [ ] mimic 레포 README 상단에 팀 프로젝트 안내 블록 있음
- [ ] mimic 레포 README에 "나의 주요 기여" 테이블 있음
- [ ] mimic 레포 README 하단에 관련 프로젝트 링크 있음
- [ ] mimic 레포 src/README.md 생성됨
- [ ] clinical 레포 README 상단에 팀 프로젝트 안내 블록 있음
- [ ] clinical 레포 README에 "나의 주요 기여" 테이블 있음
- [ ] clinical 레포 README 하단에 관련 프로젝트 링크 있음
- [ ] clinical 레포 src/README.md 생성됨
- [ ] 두 레포 모두 커밋 완료 (push는 안 함)
