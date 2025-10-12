"""
FastAPI 엔드포인트 테스트
"""
import pytest
from fastapi.testclient import TestClient
from app.main_simple import app

client = TestClient(app)


def test_root_endpoint():
    """루트 엔드포인트 테스트"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_health_endpoint():
    """헬스 체크 엔드포인트 테스트"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


def test_analyze_endpoint(sample_ci_log):
    """분석 엔드포인트 테스트"""
    response = client.post(
        "/analyze",
        json={
            "ci_log": sample_ci_log,
            "repository": "test-repo",
            "job_name": "TEST-JOB",
            "build_number": 1
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "analysis_id" in data
    assert "error_type" in data
    assert "confidence" in data
    assert "approval_token" in data or data.get("recommend_save") == False


def test_analyze_missing_log():
    """로그 누락 시 오류 테스트"""
    response = client.post(
        "/analyze",
        json={}
    )
    
    assert response.status_code == 422  # Validation error


def test_kb_list_endpoint():
    """KB 목록 조회 테스트"""
    response = client.get("/kb/list")
    assert response.status_code == 200
    data = response.json()
    
    assert "total" in data
    assert "entries" in data
    assert isinstance(data["entries"], list)
