# Deprecated Files

이 폴더는 더 이상 사용되지 않는 파일들을 포함합니다.

## 📁 n8n-workflows/

n8n 기반 워크플로우 파일들입니다. **로컬 LLM 서버로 대체되었습니다.**

### 포함된 파일들:
- `ci-llm-analyzer.json` - CI LLM 분석 워크플로우
- `README.md` - n8n 설정 가이드
- `setup-guide.md` - 상세 설정 가이드
- `test-payload.json` - 테스트 페이로드

### 대체 솔루션:
**`../local_llm_server.py`** - 로컬 Python FastAPI 서버
- 더 간단한 설정
- 직접적인 OpenAI API 연동
- n8n 서버 불필요

## 📄 test_n8n_agent_workflow.json

Azure OpenAI Agent 테스트용 n8n 워크플로우입니다.

### 대체 솔루션:
**`../LOCAL_LLM_SERVER.md`** - 로컬 LLM 서버 가이드 참조

## 🔄 마이그레이션 가이드

1. **기존 n8n 사용자**:
   - `../LOCAL_LLM_SERVER.md` 가이드 참조
   - 로컬 LLM 서버로 마이그레이션

2. **설정 변경**:
   - `../k8s/secrets.yaml`의 `n8n-webhook-url`을 로컬 PC IP로 변경

3. **의존성**:
   - `../requirements.txt`에 openai 패키지 추가됨

## ⚠️ 주의사항

이 파일들은 참고용으로만 보관됩니다. 새로운 개발에서는 사용하지 마세요.
