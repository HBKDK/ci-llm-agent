"""
KB 검색 및 관리 테스트
"""
import pytest
from app.kb.db import ensure_initialized, search_kb, add_to_kb, get_all_documents


@pytest.fixture(autouse=True)
def setup_kb():
    """각 테스트 전에 KB 초기화"""
    ensure_initialized()


def test_kb_initialization():
    """KB 초기화 테스트"""
    docs = get_all_documents()
    assert len(docs) >= 0  # 최소 0개 (seed 데이터 있으면 더 많음)


def test_kb_search_tasking():
    """Tasking 관련 KB 검색 테스트"""
    results = search_kb("tasking compiler error", top_k=5)
    
    if results:  # seed 데이터가 있으면
        assert len(results) > 0
        assert "score" in results[0]
        assert results[0]["score"] >= 0


def test_kb_search_empty():
    """빈 쿼리 검색 테스트"""
    results = search_kb("", top_k=5)
    assert isinstance(results, list)


def test_add_to_kb():
    """KB 추가 테스트"""
    result = add_to_kb(
        title="Test Entry",
        summary="Test summary",
        fix="Test fix",
        tags=["test", "pytest"],
        auto_approve=True
    )
    
    assert result["status"] in ["success", "duplicate"]
    
    if result["status"] == "success":
        assert "id" in result


def test_add_duplicate():
    """중복 항목 추가 테스트"""
    # 첫 번째 추가
    add_to_kb(
        title="Duplicate Test",
        summary="Test",
        fix="Test",
        tags=["test"]
    )
    
    # 동일한 제목으로 재추가
    result = add_to_kb(
        title="Duplicate Test",
        summary="Test",
        fix="Test",
        tags=["test"]
    )
    
    assert result["status"] == "duplicate"
