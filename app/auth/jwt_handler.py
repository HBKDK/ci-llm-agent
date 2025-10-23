"""
JWT 토큰 기반 승인 시스템
"""
import os
import jwt
from datetime import datetime, timedelta
from typing import Dict, Optional


SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
TOKEN_EXPIRE_DAYS = 7

# JWT secret key 검증
if SECRET_KEY == "your-secret-key-change-in-production":
    import warnings
    warnings.warn("⚠️ JWT_SECRET_KEY가 기본값으로 설정되어 있습니다. 프로덕션에서는 반드시 변경하세요!", UserWarning)


def create_approval_token(
    analysis_id: int,
    pending_approval_id: int,
    admin_email: str
) -> str:
    """
    승인 토큰 생성
    
    Args:
        analysis_id: 분석 이력 ID
        pending_approval_id: 승인 대기 ID
        admin_email: 관리자 이메일
    
    Returns:
        str: JWT 토큰
    """
    try:
        expire = datetime.utcnow() + timedelta(days=TOKEN_EXPIRE_DAYS)
        
        payload = {
            "analysis_id": int(analysis_id),
            "pending_approval_id": int(pending_approval_id),
            "admin_email": str(admin_email),
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "kb_approval"
        }
        
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        
        # 생성된 토큰이 문자열인지 확인
        if not isinstance(token, str):
            raise ValueError("토큰 생성 실패: 문자열이 아닌 토큰이 생성됨")
        
        return token
        
    except Exception as e:
        raise ValueError(f"토큰 생성 중 오류가 발생했습니다: {str(e)}")


def verify_approval_token(token: str) -> Optional[Dict]:
    """
    승인 토큰 검증
    
    Args:
        token: JWT 토큰
    
    Returns:
        Dict: 토큰 페이로드 (유효한 경우)
        None: 토큰이 유효하지 않은 경우
    """
    # 토큰 형식 기본 검증
    if not token or not isinstance(token, str):
        return {"error": "토큰이 제공되지 않았습니다."}
    
    # JWT 토큰 형식 검증 (3개 부분으로 구성되어야 함)
    token_parts = token.split('.')
    if len(token_parts) != 3:
        return {"error": "잘못된 토큰 형식입니다."}
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # 토큰 타입 확인
        if payload.get("type") != "kb_approval":
            return {"error": "잘못된 토큰 타입입니다."}
        
        return payload
    
    except jwt.ExpiredSignatureError:
        return {"error": "토큰이 만료되었습니다."}
    except jwt.InvalidTokenError as e:
        # 더 구체적인 오류 메시지 제공
        error_msg = str(e)
        if "Invalid token" in error_msg or "access token is invalid" in error_msg:
            return {"error": "유효하지 않은 토큰입니다."}
        elif "Invalid signature" in error_msg:
            return {"error": "토큰 서명이 유효하지 않습니다."}
        elif "Invalid header" in error_msg:
            return {"error": "토큰 헤더가 유효하지 않습니다."}
        else:
            return {"error": f"토큰 검증 실패: {error_msg}"}
    except Exception as e:
        return {"error": f"토큰 처리 중 오류가 발생했습니다: {str(e)}"}


def create_modification_token(
    pending_approval_id: int,
    admin_email: str
) -> str:
    """
    수정용 토큰 생성 (승인 전 수정할 수 있는 토큰)
    
    Args:
        pending_approval_id: 승인 대기 ID
        admin_email: 관리자 이메일
    
    Returns:
        str: JWT 토큰
    """
    try:
        expire = datetime.utcnow() + timedelta(days=TOKEN_EXPIRE_DAYS)
        
        payload = {
            "pending_approval_id": int(pending_approval_id),
            "admin_email": str(admin_email),
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "kb_modification"
        }
        
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        
        # 생성된 토큰이 문자열인지 확인
        if not isinstance(token, str):
            raise ValueError("토큰 생성 실패: 문자열이 아닌 토큰이 생성됨")
        
        return token
        
    except Exception as e:
        raise ValueError(f"수정 토큰 생성 중 오류가 발생했습니다: {str(e)}")

