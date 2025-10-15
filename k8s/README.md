# 🚀 K8s 배포 가이드

## 📋 배포 순서

### 1️⃣ Secrets 및 ConfigMap 생성

```bash
# ConfigMap 수정
# k8s/secrets.yaml 파일에서 다음 값들을 실제 값으로 변경:
# - smtp-host: SMTP 서버 주소
# - base-url: 외부 접근 URL
# - developer-email: 개발자 이메일
# - admin-email: 관리자 이메일

# Secrets 생성
kubectl apply -f k8s/secrets.yaml
```

### 2️⃣ PostgreSQL 배포

```bash
kubectl apply -f k8s/postgres.yaml

# PostgreSQL 준비 확인
kubectl wait --for=condition=ready pod -l app=postgres --timeout=120s
```

### 3️⃣ N8N 워크플로우 설정

```bash
# N8N 서버에 워크플로우 Import
# 1. n8n UI 접속 (http://your-n8n-server:5678)
# 2. n8n-workflows/ci-llm-analyzer.json 파일 Import
# 3. 환경변수 설정:
#    - PRIVATE_LLM_URL=http://your-llm-server:8000/v1/chat/completions
#    - PRIVATE_LLM_MODEL=llama-3-70b
#    - PRIVATE_LLM_API_KEY=your-api-key
# 4. 워크플로우 활성화
```

### 4️⃣ CI Error Agent 배포

```bash
# Docker 이미지 빌드 및 푸시
docker build -t ci-error-agent:latest .
docker tag ci-error-agent:latest your-registry/ci-error-agent:latest
docker push your-registry/ci-error-agent:latest

# K8s 배포
kubectl apply -f k8s/deployment.yaml

# 배포 확인
kubectl get pods -l app=ci-error-agent
```

### 5️⃣ 배포 확인

```bash
# 모든 Pod 확인
kubectl get pods

# 로그 확인
kubectl logs -f deployment/ci-error-agent

# 서비스 확인
kubectl get svc

# PVC 확인
kubectl get pvc
```

## 🔧 설정 파일 수정

### k8s/secrets.yaml
```yaml
# 실제 환경에 맞게 수정
stringData:
  # PostgreSQL 비밀번호
  username: postgres
  password: "CHANGE_THIS_PASSWORD"
  
  # JWT Secret (긴 랜덤 문자열)
  jwt-secret-key: "CHANGE_THIS_TO_LONG_RANDOM_STRING"
  
  # SMTP 인증
  username: "your-smtp-username"
  password: "your-smtp-password"

# ConfigMap 수정
data:
  smtp-host: "smtp.your-company.com"
  base-url: "https://ci-agent.your-company.com"
  developer-email: "dev@your-company.com"
  admin-email: "admin@your-company.com"
  n8n-webhook-url: "http://your-n8n-server:5678/webhook/llm-analyze"
```


## 🌐 외부 접근 설정 (선택사항)

### Ingress 설정
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ci-error-agent-ingress
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  rules:
  - host: ci-agent.your-company.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: ci-error-agent-service
            port:
              number: 8000
  tls:
  - hosts:
    - ci-agent.your-company.com
    secretName: ci-agent-tls
```

## 🔍 모니터링

### 헬스 체크
```bash
kubectl exec -it deployment/ci-error-agent -- curl http://localhost:8000/health
```

### DB 연결 확인
```bash
kubectl exec -it deployment/postgres -- psql -U postgres -d ci_agent -c "SELECT COUNT(*) FROM knowledge_base;"
```

### 승인 대기 목록 확인
```bash
kubectl exec -it deployment/ci-error-agent -- curl http://localhost:8000/pending/list
```

## 🛠️ 트러블슈팅

### Pod가 시작하지 않는 경우
```bash
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```

### DB 연결 오류
```bash
# PostgreSQL 상태 확인
kubectl get pods -l app=postgres

# DB 로그 확인
kubectl logs deployment/postgres
```

### 이메일 전송 실패
```bash
# SMTP 설정 확인
kubectl get configmap app-config -o yaml

# Secret 확인
kubectl get secret smtp-secret -o yaml
```

## 📊 운영 팁

### 정기 백업
```bash
# 매일 자동 백업 (CronJob)
kubectl create cronjob kb-backup \
  --schedule="0 0 * * *" \
  --image=ci-error-agent:latest \
  -- python -c "from ci_error_agent import CIErrorAgent; CIErrorAgent().export_kb('/app/data/backup.json')"
```

### 로그 회전
```bash
# 오래된 분석 이력 정리 (예: 90일 이상)
kubectl exec -it deployment/postgres -- psql -U postgres -d ci_agent -c \
  "DELETE FROM analysis_history WHERE created_at < NOW() - INTERVAL '90 days';"
```

### 승인 대기 정리
```bash
# 만료된 승인 대기 항목 정리
kubectl exec -it deployment/postgres -- psql -U postgres -d ci_agent -c \
  "UPDATE pending_approvals SET approval_status='expired' WHERE token_expires_at < NOW() AND approval_status='pending';"
```

이제 **K8s 환경에서 완전히 자동화된 CI 오류 분석 시스템**을 배포할 수 있습니다! 🚗✨

