# 🎯 간소화된 아키텍처 - CI 시스템 연동

## 🏗️ 최종 아키텍처 (간소화)

```
┌─────────────────────────────────────────────────────────────┐
│              Bamboo CI / 다른 CI 시스템                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  1. 빌드 실패 감지                                    │  │
│  │  2. 로그 파일 읽기                                    │  │
│  │  3. Agent에 REST API 요청                            │  │
│  │     POST /analyze                                    │  │
│  │  4. 분석 결과 + 승인 토큰 받음                        │  │
│  │  5. 이메일 전송 (SMTP)                               │  │
│  │     - 개발자: 분석 결과                              │  │
│  │     - 관리자: 분석 결과 + 승인 링크                   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────┬───────────────────────────────────────────┘
                  │ POST /analyze
                  ▼
┌─────────────────────────────────────────────────────────────┐
│         Kubernetes Pod: ci-error-agent                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  FastAPI 서버 (3개 주요 API만)                       │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │  POST /analyze                                  │  │  │
│  │  │  - 분석 실행 (LangGraph)                       │  │  │
│  │  │  - DB 저장                                      │  │  │
│  │  │  - 승인 토큰 생성 (JWT, 7일)                   │  │  │
│  │  │  - 반환: 분석 결과 + approval_url              │  │  │
│  │  │                                                  │  │  │
│  │  │  GET /approve/{token}                           │  │  │
│  │  │  - 토큰 검증                                    │  │  │
│  │  │  - KB에 저장                                    │  │  │
│  │  │  - 확인 페이지 표시                             │  │  │
│  │  │                                                  │  │  │
│  │  │  GET /modify/{token}                            │  │  │
│  │  │  - 수정 페이지 표시                             │  │  │
│  │  │  - 수정 후 KB에 저장                            │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│               PostgreSQL Database                            │
│  - knowledge_base (지식베이스)                              │
│  - analysis_history (분석 이력)                             │
│  - pending_approvals (승인 대기)                            │
└─────────────────────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                  이메일 수신 (관리자)                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  이메일 내용:                                         │  │
│  │  - 오류 분석 결과                                     │  │
│  │  - [✅ 승인] 버튼 → http://agent/approve/{token}     │  │
│  │  - [✏️ 수정] 버튼 → http://agent/modify/{token}      │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 🔄 워크플로우

### 전체 프로세스

```
1. CI 시스템: 빌드 실패
   ↓
2. CI 시스템: 로그 파일 읽기
   ↓
3. CI 시스템 → Agent: POST /analyze
   {
     "ci_log": "...",
     "repository": "automotive-ecu",
     "job_name": "BUILD-COMPILE",
     "build_number": 123
   }
   ↓
4. Agent: LangGraph 분석 실행
   - 증상 추출
   - KB 검색 (신뢰도 ≥0.8이면 웹 검색 생략)
   - 보안 검증
   - 웹 검색 (조건부)
   - LLM 분석
   ↓
5. Agent → CI 시스템: 응답 반환
   {
     "analysis_id": 456,
     "error_type": "tasking",
     "confidence": 0.85,
     "analysis": "분석 결과...",
     "approval_token": "eyJ...",
     "approval_url": "http://agent/approve/eyJ...",
     "modify_url": "http://agent/modify/eyJ...",
     "recommend_save": true
   }
   ↓
6. CI 시스템: 이메일 전송 (SMTP)
   - To: developer@company.com, admin@company.com
   - 내용: 분석 결과 + 승인 링크
   ↓
7. 관리자: 이메일 확인
   ↓
8. 관리자: 승인 링크 클릭
   → GET /approve/{token}
   ↓
9. Agent: KB에 저장
   ↓
10. 웹 페이지: "✅ KB에 저장 완료!" 표시
   ↓
11. 다음 번 동일 오류: KB에서 즉시 찾아서 빠른 답변!
```

## 🎯 주요 변경 사항

### ❌ **제거된 것**
- ~~bamboo-watcher~~ (파일 감시 불필요)
- ~~k8s/bamboo-watcher-deployment.yaml~~
- ~~Agent에서 이메일 전송~~ (CI 시스템에서 담당)

### ✅ **추가된 것**
- **간소화된 API**: `app/main_simple.py`
- **CI 시스템 예시 코드**: `ci_system_example.py`
- **승인 토큰 포함 응답**: `approval_url`, `modify_url`

## 📝 CI 시스템에서 사용법

### Python 예시 (Bamboo Script)

```python
import requests
import os

# 1. 로그 파일 읽기
log_file = "${bamboo.build.working.directory}/build.log"
with open(log_file, 'r') as f:
    ci_log = f.read()

