# n8n LLM 워크플로우 설정 가이드

## 개요

K8s CI Agent에서 n8n을 통해 Azure OpenAI 분석을 수행하는 워크플로우 설정 방법입니다.

## 아키텍처

```
CI (Bamboo) → K8s App → KB Search
                  ↓ (if KB miss)
                n8n Webhook → Azure OpenAI
                  ↓
            K8s App ← LLM Result
                  ↓
               CI Response
```

## n8n 워크플로우 구성

### 1. 웹훅 트리거 생성

1. n8n에서 새 워크플로우 생성
2. **Webhook** 노드 추가
3. 웹훅 설정:
   - **HTTP Method**: POST
   - **Path**: `/webhook/llm-analyze`
   - **Response Mode**: "On Received"
   - **Response Data**: "All Incoming Items"

### 2. 데이터 전처리 노드 (선택사항)

**Function** 노드를 추가하여 요청 데이터 정리:

```javascript
// 요청 데이터 정리 및 검증
const inputData = $input.first().json;

return {
  json: {
    ci_log: inputData.ci_log || "",
    symptoms: inputData.symptoms || [],
    error_type: inputData.error_type || "unknown",
    context: inputData.context || "",
    repository: inputData.repository || ""
  }
};
```

### 3. Azure OpenAI 호출 노드

**HTTP Request** 노드를 추가하여 Azure OpenAI 호출:

#### 설정:
- **Method**: POST
- **URL**: `{{ $env.AZURE_OPENAI_ENDPOINT }}/openai/deployments/{{ $env.AZURE_OPENAI_DEPLOYMENT_NAME }}/chat/completions?api-version={{ $env.AZURE_OPENAI_API_VERSION }}`
- **Headers**:
  ```
  Content-Type: application/json
  api-key: {{ $env.AZURE_OPENAI_API_KEY }}
  ```
- **Body** (JSON):
```json
{
  "messages": [
    {
      "role": "system",
      "content": "당신은 자동차 소프트웨어 CI/CD 오류 분석 전문가입니다. Tasking, NXP, Polyspace, Simulink, AUTOSAR, CAN 등의 도구에서 발생하는 오류를 분석하고 해결책을 제시하세요. 한국어로 답변하세요."
    },
    {
      "role": "user",
      "content": "CI 로그:\n{{ $json.ci_log }}\n\n증상:\n{{ $json.symptoms.join('\\n') }}\n\n오류 타입: {{ $json.error_type }}\n\n컨텍스트: {{ $json.context }}"
    }
  ],
  "temperature": 0.2,
  "max_tokens": 1000
}
```

### 4. 응답 처리 노드

**Function** 노드를 추가하여 LLM 응답을 K8s App 형식으로 변환:

```javascript
// LLM 응답 처리
const llmResponse = $input.first().json;
const analysis = llmResponse.choices[0].message.content;

// 신뢰도 계산 (간단한 휴리스틱)
const confidence = analysis.length > 100 ? 0.8 : 0.6;

return {
  json: {
    analysis: analysis,
    confidence: confidence
  }
};
```

### 5. HTTP 응답 노드

**Respond to Webhook** 노드를 추가:

- **Response Code**: 200
- **Response Body** (JSON):
```json
{
  "analysis": "{{ $json.analysis }}",
  "confidence": {{ $json.confidence }}
}
```

## 환경변수 설정

n8n 워크플로우에서 사용할 환경변수:

```bash
# .env 파일 또는 n8n 환경변수 설정
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com
AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment-name
AZURE_OPENAI_API_KEY=your-azure-openai-api-key
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

## API 계약

### K8s App → n8n 요청

```json
{
  "ci_log": "tasking compiler error: undefined reference to 'main'",
  "symptoms": ["tasking compiler", "undefined reference", "main function"],
  "error_type": "tasking",
  "context": "automotive sw build",
  "repository": "ecu-firmware"
}
```

### n8n → K8s App 응답

```json
{
  "analysis": "Tasking 컴파일러에서 'main' 함수를 찾을 수 없다는 오류입니다. 이는 일반적으로 다음 원인으로 발생합니다:\n\n1. main.c 파일이 빌드에 포함되지 않음\n2. 링커 스크립트에서 진입점 설정 오류\n3. 라이브러리 경로 문제\n\n해결방법:\n- 프로젝트 설정에서 main.c 파일이 소스에 포함되어 있는지 확인\n- 링커 스크립트에서 ENTRY(_start) 또는 ENTRY(main) 설정 확인\n- 라이브러리 경로와 링킹 순서 점검",
  "confidence": 0.85
}
```

## 테스트 방법

### 1. 워크플로우 테스트

n8n에서 **Execute Workflow** 버튼을 클릭하여 테스트:

```json
{
  "ci_log": "tasking compiler error: undefined reference to 'main'",
  "symptoms": ["tasking", "compiler", "undefined reference"],
  "error_type": "tasking",
  "context": "test",
  "repository": "test-repo"
}
```

### 2. K8s App 연동 테스트

```bash
curl -X POST http://k8s-app-ip:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "ci_log": "tasking compiler error: undefined reference to main",
    "context": "automotive sw build",
    "repository": "ecu-firmware"
  }'
```

## 오류 처리

### 타임아웃 설정
- n8n 워크플로우 타임아웃: 30초
- HTTP Request 노드 타임아웃: 25초

### 에러 응답
n8n에서 오류 발생시:

```json
{
  "error": "LLM 분석 실패",
  "detail": "Connection timeout"
}
```

## 보안 고려사항

1. **API 키 보안**: 환경변수로 관리
2. **네트워크 접근**: Private LLM 서버는 내부 네트워크에서만 접근 가능
3. **로그 필터링**: 민감한 정보는 로그에서 제외
4. **인증**: 필요시 n8n webhook에 인증 추가

## 모니터링

### n8n 워크플로우 모니터링
- 실행 로그 확인
- 성공/실패 통계
- 응답 시간 모니터링

### K8s App 로그 확인
```bash
kubectl logs -f deployment/ci-error-agent
```

로그에서 다음 메시지 확인:
- `🔄 n8n webhook 호출`
- `✅ n8n LLM 분석 완료`
- `⚠️ n8n webhook 에러`

## 트러블슈팅

### 자주 발생하는 문제

1. **연결 실패**
   - Azure OpenAI 서비스 상태 확인
   - 네트워크 연결 확인
   - API 키 유효성 확인
   - 엔드포인트 URL 정확성 확인

2. **타임아웃**
   - Azure OpenAI 서비스 성능 확인
   - 요청 복잡도 줄이기
   - 타임아웃 시간 조정

3. **응답 형식 오류**
   - Azure OpenAI 응답 JSON 형식 확인
   - n8n Function 노드 로직 점검

4. **인증 오류**
   - Azure OpenAI API 키 확인
   - 배포 이름 정확성 확인
   - API 버전 호환성 확인

### 로그 확인 명령어

```bash
# n8n 로그
docker logs n8n-container

# K8s App 로그
kubectl logs deployment/ci-error-agent

# Azure OpenAI 로그 (Azure Portal에서 확인)
# 또는 Azure CLI로 확인
az monitor activity-log list --resource-group your-resource-group
```
