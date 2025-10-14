# n8n Workflows for CI Agent

## 워크플로우 파일

### `ci-llm-analyzer.json`
K8s CI Agent에서 KB 검색 후 필요시 호출하는 LLM 분석 워크플로우입니다.

## Import 방법

1. n8n UI 접속 (`http://your-n8n-server:5678`)
2. **Workflows** 메뉴 클릭
3. **Import from File** 클릭
4. `ci-llm-analyzer.json` 파일 선택
5. 워크플로우 활성화

## 환경변수 설정

n8n에서 다음 환경변수를 설정하세요:

```bash
PRIVATE_LLM_URL=http://your-llm-server:8000/v1/chat/completions
PRIVATE_LLM_MODEL=llama-3-70b
```

## API 계약

### 요청 (K8s App → n8n)
```json
{
  "ci_log": "tasking compiler error: undefined reference to 'main'",
  "symptoms": ["tasking", "compiler", "undefined reference"],
  "error_type": "tasking",
  "context": "automotive sw build",
  "repository": "ecu-firmware"
}
```

### 응답 (n8n → K8s App)
```json
{
  "analysis": "Tasking 컴파일러에서 'main' 함수를 찾을 수 없다는 오류입니다...",
  "confidence": 0.85
}
```

## 웹훅 URL

워크플로우 활성화 후 다음 URL로 호출됩니다:
```
http://your-n8n-server:5678/webhook/llm-analyze
```

## 테스트

### 1. n8n 워크플로우 테스트
n8n UI에서 **Execute Workflow** 버튼으로 테스트할 수 있습니다.

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

## 트러블슈팅

### 자주 발생하는 문제

1. **연결 실패**
   - Private LLM 서버 상태 확인
   - 네트워크 연결 확인
   - 환경변수 설정 확인

2. **타임아웃**
   - LLM 서버 성능 확인
   - 타임아웃 설정 조정 (현재 25초)

3. **응답 형식 오류**
   - LLM 응답 JSON 형식 확인
   - 후처리 노드 로직 점검

## 워크플로우 구조

```
Webhook → 전처리 → Private LLM 호출 → 후처리 → Respond to Webhook
```

각 노드의 역할:
- **Webhook**: K8s App 요청 수신
- **전처리**: 입력 데이터 정리 및 검증
- **Private LLM 호출**: 실제 LLM 분석 수행
- **후처리**: 응답 처리 및 신뢰도 계산
- **Respond to Webhook**: K8s App에 결과 반환
