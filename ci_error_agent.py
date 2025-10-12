#!/usr/bin/env python3
"""
CI 오류 분석 에이전트 - 클래스 기반 인터페이스
API 서버 없이 직접 인스턴스로 사용 가능
"""
import os
from typing import Dict, List, Optional, Any
from app.graph.workflow import CIErrorAnalyzer


class CIErrorAgent:
    """
    CI 오류 분석 에이전트 메인 클래스
    
    사용법:
        agent = CIErrorAgent()
        result = agent.analyze(ci_log="오류 로그", context="추가 정보")
    """
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        search_engine: str = "auto",
        kb_confidence_threshold: float = 0.8,
        enable_web_search: bool = True
    ):
        """
        CI 오류 분석 에이전트 초기화
        
        Args:
            openai_api_key: OpenAI API 키 (선택사항, 없으면 로컬 분석)
            search_engine: 검색 엔진 (auto, google, official_docs, ddg, none)
            kb_confidence_threshold: KB 신뢰도 임계값 (기본: 0.8)
            enable_web_search: 웹 검색 활성화 여부
        """
        # 환경변수 설정
        if openai_api_key:
            os.environ["OPENAI_API_KEY"] = openai_api_key
        
        if not enable_web_search:
            os.environ["SEARCH_ENGINE"] = "none"
        else:
            os.environ["SEARCH_ENGINE"] = search_engine
        
        # 설정 저장
        self.kb_confidence_threshold = kb_confidence_threshold
        self.enable_web_search = enable_web_search
        self.search_engine = search_engine
        
        # 워크플로우 초기화
        self.analyzer = CIErrorAnalyzer()
        self.workflow = self.analyzer.create_workflow()
    
    def analyze(
        self,
        ci_log: str,
        context: Optional[str] = None,
        repository: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        CI 오류 로그 분석
        
        Args:
            ci_log: CI 오류 로그 텍스트
            context: 추가 컨텍스트 정보 (선택사항)
            repository: 저장소 이름 (선택사항)
        
        Returns:
            Dict: 분석 결과
                - symptoms: 추출된 증상 리스트
                - kb_hits: KB 검색 결과
                - web_hits: 웹 검색 결과
                - security_status: 보안 상태 (kb_only, verified, blocked, error)
                - kb_confidence: KB 신뢰도
                - analysis: 분석 결과 텍스트
                - confidence: 전체 신뢰도
                - error_type: 오류 타입 (tasking, nxp, polyspace, ...)
        """
        initial_state = {
            "ci_log": ci_log,
            "context": context,
            "repository": repository,
            "symptoms": [],
            "kb_hits": [],
            "web_hits": [],
            "security_status": "pending",
            "kb_confidence": 0.0,
            "analysis": "",
            "confidence": 0.0,
            "error_type": "unknown"
        }
        
        result = self.workflow.invoke(initial_state)
        
        return {
            "symptoms": result["symptoms"],
            "kb_hits": result["kb_hits"],
            "web_hits": result["web_hits"],
            "security_status": result["security_status"],
            "kb_confidence": result["kb_confidence"],
            "analysis": result["analysis"],
            "confidence": result["confidence"],
            "error_type": result["error_type"]
        }
    
    def analyze_with_details(
        self,
        ci_log: str,
        context: Optional[str] = None,
        repository: Optional[str] = None,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        상세 정보를 포함한 CI 오류 로그 분석
        
        Args:
            ci_log: CI 오류 로그 텍스트
            context: 추가 컨텍스트 정보
            repository: 저장소 이름
            verbose: 상세 로그 출력 여부
        
        Returns:
            Dict: 상세 분석 결과
        """
        if verbose:
            print(f"🔍 CI 오류 분석 시작")
            print(f"   로그 길이: {len(ci_log)} 문자")
            print(f"   검색 엔진: {self.search_engine}")
            print(f"   KB 임계값: {self.kb_confidence_threshold}")
        
        result = self.analyze(ci_log, context, repository)
        
        if verbose:
            print(f"\n✅ 분석 완료")
            print(f"   오류 타입: {result['error_type']}")
            print(f"   보안 상태: {result['security_status']}")
            print(f"   KB 신뢰도: {result['kb_confidence']:.2f}")
            print(f"   전체 신뢰도: {result['confidence']:.2f}")
        
        return result
    
    def get_kb_only_analysis(
        self,
        ci_log: str,
        context: Optional[str] = None,
        repository: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        KB만 사용한 오프라인 분석 (웹 검색 없음)
        
        Args:
            ci_log: CI 오류 로그 텍스트
            context: 추가 컨텍스트 정보
            repository: 저장소 이름
        
        Returns:
            Dict: KB 기반 분석 결과
        """
        # 임시로 웹 검색 비활성화
        original_setting = os.environ.get("SEARCH_ENGINE", "auto")
        os.environ["SEARCH_ENGINE"] = "none"
        
        try:
            result = self.analyze(ci_log, context, repository)
            return result
        finally:
            # 원래 설정 복원
            os.environ["SEARCH_ENGINE"] = original_setting
    
    def extract_symptoms_only(self, ci_log: str) -> List[str]:
        """
        증상만 추출 (분석 없음)
        
        Args:
            ci_log: CI 오류 로그 텍스트
        
        Returns:
            List[str]: 추출된 증상 리스트
        """
        from app.utils.text import extract_symptoms
        return extract_symptoms(ci_log)
    
    def search_kb_only(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        KB 검색만 수행
        
        Args:
            query: 검색 쿼리
            top_k: 반환할 결과 개수
        
        Returns:
            List[Dict]: KB 검색 결과
        """
        from app.kb.db import search_kb
        return search_kb(query=query, top_k=top_k)
    
    def save_to_kb(
        self,
        ci_log: str,
        analysis_result: Dict[str, Any],
        auto_approve: bool = False
    ) -> Dict[str, Any]:
        """
        분석 결과를 KB에 저장 (학습)
        
        Args:
            ci_log: 원본 CI 로그
            analysis_result: analyze() 반환 결과
            auto_approve: 자동 승인 여부
        
        Returns:
            Dict: 저장 결과
        """
        from app.kb.db import add_to_kb
        
        # 분석 결과에서 정보 추출
        error_type = analysis_result.get("error_type", "unknown")
        symptoms = analysis_result.get("symptoms", [])
        analysis = analysis_result.get("analysis", "")
        
        # 제목 생성
        title = f"{error_type.upper()}: {symptoms[0] if symptoms else 'Unknown Error'}"
        
        # 요약 생성 (CI 로그의 핵심 부분)
        summary = "\n".join(symptoms[:3]) if symptoms else ci_log[:200]
        
        # 해결 방법 추출 (분석 결과에서)
        fix = analysis if analysis else "분석 결과 없음"
        
        # 태그 생성
        tags = [error_type]
        if symptoms:
            # 증상에서 키워드 추출
            for symptom in symptoms[:2]:
                words = symptom.lower().split()
                for word in words:
                    if len(word) > 3 and word.isalpha():
                        tags.append(word)
        
        # KB에 저장
        result = add_to_kb(
            title=title[:512],  # 길이 제한
            summary=summary[:4000],
            fix=fix[:4000],
            tags=list(set(tags))[:10],  # 중복 제거, 최대 10개
            auto_approve=auto_approve
        )
        
        return result
    
    def learn_from_analysis(
        self,
        ci_log: str,
        context: Optional[str] = None,
        repository: Optional[str] = None,
        save_if_confident: bool = True,
        confidence_threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        분석 후 신뢰도가 높으면 자동으로 KB에 학습
        
        Args:
            ci_log: CI 오류 로그
            context: 추가 컨텍스트
            repository: 저장소 이름
            save_if_confident: 신뢰도 높으면 자동 저장
            confidence_threshold: 저장할 최소 신뢰도
        
        Returns:
            Dict: 분석 결과 + KB 저장 결과
        """
        # 분석 실행
        result = self.analyze(ci_log, context, repository)
        
        # 신뢰도 확인 후 저장
        saved = False
        save_result = None
        
        if save_if_confident and result["confidence"] >= confidence_threshold:
            save_result = self.save_to_kb(ci_log, result, auto_approve=True)
            saved = save_result.get("status") == "success"
        
        # 결과에 저장 정보 추가
        result["saved_to_kb"] = saved
        if save_result:
            result["kb_save_result"] = save_result
        
        return result
    
    def get_config(self) -> Dict[str, Any]:
        """
        현재 에이전트 설정 반환
        
        Returns:
            Dict: 설정 정보
        """
        return {
            "search_engine": self.search_engine,
            "enable_web_search": self.enable_web_search,
            "kb_confidence_threshold": self.kb_confidence_threshold,
            "openai_api_key_set": bool(os.environ.get("OPENAI_API_KEY"))
        }
    
    def update_config(
        self,
        search_engine: Optional[str] = None,
        enable_web_search: Optional[bool] = None,
        kb_confidence_threshold: Optional[float] = None
    ):
        """
        에이전트 설정 업데이트
        
        Args:
            search_engine: 검색 엔진 변경
            enable_web_search: 웹 검색 활성화 여부
            kb_confidence_threshold: KB 신뢰도 임계값
        """
        if search_engine is not None:
            self.search_engine = search_engine
            os.environ["SEARCH_ENGINE"] = search_engine
        
        if enable_web_search is not None:
            self.enable_web_search = enable_web_search
            if not enable_web_search:
                os.environ["SEARCH_ENGINE"] = "none"
        
        if kb_confidence_threshold is not None:
            self.kb_confidence_threshold = kb_confidence_threshold
    
    def add_knowledge(
        self,
        title: str,
        summary: str,
        fix: str,
        tags: List[str]
    ) -> Dict[str, Any]:
        """
        KB에 새로운 지식 수동 추가
        
        Args:
            title: 오류 제목
            summary: 오류 요약
            fix: 해결 방법
            tags: 태그 리스트
        
        Returns:
            Dict: 저장 결과
        """
        from app.kb.db import add_to_kb
        return add_to_kb(title, summary, fix, tags, auto_approve=False)
    
    def update_knowledge(
        self,
        kb_id: int,
        title: Optional[str] = None,
        summary: Optional[str] = None,
        fix: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        KB 항목 업데이트
        
        Args:
            kb_id: 업데이트할 항목 ID
            title: 새 제목
            summary: 새 요약
            fix: 새 해결 방법
            tags: 새 태그
        
        Returns:
            Dict: 업데이트 결과
        """
        from app.kb.db import update_kb
        return update_kb(kb_id, title, summary, fix, tags)
    
    def delete_knowledge(self, kb_id: int) -> Dict[str, Any]:
        """
        KB에서 항목 삭제
        
        Args:
            kb_id: 삭제할 항목 ID
        
        Returns:
            Dict: 삭제 결과
        """
        from app.kb.db import delete_from_kb
        return delete_from_kb(kb_id)
    
    def export_kb(self, output_path: Optional[str] = None) -> str:
        """
        KB를 JSON 파일로 내보내기
        
        Args:
            output_path: 출력 파일 경로
        
        Returns:
            str: 생성된 파일 경로
        """
        from app.kb.db import export_kb_to_json
        return export_kb_to_json(output_path)
    
    def get_all_kb_entries(self) -> List[Dict[str, Any]]:
        """
        모든 KB 항목 조회
        
        Returns:
            List[Dict]: 모든 KB 항목
        """
        from app.kb.db import get_all_documents
        return get_all_documents()


# 간편한 사용을 위한 팩토리 함수들
def create_agent(
    openai_api_key: Optional[str] = None,
    search_engine: str = "auto",
    enable_web_search: bool = True
) -> CIErrorAgent:
    """
    CI 오류 분석 에이전트 생성
    
    Args:
        openai_api_key: OpenAI API 키
        search_engine: 검색 엔진
        enable_web_search: 웹 검색 활성화
    
    Returns:
        CIErrorAgent: 초기화된 에이전트 인스턴스
    """
    return CIErrorAgent(
        openai_api_key=openai_api_key,
        search_engine=search_engine,
        enable_web_search=enable_web_search
    )


def create_secure_agent(openai_api_key: Optional[str] = None) -> CIErrorAgent:
    """
    보안 강화 에이전트 생성 (웹 검색 비활성화)
    
    Args:
        openai_api_key: OpenAI API 키
    
    Returns:
        CIErrorAgent: 보안 강화 에이전트 인스턴스
    """
    return CIErrorAgent(
        openai_api_key=openai_api_key,
        search_engine="none",
        enable_web_search=False
    )


def create_automotive_agent(openai_api_key: Optional[str] = None) -> CIErrorAgent:
    """
    자동차 SW 특화 에이전트 생성 (자동 검색 엔진 선택)
    
    Args:
        openai_api_key: OpenAI API 키
    
    Returns:
        CIErrorAgent: 자동차 SW 특화 에이전트 인스턴스
    """
    return CIErrorAgent(
        openai_api_key=openai_api_key,
        search_engine="auto",
        enable_web_search=True,
        kb_confidence_threshold=0.8
    )


# 간단한 분석 함수
def quick_analyze(ci_log: str, context: Optional[str] = None) -> str:
    """
    빠른 분석 (결과 텍스트만 반환)
    
    Args:
        ci_log: CI 오류 로그
        context: 추가 컨텍스트
    
    Returns:
        str: 분석 결과 텍스트
    """
    agent = CIErrorAgent()
    result = agent.analyze(ci_log, context)
    return result["analysis"]


if __name__ == "__main__":
    # 사용 예시
    print("🚗 CI 오류 분석 에이전트 - 클래스 기반 인터페이스")
    print("=" * 60)
    
    # 기본 사용법
    print("\n📋 사용 예시:")
    print("""
# 1. 기본 사용
agent = CIErrorAgent()
result = agent.analyze(ci_log="오류 로그", context="추가 정보")

# 2. OpenAI API 키 설정
agent = CIErrorAgent(openai_api_key="your-api-key")

# 3. 보안 모드 (웹 검색 비활성화)
agent = CIErrorAgent(enable_web_search=False)

# 4. 팩토리 함수 사용
agent = create_automotive_agent()
result = agent.analyze(ci_log="오류 로그")

# 5. KB만 사용
result = agent.get_kb_only_analysis(ci_log="오류 로그")

# 6. 간단한 분석
analysis_text = quick_analyze(ci_log="오류 로그")
""")
