# 🚀 배포 가이드

## ☸️ Kubernetes 배포

### 전제 조건
- Kubernetes 클러스터
- kubectl 설정 완료
- Docker 레지스트리 (선택사항)

### 1단계: 설정 파일 수정

#### `k8s/secrets.yaml`:
```yaml
# PostgreSQL 비밀번호 변경 (필수!)
password: "your-strong-password-here"

# JWT Secret 변경 (필수!)
jwt-secret-key: "your-64-char-random-secret-key-here"

# Private LLM API Key
private-llm-api-key: "your-llm-api-key"

# Base URL (K8s 노드 IP)
base-url: "http://192.168.1.100:30800"  # 실제 노드 IP로 변경

# Private LLM URL
private-llm-base-url: "http://your-llm-server:8000/v1"
private-llm-model: "llama-3-70b"
```

### 2단계: 배포 실행

```bash
# 1. Secret 생성
kubectl apply -f k8s/secrets.yaml

# 2. PostgreSQL 배포
kubectl apply -f k8s/postgres.yaml

# 3. PostgreSQL Ready 확인
kubectl get pods -w
# postgres Pod이 Running 상태가 될 때까지 대기

# 4. Agent 배포
kubectl apply -f k8s/deployment.yaml

# 5. 확인
kubectl get pods
kubectl get svc
```

### 3단계: 접속 테스트

```bash
# Health Check
curl http://<node-ip>:30800/health

# API 문서 (브라우저)
http://<node-ip>:30800/docs
```

## 🐳 Docker만 사용 (로컬 테스트)

```bash
# 빌드
docker build -t ci-error-agent:latest .

# 실행
docker run -p 8000:8000 \
  -e USE_SQLITE=true \
  -e LLM_PROVIDER="" \
  -e SEARCH_ENGINE=none \
  ci-error-agent:latest

# 접속
http://localhost:8000/docs
```

## 🔧 문제 해결

### Pod이 시작되지 않음
```bash
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```

### PostgreSQL 연결 실패
```bash
kubectl get svc postgres-service
kubectl logs deployment/postgres
```

### Health Check 실패
```bash
kubectl logs -f deployment/ci-error-agent
```

## 📊 리소스 요구사항

- **RAM**: 512Mi (최소) - 1Gi (권장)
- **CPU**: 500m (최소) - 1000m (권장)
- **Storage**: 10Gi (PVC)

## 🎯 NodePort 접속

```
http://<K8s-Node-IP>:30800
```

### 노드 IP 확인:
```bash
kubectl get nodes -o wide
# INTERNAL-IP 또는 EXTERNAL-IP 사용
```

## ✅ 배포 완료 후

1. **Health Check**: `curl http://<node-ip>:30800/health`
2. **API 문서**: 브라우저에서 `http://<node-ip>:30800/docs`
3. **CI 연동**: `ci_system_example.py` 참고
4. **테스트**: POST /analyze로 오류 분석

**배포 준비 완료!** 🚗✨
