# n8n 워크플로우 설정 가이드

## 🚀 빠른 설정

### 1. 워크플로우 Import
1. n8n UI 접속: `http://your-n8n-server:5678`
2. **Workflows** → **Import from File**
3. `ci-llm-analyzer.json` 파일 선택
4. Import 완료 후 워크플로우 활성화

### 2. 환경변수 설정
n8n 서버에서 다음 환경변수 설정:

```bash
# Private LLM 서버 URL
export PRIVATE_LLM_URL="http://your-llm-server:8000/v1/chat/completions"

# LLM 모델명
export PRIVATE_LLM_MODEL="llama-3-70b"

# API 키 (필요한 경우)
export PRIVATE_LLM_API_KEY="your-api-key"
```

### 3. 웹훅 URL 확인
워크플로우 활성화 후 다음 URL이 생성됩니다:
```
http://your-n8n-server:5678/webhook/llm-analyze
```

## 🔧 상세 설정

### 워크플로우 노드 설명

#### 1. Webhook 노드
- **Path**: `llm-analyze`
- **Method**: `POST`
- **Response Mode**: `On Received`

#### 2. 전처리 노드 (Code)
입력 데이터를 정리하고 검증합니다:
```javascript
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

#### 3. Private LLM 호출 노드 (HTTP Request)
- **URL**: `{{ $env.PRIVATE_LLM_URL }}`
- **Method**: `POST`
- **Headers**: `Content-Type: application/json`
- **Body**: JSON 형식의 LLM 요청

#### 4. 후처리 노드 (Code)
LLM 응답을 처리하고 신뢰도를 계산합니다:
```javascript
const llmResponse = $input.first().json;
const analysis = llmResponse.choices?.[0]?.message?.content || "분석 결과를 가져올 수 없습니다.";

// 신뢰도 계산 로직
let confidence = 0.5;
if (analysis.length > 200) {
  confidence = 0.85;
} else if (analysis.length > 100) {
  confidence = 0.75;
} else if (analysis.length > 50) {
  confidence = 0.6;
}

// 자동차 SW 키워드 확인
const errorKeywords = ['tasking', 'nxp', 'polyspace', 'simulink', 'autosar', 'can'];
const hasKeyword = errorKeywords.some(keyword => 
  analysis.toLowerCase().includes(keyword)
);

if (hasKeyword) {
  confidence = Math.min(confidence + 0.1, 0.95);
}

return {
  json: {
    analysis: analysis,
    confidence: confidence
  }
};
```

#### 5. Respond to Webhook 노드
K8s App에 결과를 JSON 형식으로 반환합니다.

## 🧪 테스트

### 1. n8n 워크플로우 테스트
1. n8n UI에서 워크플로우 선택
2. **Execute Workflow** 버튼 클릭
3. 테스트 데이터 입력:
```json
{
  "ci_log": "tasking compiler error: undefined reference to 'main'",
  "symptoms": ["tasking", "compiler", "undefined reference"],
  "error_type": "tasking",
  "context": "test",
  "repository": "test-repo"
}
```

### 2. 직접 웹훅 테스트
```bash
curl -X POST http://your-n8n-server:5678/webhook/llm-analyze \
  -H "Content-Type: application/json" \
  -d @test-payload.json
```

### 3. K8s App 연동 테스트
```bash
curl -X POST http://k8s-app-ip:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "ci_log": "tasking compiler error: undefined reference to main",
    "context": "automotive sw build",
    "repository": "ecu-firmware"
  }'
```

## 🔍 트러블슈팅

### 자주 발생하는 문제

#### 1. 연결 실패
**증상**: Private LLM 서버 연결 실패
**해결방법**:
- LLM 서버 상태 확인
- 네트워크 연결 확인
- `PRIVATE_LLM_URL` 환경변수 확인

#### 2. 타임아웃
**증상**: 25초 후 타임아웃
**해결방법**:
- LLM 서버 성능 확인
- 요청 복잡도 줄이기
- 타임아웃 시간 조정

#### 3. 응답 형식 오류
**증상**: JSON 파싱 오류
**해결방법**:
- LLM 응답 형식 확인
- 후처리 노드 로직 점검

#### 4. 환경변수 미설정
**증상**: `{{ $env.PRIVATE_LLM_URL }}` 값이 비어있음
**해결방법**:
- n8n 서버 재시작
- 환경변수 설정 확인

## 📊 모니터링

### n8n 실행 로그 확인
```bash
# Docker로 실행한 경우
docker logs n8n-container

# 직접 실행한 경우
n8n logs
```

### 워크플로우 실행 통계
n8n UI에서 **Executions** 탭에서 실행 통계를 확인할 수 있습니다.

## 🔒 보안 고려사항

1. **API 키 보안**: 환경변수로 관리
2. **네트워크 접근**: Private LLM 서버는 내부 네트워크에서만 접근
3. **로그 필터링**: 민감한 정보는 로그에서 제외
4. **인증**: 필요시 n8n webhook에 인증 추가

## 📈 성능 최적화

1. **캐싱**: 자주 사용되는 분석 결과 캐싱
2. **병렬 처리**: 여러 요청 동시 처리
3. **리소스 모니터링**: CPU/메모리 사용량 모니터링
4. **타임아웃 조정**: 서버 성능에 맞게 조정
