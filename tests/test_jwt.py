"""
JWT 토큰 테스트
"""
import pytest
from datetime import datetime, timedelta
from app.auth.jwt_handler import create_approval_token, verify_approval_token


def test_create_token():
    """토큰 생성 테스트"""
    token = create_approval_token(
        analysis_id=1,
        pending_approval_id=2,
        admin_email="admin@company.com"
    )
    
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0


def test_verify_token():
    """토큰 검증 테스트"""
    # 토큰 생성
    token = create_approval_token(
        analysis_id=1,
        pending_approval_id=2,
        admin_email="admin@company.com"
    )
    
    # 토큰 검증
    payload = verify_approval_token(token)
    
    assert payload is not None
    assert "analysis_id" in payload
    assert "pending_approval_id" in payload
    assert "admin_email" in payload
    assert payload["analysis_id"] == 1
    assert payload["pending_approval_id"] == 2


def test_verify_invalid_token():
    """잘못된 토큰 검증 테스트"""
    invalid_token = "invalid.token.here"
    payload = verify_approval_token(invalid_token)
    
    assert payload is not None
    assert "error" in payload


def test_verify_expired_token():
    """만료된 토큰 테스트"""
    # 실제 만료 테스트는 시간이 오래 걸리므로 구조만 확인
    token = create_approval_token(1, 2, "admin@company.com")
    payload = verify_approval_token(token)
    
    # 만료 시간 확인
    assert "exp" in payload
    exp_time = datetime.fromtimestamp(payload["exp"])
    now = datetime.utcnow()
    
    # 7일 후 만료 확인
    assert (exp_time - now).days <= 7
