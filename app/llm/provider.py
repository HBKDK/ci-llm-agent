import os
from dataclasses import dataclass
from typing import Protocol

from tenacity import retry, stop_after_attempt, wait_exponential
from app.utils.config import load_config, get_azure_config, get_private_llm_config, get_openai_config


class LLMClient(Protocol):
    async def achain(self, prompt: str) -> str:  # simple async generate
        ...


@dataclass
class OpenAIClient:
    model: str = "gpt-4o-mini"

    @retry(wait=wait_exponential(multiplier=1, min=1, max=20), stop=stop_after_attempt(3))
    async def achain(self, prompt: str) -> str:
        from openai import AsyncOpenAI

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            # fallback: local simple heuristic summarizer
            return _local_fallback(prompt)
        client = AsyncOpenAI(api_key=api_key)
        resp = await client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "당신은 DevOps 전문가입니다."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        return resp.choices[0].message.content or ""


@dataclass
class AzureOpenAIClient:
    """Azure OpenAI 클라이언트"""
    endpoint: str = ""
    deployment_name: str = ""
    api_key: str = ""
    api_version: str = "2024-02-15-preview"

    @retry(wait=wait_exponential(multiplier=1, min=1, max=20), stop=stop_after_attempt(3))
    async def achain(self, prompt: str) -> str:
        from openai import AsyncOpenAI

        # Azure OpenAI 클라이언트 설정
        client = AsyncOpenAI(
            api_key=self.api_key,
            azure_endpoint=self.endpoint,
            api_version=self.api_version
        )
        
        resp = await client.chat.completions.create(
            model=self.deployment_name,
            messages=[
                {"role": "system", "content": "당신은 자동차 SW 개발 환경의 DevOps 전문가입니다."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        return resp.choices[0].message.content or ""


@dataclass
class PrivateLLMClient:
    """Private LLM (사내 LLM 서버) 클라이언트"""
    base_url: str = ""
    model: str = ""
    api_key: str = ""

    @retry(wait=wait_exponential(multiplier=1, min=1, max=20), stop=stop_after_attempt(3))
    async def achain(self, prompt: str) -> str:
        from openai import AsyncOpenAI

        # Private LLM도 OpenAI API 호환 인터페이스 사용
        client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        resp = await client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "당신은 자동차 SW 개발 환경의 DevOps 전문가입니다."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        return resp.choices[0].message.content or ""


def _local_fallback(prompt: str) -> str:
    # 간단한 추출 요약 (LLM 키가 없을 때 비상 동작)
    import re

    lines = [l.strip() for l in prompt.splitlines() if l.strip()]
    candidates = [l for l in lines if any(k in l.lower() for k in ["error", "exception", "failed", "unable", "missing", "not found"])][:5]
    summary = "\n".join(candidates) or lines[-10:]
    return (
        "[로컬 요약] LLM 키가 없어 간이 분석을 제공합니다.\n" +
        "핵심 메시지:\n" + "\n".join(candidates[:3]) + "\n\n" +
        "가능한 조치:\n- 로그의 패키지/버전 충돌 확인\n- 캐시/빌드 폴더 정리 후 재시도\n- 의존성 설치 단계 재실행\n- 관련 이슈 검색으로 해결책 확인"
    ).strip()


def get_llm() -> LLMClient:
    """
    LLM 클라이언트 생성 (config 파일 + 환경변수 기반)
    
    우선순위: 환경변수 > config 파일 > 기본값
    
    환경변수:
        LLM_PROVIDER: openai (기본값), azure, 또는 private
        
        OpenAI 사용 시:
            OPENAI_API_KEY: OpenAI API 키
        
        Azure OpenAI 사용 시:
            AZURE_OPENAI_ENDPOINT: Azure OpenAI 엔드포인트 URL
            AZURE_OPENAI_DEPLOYMENT_NAME: 배포된 모델 이름
            AZURE_OPENAI_API_KEY: Azure OpenAI API 키
            AZURE_OPENAI_API_VERSION: API 버전 (기본값: 2024-02-15-preview)
        
        Private LLM 사용 시:
            PRIVATE_LLM_BASE_URL: Private LLM 서버 URL (예: http://llm-server:8000/v1)
            PRIVATE_LLM_MODEL: 모델 이름 (예: llama-3-70b, mistral-7b)
            PRIVATE_LLM_API_KEY: Private LLM API 키 (없으면 빈 문자열)
    """
    # config 파일 로드 시도
    try:
        config = load_config()
        print("✅ Config 파일 로드 성공")
    except Exception as e:
        print(f"⚠️ Config 파일 로드 실패: {e}")
        config = {}
    
    llm_provider = os.getenv("LLM_PROVIDER", "openai").lower()
    
    if llm_provider == "azure":
        # Azure OpenAI 사용 - config 파일에서 값 가져오기
        azure_config = get_azure_config(config)
        endpoint = azure_config["endpoint"]
        deployment_name = azure_config["deployment_name"]
        api_key = azure_config["api_key"]
        api_version = azure_config["api_version"]
        
        print(f"🔧 Azure OpenAI 설정:")
        print(f"   Endpoint: {endpoint}")
        print(f"   Deployment: {deployment_name}")
        print(f"   API Key: {'설정됨' if api_key else '없음'}")
        print(f"   API Version: {api_version}")
        
        if not endpoint or not deployment_name or not api_key:
            print("⚠️ Azure OpenAI 설정이 불완전합니다. 로컬 분석으로 대체합니다.")
            print(f"   필요한 설정: endpoint, deployment_name, api_key")
            # Fallback을 반환하는 간단한 클래스
            class LocalClient:
                async def achain(self, prompt: str) -> str:
                    return _local_fallback(prompt)
            return LocalClient()
        
        return AzureOpenAIClient(
            endpoint=endpoint,
            deployment_name=deployment_name,
            api_key=api_key,
            api_version=api_version
        )
    
    elif llm_provider == "private":
        # Private LLM 사용 - config 파일에서 값 가져오기
        private_config = get_private_llm_config(config)
        base_url = private_config["base_url"]
        model = private_config["model"]
        api_key = private_config["api_key"]
        
        print(f"🔧 Private LLM 설정:")
        print(f"   Base URL: {base_url}")
        print(f"   Model: {model}")
        print(f"   API Key: {'설정됨' if api_key else '없음'}")
        
        if not base_url:
            print("⚠️ PRIVATE_LLM_BASE_URL이 설정되지 않았습니다. 로컬 분석으로 대체합니다.")
            # Fallback을 반환하는 간단한 클래스
            class LocalClient:
                async def achain(self, prompt: str) -> str:
                    return _local_fallback(prompt)
            return LocalClient()
        
        return PrivateLLMClient(
            base_url=base_url,
            model=model,
            api_key=api_key
        )
    
    else:
        # OpenAI 사용 (기본값) - config 파일에서 값 가져오기
        openai_config = get_openai_config(config)
        model = openai_config["model"]
        api_key = openai_config["api_key"]
        
        print(f"🔧 OpenAI 설정:")
        print(f"   Model: {model}")
        print(f"   API Key: {'설정됨' if api_key else '없음'}")
        
        return OpenAIClient(model=model)


