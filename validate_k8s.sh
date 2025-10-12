#!/bin/bash
# K8s 배포 검증 스크립트

echo "============================================================"
echo "K8s 배포 검증"
echo "============================================================"

# 1. YAML 파일 검증
echo ""
echo "[1/5] YAML 파일 검증..."
for file in k8s/*.yaml; do
    echo "   Checking $file..."
    kubectl apply --dry-run=client -f "$file" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ $file - YAML 구문 오류"
        kubectl apply --dry-run=client -f "$file"
        exit 1
    fi
done

# 2. Docker 이미지 빌드 테스트
echo ""
echo "[2/5] Docker 이미지 빌드..."
docker build -t ci-error-agent:test . > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ Docker 이미지 빌드 성공"
else
    echo "   ❌ Docker 빌드 실패"
    exit 1
fi

# 3. Docker 컨테이너 테스트
echo ""
echo "[3/5] Docker 컨테이너 테스트..."
docker run -d --name ci-agent-test \
  -p 9000:8000 \
  -e USE_SQLITE=true \
  -e LLM_PROVIDER="" \
  -e SEARCH_ENGINE=none \
  ci-error-agent:test

sleep 10

# Health check
curl -f http://localhost:9000/health > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ 컨테이너 정상 작동"
else
    echo "   ❌ 컨테이너 health check 실패"
    docker logs ci-agent-test
    docker rm -f ci-agent-test
    exit 1
fi

docker rm -f ci-agent-test > /dev/null 2>&1

# 4. K8s Secret 검증
echo ""
echo "[4/5] K8s Secret 검증..."
kubectl apply --dry-run=client -f k8s/secrets.yaml > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ Secret 검증 완료"
else
    echo "   ❌ Secret 검증 실패"
    exit 1
fi

# 5. 필수 환경변수 확인
echo ""
echo "[5/5] 환경변수 확인..."

echo "   확인 필요:"
echo "   - base-url: K8s 노드 IP:30800"
echo "   - private-llm-base-url: Private LLM URL"
echo "   - jwt-secret-key: 64자 이상"
echo "   - postgres password: 강력한 비밀번호"

echo ""
echo "============================================================"
echo "✅ 검증 완료!"
echo "============================================================"

echo ""
echo "배포 명령어:"
echo "   kubectl apply -f k8s/secrets.yaml"
echo "   kubectl apply -f k8s/postgres.yaml"
echo "   # PostgreSQL Ready 대기..."
echo "   kubectl apply -f k8s/deployment.yaml"
echo ""
echo "확인:"
echo "   kubectl get pods"
echo "   kubectl get svc"
echo "   kubectl logs -f deployment/ci-error-agent"
echo ""
echo "접속:"
echo "   http://<node-ip>:30800/docs"
echo ""
