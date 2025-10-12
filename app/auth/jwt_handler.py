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
    expire = datetime.utcnow() + timedelta(days=TOKEN_EXPIRE_DAYS)
    
    payload = {
        "analysis_id": analysis_id,
        "pending_approval_id": pending_approval_id,
        "admin_email": admin_email,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "kb_approval"
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


def verify_approval_token(token: str) -> Optional[Dict]:
    """
    승인 토큰 검증
    
    Args:
        token: JWT 토큰
    
    Returns:
        Dict: 토큰 페이로드 (유효한 경우)
        None: 토큰이 유효하지 않은 경우
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # 토큰 타입 확인
        if payload.get("type") != "kb_approval":
            return None
        
        return payload
    
    except jwt.ExpiredSignatureError:
        return {"error": "토큰이 만료되었습니다."}
    except jwt.InvalidTokenError:
        return {"error": "유효하지 않은 토큰입니다."}


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
    expire = datetime.utcnow() + timedelta(days=TOKEN_EXPIRE_DAYS)
    
    payload = {
        "pending_approval_id": pending_approval_id,
        "admin_email": admin_email,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "kb_modification"
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