# 2. Agent API 호출
response = requests.post(
    "http://ci-error-agent-service:8000/analyze",
    json={
        "ci_log": ci_log,
        "repository": "${bamboo.planRepository.repositoryUrl}",
        "job_name": "${bamboo.shortJobName}",
        "build_number": int("${bamboo.buildNumber}")
    }
)

result = response.json()

# 3. 이메일 전송 (Bamboo의 이메일 기능 또는 Python SMTP)
import smtplib
from email.mime.text import MIMEText

msg = MIMEText(f"""
오류 타입: {result['error_type']}
신뢰도: {result['confidence']}
분석 결과: {result['analysis']}

KB 저장 승인: {result['approval_url']}
수정 후 승인: {result['modify_url']}
""")

msg['Subject'] = f"CI 오류: {result['error_type']}"
msg['From'] = "ci@company.com"
msg['To'] = "developer@company.com, admin@company.com"

# SMTP 전송
# ...
```

### Shell Script 예시 (Bamboo Shell Task)

```bash
#!/bin/bash

# 로그 파일
LOG_FILE="${bamboo.build.working.directory}/build.log"

# Agent API 호출
RESULT=$(curl -s -X POST http://ci-error-agent-service:8000/analyze \
  -H "Content-Type: application/json" \
  -d "{
    \"ci_log\": \"$(cat $LOG_FILE | jq -Rs .)\",
    \"repository\": \"${bamboo.planRepository.repositoryUrl}\",
    \"job_name\": \"${bamboo.shortJobName}\",
    \"build_number\": ${bamboo.buildNumber}
  }")

# 승인 링크 추출
APPROVAL_URL=$(echo $RESULT | jq -r '.approval_url')

# 이메일 전송 (Bamboo 이메일 기능 사용)
echo "분석 결과: $RESULT" | mail -s "CI 오류" admin@company.com
```

## 📧 이메일 템플릿 (CI 시스템에서 사용)

```html
<!DOCTYPE html>
<html>
<body>
  <h1>🚗 CI 오류 분석 결과</h1>
  
  <p><strong>오류 타입:</strong> {error_type}</p>
  <p><strong>신뢰도:</strong> {confidence}%</p>
  
  <h3>분석 결과:</h3>
  <pre>{analysis}</pre>
  
  <!-- 승인 링크 (신뢰도 높을 때만) -->
  <div style="margin: 30px 0; text-align: center;">
    <h3>이 분석 결과를 KB에 저장하시겠습니까?</h3>
    <a href="{approval_url}" style="padding: 12px 24px; background: #4caf50; color: white; text-decoration: none; border-radius: 5px;">
      ✅ 승인 (KB에 저장)
    </a>
    <a href="{modify_url}" style="padding: 12px 24px; background: #ff9800; color: white; text-decoration: none; border-radius: 5px;">
      ✏️ 수정 후 승인
    </a>
  </div>
  
  <p>링크는 7일 후 만료됩니다.</p>
</body>
</html>
```

## 🚀 배포 (간소화)

```bash
# 1. Secrets
kubectl apply -f k8s/secrets.yaml

# 2. PostgreSQL
kubectl apply -f k8s/postgres.yaml

# 3. Docker 빌드
docker build -t ci-error-agent:latest .

# 4. Agent만 배포 (Watcher 불필요!)
kubectl apply -f k8s/deployment.yaml

# 5. 확인
kubectl get pods
kubectl get svc
```

## 💡 이 구조의 장점

### ✅ **단순성**
- CI 시스템이 모든 것을 제어
- Agent는 순수 분석만 담당
- 파일 감시 불필요

### ✅ **유연성**
- Bamboo뿐 아니라 Jenkins, GitLab CI 등 어떤 CI든 사용 가능
- CI 시스템의 기존 이메일 기능 활용 가능
- REST API만 호출하면 됨

### ✅ **보안**
- CI 시스템 내부에서 로그 처리
- Agent는 승인 링크 처리만
- JWT 토큰 7일 만료

### ✅ **확장성**
- CI 시스템별 커스터마이징 가능
- 이메일 템플릿 자유롭게 수정
- 승인 워크플로우 유연

## 🎯 핵심 포인트

1. **CI 시스템**: 로그 읽기 + API 호출 + 이메일 전송
2. **Agent**: 분석 + 토큰 생성 + 승인 처리
3. **이메일**: 승인 링크 포함 (JWT 토큰)
4. **관리자**: 이메일 링크 클릭 → KB 저장

**가장 간단하고 효과적인 구조입니다!** 🚗✨

