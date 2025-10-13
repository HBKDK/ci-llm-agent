#!/bin/bash

# CI Error Agent Docker 이미지 저장 스크립트

echo "💾 CI Error Agent Docker 이미지 저장 시작..."

# 이미지 태그 설정
IMAGE_NAME="ci-error-agent"
TAG="latest"
FULL_IMAGE_NAME="${IMAGE_NAME}:${TAG}"

# 이미지 존재 확인
if ! docker images | grep -q "${IMAGE_NAME}"; then
    echo "❌ 이미지가 존재하지 않습니다. 먼저 build_docker_image.sh를 실행하세요."
    exit 1
fi

# 저장 디렉토리 생성
mkdir -p docker-images

# 1. tar 파일로 저장
echo "📦 tar 파일로 저장 중..."
docker save ${FULL_IMAGE_NAME} -o docker-images/ci-error-agent.tar
if [ $? -eq 0 ]; then
    echo "✅ ci-error-agent.tar 저장 완료"
    ls -lh docker-images/ci-error-agent.tar
fi

# 2. 압축된 tar.gz 파일로 저장
echo "🗜️ 압축된 tar.gz 파일로 저장 중..."
docker save ${FULL_IMAGE_NAME} | gzip > docker-images/ci-error-agent.tar.gz
if [ $? -eq 0 ]; then
    echo "✅ ci-error-agent.tar.gz 저장 완료"
    ls -lh docker-images/ci-error-agent.tar.gz
fi

# 3. 이미지 정보 저장
echo "📋 이미지 정보 저장 중..."
docker inspect ${FULL_IMAGE_NAME} > docker-images/image-info.json
echo "✅ image-info.json 저장 완료"

echo ""
echo "🎉 Docker 이미지 저장 완료!"
echo "📁 저장 위치: docker-images/"
echo "   - ci-error-agent.tar (압축 안됨)"
echo "   - ci-error-agent.tar.gz (압축됨)"
echo "   - image-info.json (이미지 메타데이터)"
echo ""
echo "🔄 이미지 복원 방법:"
echo "docker load -i docker-images/ci-error-agent.tar"
echo "또는"
echo "docker load < docker-images/ci-error-agent.tar.gz"