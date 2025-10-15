#!/usr/bin/env python3
"""
Local LLM Server

n8n을 대체하는 로컬 Python FastAPI 서버
OpenAI API를 사용하여 CI 로그 분석을 수행합니다.
"""

import os
import asyncio
import yaml
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import openai
from openai import AsyncOpenAI
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 설정 로드
def load_config():
    """설정 파일에서 설정을 로드합니다."""
    config_file = "local_llm_server_config.yaml"
    default_config = {
        "openai": {
            "api_key": os.getenv("OPENAI_API_KEY", ""),
            "model": "gpt-3.5-turbo",
            "temperature": 0.2,
            "max_tokens": 1000
        },
        "server": {
            "port": 5678,
            "host": "0.0.0.0",
            "timeout": 30
        }
    }
    
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                file_config = yaml.safe_load(f) or {}
            # 기본 설정에 파일 설정 병합
            for key, value in file_config.items():
                if key in default_config:
                    default_config[key].update(value)
                else:
                    default_config[key] = value
        except Exception as e:
            logger.warning(f"설정 파일 로드 실패, 기본값 사용: {e}")
    
    return default_config

config = load_config()

# OpenAI 클라이언트 초기화
openai_client = None
if config["openai"]["api_key"]:
    openai_client = AsyncOpenAI(api_key=config["openai"]["api_key"])
else:
    logger.warning("OPENAI_API_KEY가 설정되지 않았습니다. 환경변수를 설정하거나 config 파일을 확인하세요.")

# FastAPI 앱 생성
app = FastAPI(
    title="Local LLM Server",
    description="n8n을 대체하는 로컬 LLM 분석 서버",
    version="1.0.0"
)

# 요청 모델
class AnalyzeRequest(BaseModel):
    ci_log: str
    symptoms: list
    error_type: str
    context: Optional[str] = None
    repository: Optional[str] = None

# 응답 모델
class AnalyzeResponse(BaseModel):
    analysis: str
    confidence: float

def calculate_confidence(analysis: str) -> float:
    """분석 결과 길이에 따른 신뢰도 계산"""
    length = len(analysis)
    if length > 500:
        return 0.9
    elif length > 300:
        return 0.8
    elif length > 200:
        return 0.7
    elif length > 100:
        return 0.6
    else:
        return 0.5

async def analyze_with_openai(request: AnalyzeRequest) -> Dict[str, Any]:
    """OpenAI API를 사용하여 CI 로그 분석"""
    if not openai_client:
        raise HTTPException(
            status_code=503,
            detail="OpenAI API 키가 설정되지 않음"
        )
    
    # 프롬프트 구성
    system_prompt = """당신은 자동차 소프트웨어 CI/CD 오류 분석 전문가입니다.

다음 형식으로 분석 결과를 제공해주세요:

## 🔍 오류 분석

**오류 유형**: [오류 유형]
**핵심 증상**: [주요 증상]

## 🛠️ 해결책

### 1단계: [첫 번째 해결 방법]
[구체적인 설명]

### 2단계: [두 번째 해결 방법]
[구체적인 설명]

### 3단계: [추가 해결 방법]
[구체적인 설명]

**참고**: [추가 팁이나 주의사항]

간단하고 명확하게, 실제로 실행 가능한 해결책을 제시해주세요."""

    user_prompt = f"""다음 CI 로그 오류를 분석해주세요:

**오류 타입**: {request.error_type}

**증상**:
{chr(10).join(f"- {symptom}" for symptom in request.symptoms)}

**CI 로그**:
{request.ci_log}

{f"**컨텍스트**: {request.context}" if request.context else ""}
{f"**저장소**: {request.repository}" if request.repository else ""}"""

    try:
        response = await openai_client.chat.completions.create(
            model=config["openai"]["model"],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=config["openai"]["temperature"],
            max_tokens=config["openai"]["max_tokens"]
        )
        
        analysis = response.choices[0].message.content
        confidence = calculate_confidence(analysis)
        
        return {
            "analysis": analysis,
            "confidence": confidence
        }
        
    except Exception as e:
        logger.error(f"OpenAI API 호출 실패: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"LLM 분석 실패: {str(e)}"
        )

@app.get("/")
async def root():
    """서버 상태 확인"""
    return {
        "status": "running",
        "service": "Local LLM Server",
        "version": "1.0.0",
        "openai_configured": bool(openai_client)
    }

@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy", "openai_available": bool(openai_client)}

@app.post("/webhook/llm-analyze", response_model=AnalyzeResponse)
async def analyze_ci_error(request: AnalyzeRequest):
    """
    CI 오류 분석 엔드포인트
    
    n8n webhook과 동일한 인터페이스를 제공합니다.
    """
    logger.info(f"CI 오류 분석 요청: {request.error_type}")
    
    try:
        result = await analyze_with_openai(request)
        logger.info(f"분석 완료: 신뢰도 {result['confidence']}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"분석 중 오류 발생: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"분석 처리 중 오류: {str(e)}"
        )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """전역 예외 처리"""
    logger.error(f"예상치 못한 오류: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "내부 서버 오류가 발생했습니다."}
    )

if __name__ == "__main__":
    import uvicorn
    
    port = config["server"]["port"]
    host = config["server"]["host"]
    
    logger.info(f"로컬 LLM 서버 시작: http://{host}:{port}")
    logger.info(f"OpenAI 모델: {config['openai']['model']}")
    
    if not openai_client:
        logger.warning("⚠️ OpenAI API 키가 설정되지 않았습니다!")
        logger.warning("환경변수 OPENAI_API_KEY를 설정하거나 local_llm_server_config.yaml 파일을 확인하세요.")
    
    uvicorn.run(
        "local_llm_server:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )

