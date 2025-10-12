# 🔧 Private LLM 및 IP 기반 접속 설정 가이드

## 🎯 Private LLM 설정

### 1️⃣ **환경변수 설정**

#### k8s/secrets.yaml 수정

```yaml
# ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  # Private LLM 서버 설정
  private-llm-base-url: "http://your-llm-server.company.com:8000/v1"
  private-llm-model: "llama-3-70b"  # 사용할 모델 이름
  
  # 또는 K8s 내부 서비스
  # private-llm-base-url: "http://llm-service:8000/v1"

---
# Secret
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
type: Opaque
stringData:
  # Private LLM API 키 (필요한 경우)
  private-llm-api-key: "your-private-llm-api-key"
  
  # JWT Secret
  jwt-secret-key: "change-this-jwt-secret-in-production"
```

#### k8s/deployment.yaml에서 LLM_PROVIDER 설정

```yaml
env:
- name: LLM_PROVIDER
  value: "private"  # private 또는 openai
```

### 2️⃣ **지원하는 Private LLM**

Private LLM 서버가 **OpenAI API 호환 인터페이스**를 제공하면 모두 사용 가능합니다:

#### ✅ **호환되는 LLM 서버**
- **vLLM**: OpenAI API 호환 서버
- **Text Generation Inference (TGI)**: Hugging Face
- **Ollama**: OpenAI API 호환 모드
- **LM Studio**: OpenAI API 호환
- **FastChat**: OpenAI API 호환
- **LocalAI**: OpenAI API 호환

#### 📝 **Private LLM 서버 예시**

```bash
# vLLM 서버 실행 예시
python -m vllm.entrypoints.openai.api_server \
  --model llama-3-70b \
  --host 0.0.0.0 \
  --port 8000

# Ollama OpenAI 호환 모드
OLLAMA_HOST=0.0.0.0:8000 ollama serve
```

### 3️⃣ **설정 예시**

#### 예시 1: vLLM 서버 사용
```yaml
# ConfigMap
data:
  private-llm-base-url: "http://vllm-server.company.com:8000/v1"
  private-llm-model: "llama-3-70b"

# Secret
stringData:
  private-llm-api-key: "not-needed"  # vLLM은 API 키 불필요
```

#### 예시 2: 사내 LLM 서비스
```yaml
# ConfigMap
data:
  private-llm-base-url: "http://llm-api.internal.company.com/v1"
  private-llm-model: "company-custom-model"

# Secret
stringData:
  private-llm-api-key: "internal-api-key-12345"
```

#### 예시 3: K8s 내부 LLM 서비스
```yaml
# ConfigMap
data:
  private-llm-base-url: "http://llm-service:8000/v1"
  private-llm-model: "mistral-7b"
```

## 🌐 IP 기반 접속 설정

### 📊 **3가지 방법**

#### 방법 1: NodePort (가장 간단) ⭐ **추천**

```yaml
# k8s/deployment.yaml
apiVersion: v1
kind: Service
metadata:
  name: ci-error-agent-service
spec:
  type: NodePort
  ports:
  - port: 8000
    targetPort: 8000
    nodePort: 30800  # 외부 접속 포트
```

**접속 방법:**
```bash
# K8s 노드 IP 확인
kubectl get nodes -o wide

# 접속 URL
http://<NODE_IP>:30800

# 예시
http://192.168.1.100:30800
```

#### 방법 2: LoadBalancer (클라우드 환경)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: ci-error-agent-service
spec:
  type: LoadBalancer
  ports:
  - port: 8000
    targetPort: 8000
```

**접속 방법:**
```bash
# External IP 확인
kubectl get svc ci-error-agent-service

# 접속 URL
http://<EXTERNAL_IP>:8000
```

#### 방법 3: ClusterIP + Port Forward (개발/테스트)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: ci-error-agent-service
spec:
  type: ClusterIP
  ports:
  - port: 8000
```

**접속 방법:**
```bash
# Port Forward
kubectl port-forward svc/ci-error-agent-service 8000:8000

# 접속 URL
http://localhost:8000
```

## 🔧 CI 시스템 연동 (IP 기반)

### Python 코드 업데이트

```python
# ci_system_example.py에서

# NodePort 사용 시
analyzer = CIErrorAnalyzer(
    agent_url="http://192.168.1.100:30800"  # K8s 노드 IP + NodePort
)

# LoadBalancer 사용 시
analyzer = CIErrorAnalyzer(
    agent_url="http://10.20.30.40:8000"  # LoadBalancer External IP
)

# ClusterIP + Port Forward (로컬 테스트)
analyzer = CIErrorAnalyzer(
    agent_url="http://localhost:8000"
)
```

