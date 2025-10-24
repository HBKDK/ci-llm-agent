"""
Config 파일 로딩 유틸리티
"""
import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    설정 파일을 로드합니다.
    
    Args:
        config_path: 설정 파일 경로. None이면 기본 경로들을 시도합니다.
        
    Returns:
        설정 딕셔너리
        
    Raises:
        FileNotFoundError: 설정 파일을 찾을 수 없을 때
        yaml.YAMLError: YAML 파싱 오류
    """
    if config_path is None:
        # 기본 설정 파일 경로들 시도
        possible_paths = [
            "local_llm_server_config.yaml",
            "/workspace/local_llm_server_config.yaml",
            "config.yaml",
            "/workspace/config.yaml"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                config_path = path
                break
        else:
            raise FileNotFoundError("설정 파일을 찾을 수 없습니다. 다음 경로들을 확인하세요: " + ", ".join(possible_paths))
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    return config


def get_azure_config(config: Dict[str, Any]) -> Dict[str, str]:
    """
    Azure OpenAI 설정을 추출합니다.
    
    Args:
        config: 로드된 설정 딕셔너리
        
    Returns:
        Azure OpenAI 설정 딕셔너리
    """
    azure_config = config.get("azure_openai", {})
    
    # 환경변수 우선, config 파일은 fallback
    return {
        "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT") or azure_config.get("base_url", ""),
        "deployment_name": os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME") or azure_config.get("deployment_name", ""),
        "api_key": os.getenv("AZURE_OPENAI_API_KEY") or azure_config.get("api_key", ""),
        "api_version": os.getenv("AZURE_OPENAI_API_VERSION") or azure_config.get("api_version", "2024-02-15-preview")
    }


def get_private_llm_config(config: Dict[str, Any]) -> Dict[str, str]:
    """
    Private LLM 설정을 추출합니다.
    
    Args:
        config: 로드된 설정 딕셔너리
        
    Returns:
        Private LLM 설정 딕셔너리
    """
    # 환경변수 우선, config 파일은 fallback
    return {
        "base_url": os.getenv("PRIVATE_LLM_BASE_URL") or config.get("private_llm", {}).get("base_url", ""),
        "model": os.getenv("PRIVATE_LLM_MODEL") or config.get("private_llm", {}).get("model", "llama-3-70b"),
        "api_key": os.getenv("PRIVATE_LLM_API_KEY") or config.get("private_llm", {}).get("api_key", "")
    }


def get_openai_config(config: Dict[str, Any]) -> Dict[str, str]:
    """
    OpenAI 설정을 추출합니다.
    
    Args:
        config: 로드된 설정 딕셔너리
        
    Returns:
        OpenAI 설정 딕셔너리
    """
    # 환경변수 우선, config 파일은 fallback
    return {
        "api_key": os.getenv("OPENAI_API_KEY") or config.get("openai", {}).get("api_key", ""),
        "model": os.getenv("OPENAI_MODEL") or config.get("openai", {}).get("model", "gpt-4o-mini")
    }