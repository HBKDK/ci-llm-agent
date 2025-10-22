#!/bin/bash

# Azure OpenAI 설정 스크립트
# 이 스크립트를 실행하기 전에 Azure OpenAI 리소스의 정보를 확인하세요.

echo "🔧 Azure OpenAI 설정을 시작합니다..."

# 환경변수 파일 생성
ENV_FILE=".env.azure_openai"

echo "# Azure OpenAI 설정" > $ENV_FILE
echo "# 이 파일을 .env로 복사하거나 환경변수로 설정하세요" >> $ENV_FILE
echo "" >> $ENV_FILE

# 사용자 입력 받기
read -p "Azure OpenAI 엔드포인트 URL을 입력하세요 (예: https://your-resource.openai.azure.com): " ENDPOINT
read -p "배포된 모델 이름을 입력하세요 (예: gpt-4o-mini): " DEPLOYMENT_NAME
read -s -p "Azure OpenAI API 키를 입력하세요: " API_KEY
echo ""

# 입력값 검증
if [ -z "$ENDPOINT" ] || [ -z "$DEPLOYMENT_NAME" ] || [ -z "$API_KEY" ]; then
    echo "❌ 모든 필드를 입력해야 합니다."
    exit 1
fi

# 환경변수 파일에 쓰기
echo "AZURE_OPENAI_ENDPOINT=$ENDPOINT" >> $ENV_FILE
echo "AZURE_OPENAI_DEPLOYMENT_NAME=$DEPLOYMENT_NAME" >> $ENV_FILE
echo "AZURE_OPENAI_API_KEY=$API_KEY" >> $ENV_FILE
echo "AZURE_OPENAI_API_VERSION=2024-02-15-preview" >> $ENV_FILE
echo "LLM_PROVIDER=azure" >> $ENV_FILE

echo "✅ 환경변수 파일이 생성되었습니다: $ENV_FILE"
echo ""
echo "다음 명령어로 환경변수를 로드할 수 있습니다:"
echo "source $ENV_FILE"
echo ""
echo "또는 Docker를 사용하는 경우:"
echo "docker run --env-file $ENV_FILE ..."
echo ""
echo "⚠️  보안을 위해 $ENV_FILE 파일을 .gitignore에 추가하세요."