### 이메일에 포함될 승인 링크

```python
# ConfigMap에서 base-url 설정
data:
  base-url: "http://192.168.1.100:30800"  # 실제 접속 가능한 IP + 포트

# 이메일에 포함되는 링크
approval_url = "http://192.168.1.100:30800/approve/eyJ..."
modify_url = "http://192.168.1.100:30800/modify/eyJ..."
```

## 📋 설정 체크리스트

### Private LLM 설정
- [ ] Private LLM 서버 URL 확인
- [ ] 모델 이름 확인 (llama-3-70b, mistral-7b 등)
- [ ] API 키 확인 (필요한 경우)
- [ ] `k8s/secrets.yaml`에 설정 입력
- [ ] `k8s/deployment.yaml`에서 `LLM_PROVIDER=private` 설정

### IP 기반 접속 설정
- [ ] K8s 노드 IP 확인
- [ ] Service 타입 결정 (NodePort/LoadBalancer/ClusterIP)
- [ ] NodePort 포트 결정 (30000-32767)
- [ ] `k8s/secrets.yaml`의 `base-url` 설정
- [ ] 방화벽 규칙 확인

## 🧪 테스트

### Private LLM 연결 테스트

```bash
# Pod 내부에서 테스트
kubectl exec -it deployment/ci-error-agent -- python -c "
import os
os.environ['LLM_PROVIDER'] = 'private'
os.environ['PRIVATE_LLM_BASE_URL'] = 'http://your-llm-server:8000/v1'
os.environ['PRIVATE_LLM_MODEL'] = 'llama-3-70b'

from app.llm.provider import get_llm
import asyncio

llm = get_llm()
result = asyncio.run(llm.achain('테스트 프롬프트'))
print(result)
"
```

### IP 접속 테스트

```bash
# NodePort 접속 테스트
curl http://192.168.1.100:30800/health

# 분석 API 테스트
curl -X POST http://192.168.1.100:30800/analyze \
  -H "Content-Type: application/json" \
  -d '{"ci_log": "test error"}'
```

## 🎯 실제 설정 예시

### 완전한 secrets.yaml

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  # SMTP
  smtp-host: "smtp.company.com"
  smtp-port: "587"
  
  # Agent 접속 URL (실제 IP로 변경)
  base-url: "http://192.168.1.100:30800"
  
  # Private LLM (실제 서버 정보로 변경)
  private-llm-base-url: "http://10.0.0.50:8000/v1"
  private-llm-model: "llama-3-70b"

---
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
type: Opaque
stringData:
  # Private LLM
  private-llm-api-key: "your-actual-api-key"
  
  # JWT
  jwt-secret-key: "super-long-random-secret-key-change-this"
```

### deployment.yaml LLM 설정

```yaml
env:
- name: LLM_PROVIDER
  value: "private"  # private LLM 사용
```

## 🚀 배포

```bash
# 1. 설정 수정
# - k8s/secrets.yaml에서 Private LLM URL, 모델, API 키 설정
# - base-url을 실제 접속 가능한 IP:포트로 설정

# 2. 배포
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/deployment.yaml

# 3. NodePort 확인
kubectl get svc ci-error-agent-service

# 4. 노드 IP 확인
kubectl get nodes -o wide

# 5. 접속 테스트
# http://<NODE_IP>:30800/health
```

## 💡 추천 설정

### 프로덕션 환경
```yaml
# LLM: Private LLM (사내 서버)
LLM_PROVIDER: private
PRIVATE_LLM_BASE_URL: http://llm-server.company.com:8000/v1

# 접속: LoadBalancer (고정 IP)
Service Type: LoadBalancer
base-url: http://10.20.30.40:8000
```

### 개발 환경
```yaml
# LLM: OpenAI (빠른 테스트)
LLM_PROVIDER: openai
OPENAI_API_KEY: sk-...

# 접속: NodePort (간단)
Service Type: NodePort
base-url: http://localhost:30800
```

## ✅ 완료 체크

- [ ] Private LLM 서버 정보 입력
- [ ] LLM_PROVIDER=private 설정
- [ ] Service Type 설정 (NodePort 권장)
- [ ] base-url을 실제 IP:포트로 설정
- [ ] 배포 및 테스트

이제 **Private LLM과 IP 기반 접속**이 완벽하게 설정되었습니다! 🚗✨

