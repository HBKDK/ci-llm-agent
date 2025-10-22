# Local LLM Server 가이드

로컬 Python LLM 서버를 사용하여 CI 오류 분석을 수행하는 방법입니다.

## 📋 개요

- **목적**: 로컬 PC에서 Azure OpenAI API를 사용하여 LLM 분석 수행
- **기술**: FastAPI + Azure OpenAI API
- **포트**: 5678
- **엔드포인트**: `/webhook/llm-analyze`

## 🚀 빠른 시작

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. Azure OpenAI API 설정

**방법 1: 환경변수 (권장)**
```bash
# Windows
set AZURE_OPENAI_API_KEY=your-azure-openai-api-key-here
set AZURE_OPENAI_BASE_URL=https://your-resource-name.openai.azure.com
set AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4.1-mini
set AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Linux/Mac
export AZURE_OPENAI_API_KEY=your-azure-openai-api-key-here
export AZURE_OPENAI_BASE_URL=https://your-resource-name.openai.azure.com
export AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4.1-mini
export AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

**방법 2: 설정 파일**
`local_llm_server_config.yaml` 파일에서:
```yaml
azure_openai:
  api_key: "your-azure-openai-api-key-here"
  base_url: "https://your-resource-name.openai.azure.com"
  deployment_name: "gpt-4.1-mini"
  api_version: "2024-02-15-preview"
```

### 3. 서버 실행

```bash
python local_llm_server.py
```

서버가 시작되면 다음 메시지가 표시됩니다:
```
INFO:     로컬 LLM 서버 시작: http://0.0.0.0:5678
INFO:     Azure OpenAI 모델: gpt-4.1-mini
```

## ⚙️ 설정

### local_llm_server_config.yaml

```yaml
# Azure OpenAI 설정
azure_openai:
  deployment_name: "gpt-4.1-mini"  # gpt-4, gpt-35-turbo 등으로 변경 가능
  temperature: 0.2                 # 0.0 ~ 1.0 (낮을수록 일관성 높음)
  max_tokens: 4096                 # 최대 응답 길이

# 서버 설정
server:
  port: 5678              # 서버 포트
  host: "0.0.0.0"         # 0.0.0.0: 모든 인터페이스, 127.0.0.1: 로컬만
  timeout: 30             # 요청 타임아웃 (초)
```

### 모델 변경

다른 Azure OpenAI 모델을 사용하려면:

```yaml
azure_openai:
  deployment_name: "gpt-4"  # 더 정확하지만 비용 높음
  # 또는
  deployment_name: "gpt-35-turbo"  # 빠르고 비용 효율적
```

## 🔧 K8s 연동 설정

### 1. 로컬 PC IP 확인

```bash
# Windows
ipconfig

# Linux/Mac
ifconfig
# 또는
ip addr show
```

### 2. k8s/secrets.yaml 수정

```yaml
data:
  # 로컬 LLM 서버 설정 (n8n 대체)
  n8n-webhook-url: "http://192.168.1.100:5678/webhook/llm-analyze"  # 실제 IP로 변경
  n8n-timeout-seconds: "30"
```

**중요**: `YOUR_LOCAL_PC_IP`를 실제 로컬 PC IP 주소로 변경하세요.

### 3. K8s ConfigMap 업데이트

```bash
kubectl apply -f k8s/secrets.yaml
```

## 🧪 테스트

### 1. 서버 상태 확인

```bash
curl http://localhost:5678/
```

응답:
```json
{
  "status": "running",
  "service": "Local LLM Server",
  "version": "1.0.0",
  "openai_configured": true
}
```

### 2. 헬스 체크

```bash
curl http://localhost:5678/health
```

응답:
```json
{
  "status": "healthy",
  "openai_available": true
}
```

### 3. LLM 분석 테스트

```bash
curl -X POST http://localhost:5678/webhook/llm-analyze \
  -H "Content-Type: application/json" \
  -d '{
    "ci_log": "Build failed: npm install error",
    "symptoms": ["npm install failed", "dependency resolution error"],
    "error_type": "build",
    "context": "Node.js project",
    "repository": "my-project"
  }'
```

### 4. Azure OpenAI 직접 테스트 (참고용)

로컬 서버를 거치지 않고 Azure OpenAI API를 직접 테스트하려면:

```bash
curl --request POST \
  --url https://your-resource-name.openai.azure.com/openai/deployments/gpt-4.1-mini/chat/completions?api-version=2024-02-15-preview \
  --header 'Content-Type: application/json' \
  --header 'api-key: your-azure-openai-api-key' \
  --data '{
    "max_tokens": 4096,
    "messages": [
      {
        "role": "user",
        "content": "hello"
      }
    ]
  }'
```

## 🔍 API 스펙

### POST /webhook/llm-analyze

**요청 형식:**
```json
{
  "ci_log": "string",        // CI 로그 텍스트
  "symptoms": ["string"],    // 추출된 증상 리스트
  "error_type": "string",    // 오류 타입
  "context": "string",       // 추가 컨텍스트 (선택)
  "repository": "string"     // 저장소 이름 (선택)
}
```

**응답 형식:**
```json
{
  "analysis": "string",      // 마크다운 형식의 분석 결과
  "confidence": 0.85         // 신뢰도 (0.0 ~ 1.0)
}
```

## 🐛 문제 해결

### Azure OpenAI API 키 오류
```
⚠️ Azure OpenAI API 키 또는 Base URL이 설정되지 않았습니다!
```
**해결**: 환경변수 `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_BASE_URL` 설정 또는 설정 파일에서 확인

### 연결 실패
```
로컬 서버 연결 실패
```
**해결**: 
1. 로컬 서버가 실행 중인지 확인
2. k8s ConfigMap의 IP 주소가 올바른지 확인
3. 방화벽 설정 확인

### 타임아웃 오류
```
webhook 타임아웃 (30초)
```
**해결**: 
1. 설정 파일에서 `timeout` 값 증가
2. Azure OpenAI API 응답 속도 확인

## 📊 모니터링

### 로그 확인

서버 실행 시 콘솔에 다음 로그가 표시됩니다:
```
INFO:     CI 오류 분석 요청: build
INFO:     분석 완료: 신뢰도 0.85
```

### 성능 최적화

- **모델 선택**: `gpt-35-turbo` (빠름, 저렴) vs `gpt-4` (정확함, 비쌈)
- **토큰 제한**: `max_tokens` 조정으로 응답 길이 제어 (기본값: 4096)
- **온도 설정**: `temperature` 0.2 (일관성) vs 0.7 (창의성)

## 🔄 기존 시스템에서 마이그레이션

기존 외부 LLM 서비스를 사용 중이었다면:

1. **기존 서버 중지**
2. **로컬 LLM 서버 시작**
3. **k8s ConfigMap URL 변경**
4. **테스트 수행**

기존 API 인터페이스와 호환되므로 기존 코드 변경 불필요합니다.

