#!/bin/bash

# CI Error Agent Docker 이미지 빌드 스크립트

echo "🐳 CI Error Agent Docker 이미지 빌드 시작..."

# 이미지 태그 설정
IMAGE_NAME="ci-error-agent"
TAG="latest"
FULL_IMAGE_NAME="${IMAGE_NAME}:${TAG}"

# Docker 이미지 빌드
echo "📦 Docker 이미지 빌드 중: ${FULL_IMAGE_NAME}"
docker build -t ${FULL_IMAGE_NAME} .

# 빌드 성공 확인
if [ $? -eq 0 ]; then
    echo "✅ Docker 이미지 빌드 완료!"
    echo "📋 이미지 정보:"
    docker images | grep ${IMAGE_NAME}
    
    echo ""
    echo "🚀 이미지 실행 방법:"
    echo "docker run -p 8000:8000 ${FULL_IMAGE_NAME}"
    
    echo ""
    echo "💾 이미지 저장 방법:"
    echo "# tar 파일로 저장"
    echo "docker save ${FULL_IMAGE_NAME} -o ci-error-agent.tar"
    echo ""
    echo "# 압축된 tar 파일로 저장"
    echo "docker save ${FULL_IMAGE_NAME} | gzip > ci-error-agent.tar.gz"
    echo ""
    echo "# Docker Hub에 푸시 (선택사항)"
    echo "docker tag ${FULL_IMAGE_NAME} your-username/ci-error-agent:latest"
    echo "docker push your-username/ci-error-agent:latest"
    
else
    echo "❌ Docker 이미지 빌드 실패!"
    exit 1
fi