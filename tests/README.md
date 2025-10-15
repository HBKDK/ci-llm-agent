# 🧪 Pytest 테스트

## 📦 사용하는 패키지

- **pytest**: Python 테스트 프레임워크
- **pytest-asyncio**: 비동기 테스트 지원
- **pytest-cov**: 코드 커버리지 측정
- **httpx**: 비동기 HTTP 클라이언트

## 🚀 빠른 테스트

### 모든 테스트 실행
```cmd
pytest
```

### 특정 테스트 실행
```cmd
# 증상 추출 테스트
pytest tests/test_symptoms.py

# KB 테스트
pytest tests/test_kb.py

# 워크플로우 테스트
pytest tests/test_workflow.py

# API 테스트
pytest tests/test_api_endpoints.py

# JWT 테스트
pytest tests/test_jwt.py
```

### 상세 출력
```cmd
# 상세 모드
pytest -v

# 출력 보기
pytest -s

# 커버리지 포함
pytest --cov=app --cov-report=html
```

## 📊 테스트 구조

```
tests/
├── conftest.py              # Pytest 설정 및 fixtures
├── test_symptoms.py         # 증상 추출 테스트 (5개)
├── test_kb.py              # KB 관리 테스트 (5개)
├── test_workflow.py        # LangGraph 워크플로우 (7개)
├── test_api_endpoints.py   # FastAPI 엔드포인트 (5개)
├── test_jwt.py             # JWT 토큰 (4개)
└── README.md               # 이 파일
```

## ✅ 테스트 항목

### test_symptoms.py
- ✅ Tasking 로그 증상 추출
- ✅ NXP 로그 증상 추출
- ✅ Polyspace 로그 증상 추출
- ✅ 빈 로그 처리
- ✅ 오류 없는 로그 (fallback)

### test_kb.py
- ✅ KB 초기화
- ✅ KB 검색
- ✅ KB 추가
- ✅ 중복 감지

### test_workflow.py
- ✅ 오류 타입 분류
- ✅ KB 신뢰도 계산
- ✅ 보안 검증
- ✅ 자동차 SW 관련성
- ✅ 전체 분석 워크플로우
- ✅ N8N 워크플로우 호출 테스트

### test_api_endpoints.py
- ✅ 루트 엔드포인트
- ✅ 헬스 체크
- ✅ 분석 API
- ✅ Validation 오류
- ✅ KB 목록 조회

### test_jwt.py
- ✅ 토큰 생성
- ✅ 토큰 검증
- ✅ 잘못된 토큰
- ✅ 만료 시간 확인

## 🎯 예상 결과

```
======================== test session starts ========================
collected 26 items

tests/test_symptoms.py .....                                  [ 19%]
tests/test_kb.py .....                                        [ 38%]
tests/test_workflow.py .......                                [ 65%]
tests/test_api_endpoints.py .....                             [ 84%]
tests/test_jwt.py ....                                        [100%]

======================== 26 passed in 5.23s ========================
```

## 🚀 실행 방법

```cmd
# 1. Pytest 설치
pip install pytest pytest-asyncio pytest-cov

# 2. 모든 테스트 실행
pytest

# 3. 상세 출력
pytest -v -s

# 4. 커버리지 리포트
pytest --cov=app --cov-report=html
# 결과: htmlcov/index.html 생성
```

이제 **전문적인 pytest 기반 테스트**가 준비되었습니다! 🧪✨
