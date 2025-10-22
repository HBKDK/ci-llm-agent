"""
n8n Integration Client

K8s App에서 n8n webhook을 호출하여 Private LLM 분석을 수행하는 클라이언트
"""
import os
import httpx
from typing import Dict, Any, Optional
from fastapi import HTTPException


class N8NClient:
    """n8n webhook 클라이언트"""
    
    def __init__(self):
        self.webhook_url = os.getenv("LLM_WEBHOOK_URL") or os.getenv("N8N_WEBHOOK_URL")
        self.timeout = int(os.getenv("LLM_TIMEOUT_SECONDS", os.getenv("N8N_TIMEOUT_SECONDS", "30")))
        
        if not self.webhook_url:
            print("⚠️ LLM_WEBHOOK_URL이 설정되지 않음. LLM 분석 비활성화")
    
    async def call_llm_analysis(
        self,
        ci_log: str,
        symptoms: list,
        error_type: str,
        context: Optional[str] = None,
        repository: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        LLM webhook을 호출하여 분석 수행
        
        Args:
            ci_log: CI 로그 텍스트
            symptoms: 추출된 증상 리스트
            error_type: 오류 타입
            context: 추가 컨텍스트
            repository: 저장소 이름
            
        Returns:
            Dict with 'analysis' and 'confidence' keys
            
        Raises:
            HTTPException: LLM 호출 실패시 503 에러
        """
        if not self.webhook_url:
            raise HTTPException(
                status_code=503,
                detail="LLM webhook URL이 설정되지 않음"
            )
        
        # 요청 데이터 구성
        request_data = {
            "ci_log": ci_log,
            "symptoms": symptoms,
            "error_type": error_type,
            "context": context,
            "repository": repository
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                print(f"🔄 LLM webhook 호출: {self.webhook_url}")
                
                response = await client.post(
                    self.webhook_url,
                    json=request_data,
                    headers={"Content-Type": "application/json"}
                )
                
                # HTTP 에러 체크
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=503,
                        detail=f"LLM webhook 에러: HTTP {response.status_code}"
                    )
                
                # 응답 데이터 파싱
                result = response.json()
                
                # 필수 필드 검증
                if "analysis" not in result or "confidence" not in result:
                    raise HTTPException(
                        status_code=503,
                        detail="LLM 응답 형식이 올바르지 않음: analysis, confidence 필드 필요"
                    )
                
                print(f"✅ LLM 분석 완료: 신뢰도 {result['confidence']}")
                return result
                
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=503,
                detail=f"LLM webhook 타임아웃 ({self.timeout}초)"
            )
        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail="LLM 서버 연결 실패"
            )
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"LLM webhook 호출 실패: {str(e)}"
            )


# 전역 인스턴스
n8n_client = N8NClient()
