# 🚗 CI 오류 분석 에이전트 (자동차 SW 특화)

LangGraph 기반 CI 오류 자동 분석 및 해결책 제시 시스템

## 📝 개요

Bamboo CI에서 발생하는 자동차 SW 빌드 오류를 자동으로 분석하고, Knowledge Base 학습을 통해 지속적으로 개선되는 AI 에이전트입니다.

### 주요 기능
- 🤖 **LangGraph 워크플로우** - 증상 추출 → KB 검색 → LLM 분석
- 🚗 **자동차 SW 특화** - Tasking, NXP, Polyspace, Simulink, AUTOSAR, CAN
- 📚 **Knowledge Base** - 학습 및 검색 시스템
- 🔒 **보안 우선** - 내부 데이터만 사용
- 🔧 **Private LLM** - 사내 LLM 지원
- ✅ **수정 후 승인** - 관리자가 답변 수정 후 KB 저장

## ⚡ 빠른 시작

### 설치
```bash
# 의존성 설치
python -m pip install -r requirements.txt

# 서버 실행
python start_server.py

# 브라우저 접속
http://localhost:8000/docs
```

### 테스트
```bash
# 통합 테스트
python test_all_features.py

# Pytest
python -m pytest tests/ -v
```

## 🔄 워크플로우

```
CI 오류 발생
    ↓
POST /analyze (REST API)
    ↓
┌─────────────────────────────┐
│  LangGraph 워크플로우        │
│                             │
│  1. 증상 추출                │
│     ↓                       │
│  2. KB 검색                  │
│     ↓                       │
│  3. LLM 분석                 │
└─────────────────────────────┘
    ↓
Response (분석 + 승인 토큰)
    ↓
CI 시스템이 이메일 전송
    ├─ ✅ 바로 저장
    └─ ✏️ 수정 후 저장
    ↓
관리자 승인
    ↓
KB에 저장 → 다음 분석부터 활용
```

상세한 다이어그램은 **`WORKFLOW_DIAGRAM.md`** 참고

## ☸️ Kubernetes 배포

### 1. 설정 파일 수정
```yaml
# k8s/secrets.yaml
# - PostgreSQL password
# - JWT secret (64자+)
# - Private LLM API key
# - base-url: http://<node-ip>:30800
# - private-llm-base-url: http://<llm-server>:8000/v1
```

### 2. 배포
```bash
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/postgres.yaml
# PostgreSQL Ready 대기...
kubectl apply -f k8s/deployment.yaml
```

### 3. 접속
```
http://<node-ip>:30800/docs
```

자세한 배포 가이드는 **`DEPLOYMENT.md`** 참고

## 📚 API 엔드포인트

### 분석
- **POST /analyze** - CI 오류 분석
- **GET /health** - 헬스 체크

### 승인
- **GET /approve/{token}** - KB에 바로 저장
- **GET /modify/{token}** - 수정 폼 페이지
- **POST /api/modify/{token}** - 수정 내용 저장

### KB 관리
- **GET /kb/list** - KB 목록 조회
- **POST /kb/add** - KB 추가
- **PUT /kb/{id}** - KB 수정
- **DELETE /kb/{id}** - KB 삭제

## 🔧 Private LLM 설정

```python
# start_server.py 또는 환경변수
os.environ["LLM_PROVIDER"] = "private"
os.environ["PRIVATE_LLM_BASE_URL"] = "http://your-llm:8000/v1"
os.environ["PRIVATE_LLM_MODEL"] = "llama-3-70b"
os.environ["PRIVATE_LLM_API_KEY"] = "your-api-key"
```

자세한 설정은 **`PRIVATE_LLM_SETUP.md`** 참고

## 🧪 테스트

```bash
# 전체 테스트
python test_all_features.py

# Pytest
python -m pytest tests/ -v

# 특정 테스트
python -m pytest tests/test_workflow.py -v
```

## 📖 문서

- **DEPLOYMENT.md** - K8s 배포 가이드
- **WORKFLOW_DIAGRAM.md** - 워크플로우 다이어그램
- **PRIVATE_LLM_SETUP.md** - Private LLM 설정
- **SIMPLIFIED_ARCHITECTURE.md** - 시스템 아키텍처
- **ci_system_example.py** - CI 연동 예시 코드
- **tests/README.md** - 테스트 가이드

## 🛠️ 기술 스택

- **Backend**: FastAPI, Uvicorn
- **AI**: LangGraph, LangChain, OpenAI
- **DB**: SQLAlchemy, SQLite/PostgreSQL
- **Auth**: JWT (PyJWT)
- **Container**: Docker, Kubernetes
- **Test**: Pytest

## 🚗 지원 도구

1. **Tasking Compiler** (C166, C251, CARM)
2. **NXP S32** Design Studio
3. **Polyspace** Bug Finder
4. **MATLAB Simulink**
5. **AUTOSAR**
6. **CAN Tools**

## 📊 프로젝트 구조

```
ci_agent/
├── app/                      # 애플리케이션 코드
│   ├── main_simple.py       # FastAPI 서버
│   ├── db/                  # 데이터베이스
│   ├── auth/                # JWT 인증
│   ├── graph/               # LangGraph 워크플로우
│   ├── kb/                  # Knowledge Base
│   ├── llm/                 # LLM Provider
│   ├── search/              # 웹 검색 (미사용)
│   └── utils/               # 유틸리티
├── tests/                   # Pytest 테스트 (25개)
├── k8s/                     # Kubernetes 배포
├── data/seed_kb.json        # 초기 KB 데이터
├── start_server.py          # 서버 실행
├── test_all_features.py     # 통합 테스트
├── ci_error_agent.py        # 클래스 인터페이스
├── ci_system_example.py     # CI 연동 예시
├── requirements.txt         # 패키지 목록
├── Dockerfile               # Docker 이미지
└── .gitignore               # Git 설정
```

## 🎉 라이센스

이 프로젝트는 내부 사용을 위해 개발되었습니다.

---

**자세한 내용은 각 문서를 참고하세요!** 🚗✨