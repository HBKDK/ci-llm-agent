import os
from dataclasses import dataclass
from typing import Protocol

from tenacity import retry, stop_after_attempt, wait_exponential


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
    LLM 클라이언트 생성 (환경변수 기반)
    
    환경변수:
        LLM_PROVIDER: openai (기본값) 또는 private
        
        OpenAI 사용 시:
            OPENAI_API_KEY: OpenAI API 키
        
        Private LLM 사용 시:
            PRIVATE_LLM_BASE_URL: Private LLM 서버 URL (예: http://llm-server:8000/v1)
            PRIVATE_LLM_MODEL: 모델 이름 (예: llama-3-70b, mistral-7b)
            PRIVATE_LLM_API_KEY: Private LLM API 키 (없으면 빈 문자열)
    """
    llm_provider = os.getenv("LLM_PROVIDER", "openai").lower()
    
    if llm_provider == "private":
        # Private LLM 사용
        base_url = os.getenv("PRIVATE_LLM_BASE_URL")
        model = os.getenv("PRIVATE_LLM_MODEL", "llama-3-70b")
        api_key = os.getenv("PRIVATE_LLM_API_KEY", "not-needed")
        
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
        # OpenAI 사용 (기본값)
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        return OpenAIClient(model=model)


