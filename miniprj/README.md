# Early Deterioration Command Center

MIMIC-IV 기반 중환자 조기 악화 예측 + NLP(RAG/LLM) 활용 의사결정 지원 대시보드

## 프로젝트 개요

ICU 환자의 조기 악화를 예측하고, 의료진에게 실시간 위험도와 대응 가이드라인을 제공하는 임상 의사결정 지원 시스템(CDSS)

### 핵심 기능

1. **Multi-Outcome 예측**: 사망(24h), 기계환기 시작(12/24h), 승압제 시작(12/24h)
2. **위험도 대시보드**: 환자별 실시간 위험도 시각화
3. **LLM 기반 요약**: SHAP 결과를 의료진/보호자용 자연어로 번역
4. **RAG 가이드라인**: 대한 학회 프로토콜 기반 체크리스트 제안
5. **데이터 품질 알림**: 센서 이상/결측 감지

## 기술 스택

| 컴포넌트   | 기술                |
| ---------- | ------------------- |
| Frontend   | React, Chart.js     |
| Backend    | Express (Node.js)   |
| ML Service | Flask (Python)      |
| Database   | Oracle DB           |
| Vector DB  | Supabase (pgvector) |
| LLM        |                     |

## 디렉토리 구조

```
early-deterioration-center/
├── backend/          # Express API 서버
├── ml-service/       # Flask 모델 서빙
├── ml-training/      # 모델 훈련 코드
├── data-pipeline/    # SQL 쿼리, 전처리 스크립트
├── airflow/          # 파이프라인 오케스트레이션
├── frontend/         # React 대시보드
├── rag/              # RAG 문서, 프롬프트
├── utils/            # 공용 유틸리티
└── docs/             # 문서
```

## 역할 분담

| 역할            | 담당 폴더                             |
| --------------- | ------------------------------------- |
| Backend + Infra | `backend/`, `ml-service/`, `airflow/` |
| NLP + Frontend  | `frontend/`, `rag/`                   |
| Data Engineer   | `data-pipeline/`                      |
| ML Engineer     | `ml-training/`                        |

## 시작하기

### 1. 레포 클론

```bash
git clone https://github.com/oracle-fire4bird/miniprj.git
cd miniprj
```

### 2. Python 환경 설정

```bash
conda create -n miniprj python=3.10
conda activate miniprj
pip install -r requirements.txt
```

### 3. Node.js 환경 설정

```bash
cd backend
npm install

cd ../frontend
npm install
```

### 4. 환경 변수 설정

```bash
cp .env.example .env
# .env 파일 열어서 실제 값 입력
```

## API 엔드포인트

| Endpoint                   | Method | 설명            |
| -------------------------- | ------ | --------------- |
| `/api/patients`            | GET    | 환자 목록       |
| `/api/patient/:id`         | GET    | 환자 상세       |
| `/api/patient/:id/risk`    | GET    | 위험도 조회     |
| `/api/predict`             | POST   | 예측 요청       |
| `/api/patient/:id/summary` | GET    | AI 요약         |
| `/api/guidelines/suggest`  | GET    | 가이드라인 제안 |
