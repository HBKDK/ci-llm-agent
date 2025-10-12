"""
증상 추출 테스트
"""
import pytest
from app.utils.text import extract_symptoms


def test_extract_symptoms_tasking(sample_ci_log):
    """Tasking 로그 증상 추출 테스트"""
    symptoms = extract_symptoms(sample_ci_log)
    
    assert len(symptoms) > 0
    assert any("error" in s.lower() for s in symptoms)
    assert any("code generation" in s.lower() for s in symptoms)


def test_extract_symptoms_nxp(sample_nxp_log):
    """NXP 로그 증상 추출 테스트"""
    symptoms = extract_symptoms(sample_nxp_log)
    
    assert len(symptoms) > 0
    assert any("undefined reference" in s.lower() for s in symptoms)
    assert any("failed" in s.lower() for s in symptoms)


def test_extract_symptoms_polyspace(sample_polyspace_log):
    """Polyspace 로그 증상 추출 테스트"""
    symptoms = extract_symptoms(sample_polyspace_log)
    
    assert len(symptoms) > 0
    assert any("misra" in s.lower() for s in symptoms)
    assert any("violation" in s.lower() for s in symptoms)


def test_extract_symptoms_empty():
    """빈 로그 테스트"""
    symptoms = extract_symptoms("")
    assert symptoms == []


def test_extract_symptoms_no_error():
    """오류 없는 로그 테스트"""
    log = "Build successful\nAll tests passed\nDeployment complete"
    symptoms = extract_symptoms(log)
    
    # fallback으로 마지막 5줄 반환
    assert len(symptoms) > 0
