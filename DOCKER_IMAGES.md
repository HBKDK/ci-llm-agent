# 🐳 Docker 이미지 관리

CI Error Agent의 Docker 이미지를 빌드하고 관리하는 방법을 설명합니다.

## 📦 이미지 빌드

### 자동 빌드
```bash
# Docker 이미지 빌드
./build_docker_image.sh
```

### 수동 빌드
```bash
# 기본 빌드
docker build -t ci-error-agent:latest .

# 특정 태그로 빌드
docker build -t ci-error-agent:v1.0.0 .

# 멀티 플랫폼 빌드 (ARM64, AMD64)
docker buildx build --platform linux/amd64,linux/arm64 -t ci-error-agent:latest .
```

## 💾 이미지 저장

### 자동 저장
```bash
# 이미지를 파일로 저장 (tar, tar.gz)
./save_docker_image.sh
```

### 수동 저장
```bash
# tar 파일로 저장
docker save ci-error-agent:latest -o ci-error-agent.tar

# 압축된 tar.gz 파일로 저장
docker save ci-error-agent:latest | gzip > ci-error-agent.tar.gz

# 이미지 정보 저장
docker inspect ci-error-agent:latest > image-info.json
```

## 🔄 이미지 복원

```bash
# tar 파일에서 복원
docker load -i ci-error-agent.tar

# 압축된 파일에서 복원
docker load < ci-error-agent.tar.gz

# 복원 확인
docker images | grep ci-error-agent
```

## 🚀 이미지 실행

```bash
# 기본 실행
docker run -p 8000:8000 ci-error-agent:latest

# 환경변수와 함께 실행
docker run -p 8000:8000 \
  -e LLM_PROVIDER=openai \
  -e OPENAI_API_KEY=your-key \
  ci-error-agent:latest

# 볼륨 마운트와 함께 실행
docker run -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  ci-error-agent:latest
```

## 🏷️ 태그 관리

```bash
# 새 태그 생성
docker tag ci-error-agent:latest ci-error-agent:v1.0.0

# Docker Hub에 푸시
docker tag ci-error-agent:latest your-username/ci-error-agent:latest
docker push your-username/ci-error-agent:latest

# 태그 삭제
docker rmi ci-error-agent:v1.0.0
```

## 📊 이미지 정보

### 이미지 크기 확인
```bash
docker images ci-error-agent
docker system df
```

### 이미지 상세 정보
```bash
docker inspect ci-error-agent:latest
docker history ci-error-agent:latest
```

## 🧹 정리

```bash
# 사용하지 않는 이미지 삭제
docker image prune

# 모든 사용하지 않는 리소스 정리
docker system prune -a

# 특정 이미지 삭제
docker rmi ci-error-agent:latest
```

## 📁 저장된 파일

빌드 및 저장 후 다음 파일들이 생성됩니다:

```
docker-images/
├── ci-error-agent.tar      # 압축되지 않은 이미지
├── ci-error-agent.tar.gz   # 압축된 이미지
└── image-info.json         # 이미지 메타데이터
```

## 🔧 문제 해결

### 빌드 실패 시
1. Docker가 실행 중인지 확인: `docker --version`
2. Dockerfile 문법 확인
3. 의존성 파일 확인: `requirements.txt`

### 실행 실패 시
1. 포트 충돌 확인: `netstat -tulpn | grep 8000`
2. 환경변수 설정 확인
3. 로그 확인: `docker logs <container-id>`

### 이미지 복원 실패 시
1. 파일 무결성 확인: `file ci-error-agent.tar`
2. 권한 확인: `ls -la ci-error-agent.tar`
3. 디스크 공간 확인: `df -h`