"""
LangGraph 워크플로우 테스트
"""
import pytest
from app.graph.workflow import CIErrorAnalyzer, run_analysis


def test_error_type_classification():
    """오류 타입 분류 테스트"""
    analyzer = CIErrorAnalyzer()
    
    # Tasking
    symptoms_tasking = ["tasking", "c166", "compiler error"]
    error_type = analyzer._classify_error_type(symptoms_tasking)
    assert error_type == "tasking"
    
    # NXP
    symptoms_nxp = ["nxp", "s32k", "compilation failed"]
    error_type = analyzer._classify_error_type(symptoms_nxp)
    assert error_type == "nxp"
    
    # Polyspace
    symptoms_poly = ["polyspace", "misra violation"]
    error_type = analyzer._classify_error_type(symptoms_poly)
    assert error_type == "polyspace"


def test_kb_confidence_calculation():
    """KB 신뢰도 계산 테스트"""
    analyzer = CIErrorAnalyzer()
    
    # 빈 결과
    conf = analyzer._calculate_kb_confidence([])
    assert conf == 0.0
    
    # 높은 점수
    kb_hits = [
        {"score": 0.9},
        {"score": 0.8}
    ]
    conf = analyzer._calculate_kb_confidence(kb_hits)
    assert conf > 0.8
    
    # 낮은 점수
    kb_hits_low = [
        {"score": 0.1},
        {"score": 0.2}
    ]
    conf_low = analyzer._calculate_kb_confidence(kb_hits_low)
    assert conf_low < 0.5


def test_security_validation():
    """보안 검증 테스트"""
    analyzer = CIErrorAnalyzer()
    
    # 안전한 키워드
    safe_keywords = ["tasking", "compiler", "error"]
    assert analyzer._is_search_safe(safe_keywords, "tasking") == True
    
    # 민감한 키워드
    sensitive_keywords = ["password", "secret", "key"]
    assert analyzer._is_search_safe(sensitive_keywords, "unknown") == False
    
    # 시스템 키워드 (3개 이상)
    system_keywords = ["path", "directory", "config", "file", "setting"]
    assert analyzer._is_search_safe(system_keywords, "unknown") == False


def test_automotive_sw_related():
    """자동차 SW 관련성 검증 테스트"""
    analyzer = CIErrorAnalyzer()
    
    # 자동차 SW 관련
    auto_keywords = ["tasking", "automotive"]
    assert analyzer._is_automotive_sw_related(auto_keywords, "tasking") == True
    
    # 비관련
    non_auto_keywords = ["javascript", "web", "browser"]
    assert analyzer._is_automotive_sw_related(non_auto_keywords, "unknown") == False


def test_run_analysis(sample_ci_log):
    """전체 분석 워크플로우 테스트"""
    result = run_analysis(
        ci_log=sample_ci_log,
        context="테스트 컨텍스트",
        repository="test-repo"
    )
    
    assert "symptoms" in result
    assert "error_type" in result
    assert "confidence" in result
    assert "kb_confidence" in result
    assert "security_status" in result
    assert "analysis" in result
    
    assert len(result["symptoms"]) > 0
    assert result["error_type"] in ["tasking", "nxp", "polyspace", "simulink", "autosar", "can", "compilation", "ci", "unknown"]
    assert 0 <= result["confidence"] <= 1.0
    assert result["security_status"] in ["kb_only", "verified", "blocked", "error", "pending"]
