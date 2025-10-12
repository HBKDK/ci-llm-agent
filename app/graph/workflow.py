"""
LangGraph 기반 CI 오류 분석 워크플로우
"""
import os
from typing import Dict, List, TypedDict, Annotated, Any
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
# DuckDuckGo 도구 제거 - 자동차 SW 특화 검색 시스템 사용

from app.kb.db import ensure_initialized, search_kb
from app.utils.text import extract_symptoms, truncate_tokens


class CIWorkflowState(TypedDict, total=False):
    """워크플로우 상태 정의 - total=False로 모든 키를 선택적으로 설정"""
    # 입력
    ci_log: str
    context: str
    repository: str
    
    # 중간 결과
    symptoms: List[str]
    kb_hits: List[Dict]
    web_hits: List[Dict]
    
    # 보안 관련
    security_status: str
    kb_confidence: float
    
    # 최종 결과
    analysis: str
    confidence: float
    error_type: str


class CIErrorAnalyzer:
    """CI 오류 분석 워크플로우"""
    
    def __init__(self):
        self.llm = self._get_llm()
        # DuckDuckGo 도구 제거 - 새로운 자동차 SW 특화 검색 시스템 사용
        ensure_initialized()
    
    def _get_llm(self):
        """LLM 초기화"""
        llm_provider = os.getenv("LLM_PROVIDER", "").lower()
        
        # LLM_PROVIDER가 비어있으면 LLM 비활성화
        if not llm_provider:
            return None
        
        if llm_provider == "private":
            # Private LLM
            base_url = os.getenv("PRIVATE_LLM_BASE_URL")
            if not base_url:
                print("⚠️ PRIVATE_LLM_BASE_URL 미설정, LLM 비활성화")
                return None
            
            return ChatOpenAI(
                model=os.getenv("PRIVATE_LLM_MODEL", "llama-3-70b"),
                temperature=0.2,
                openai_api_key=os.getenv("PRIVATE_LLM_API_KEY", "not-needed"),
                openai_api_base=base_url
            )
        else:
            # OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                print("⚠️ OPENAI_API_KEY 미설정, LLM 비활성화")
                return None
            
            return ChatOpenAI(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                temperature=0.2,
                api_key=api_key
            )
        
        return None
    
    def extract_symptoms_node(self, state: CIWorkflowState) -> Dict:
        """증상 추출 노드"""
        symptoms = extract_symptoms(state["ci_log"])
        
        # 오류 타입 분류
        error_type = self._classify_error_type(symptoms)
        
        return {
            "symptoms": symptoms,
            "error_type": error_type
        }
    
    def search_knowledge_base_node(self, state: CIWorkflowState) -> Dict:
        """지식베이스 검색 노드"""
        query = "\n".join(state["symptoms"])
        kb_hits = search_kb(query=query, top_k=5)
        
        # KB 신뢰도 계산
        kb_confidence = self._calculate_kb_confidence(kb_hits)
        
        return {
            "kb_hits": kb_hits,
            "kb_confidence": kb_confidence
        }
    
    # 웹 검색 노드 제거 (현재 버전에서는 KB 검색만 사용)
    # TODO: 향후 필요시 웹 검색 기능 추가 가능
    
    def _calculate_kb_confidence(self, kb_hits: List[Dict]) -> float:
        """KB 검색 결과 신뢰도 계산"""
        if not kb_hits:
            return 0.0
        
        # KB 결과의 점수 기반 신뢰도 계산
        total_score = sum(hit.get("score", 0) for hit in kb_hits)
        avg_score = total_score / len(kb_hits)
        
        # KB 결과 개수에 따른 보너스
        count_bonus = min(len(kb_hits) * 0.1, 0.3)
        
        return min(avg_score + count_bonus, 1.0)
    
    # 웹 검색 보안 메서드들 (현재 미사용 - 향후 웹 검색 추가 시 활성화)
    
    def _is_search_safe(self, keywords: List[str], error_type: str) -> bool:
        """검색 쿼리의 보안 검증"""
        # 보안 민감 키워드 목록
        sensitive_keywords = [
            "password", "secret", "key", "token", "credential",
            "auth", "login", "admin", "root", "access",
            "security", "encryption", "certificate", "ssl", "tls",
            "vulnerability", "exploit", "hack", "attack", "breach",
            "confidential", "proprietary", "internal", "private"
        ]
        
        # 시스템 정보 노출 키워드
        system_keywords = [
            "path", "directory", "file", "config", "setting",
            "environment", "variable", "server", "host", "ip",
            "database", "connection", "url", "endpoint"
        ]
        
        # 검색 쿼리 텍스트
        query_text = " ".join(keywords).lower()
        
        # 1. 보안 민감 키워드 검사
        for sensitive in sensitive_keywords:
            if sensitive in query_text:
                print(f"보안 민감 키워드 감지: {sensitive}")
                return False
        
        # 2. 시스템 정보 노출 키워드 검사 (경고 수준)
        system_count = sum(1 for sys_kw in system_keywords if sys_kw in query_text)
        if system_count >= 3:  # 3개 이상 시스템 키워드
            print(f"시스템 정보 노출 위험: {system_count}개 키워드")
            return False
        
        # 3. 자동차 SW 도메인 특화 보안 검사
        if not self._is_automotive_sw_related(keywords, error_type):
            print("자동차 SW 관련성 부족, 검색 차단")
            return False
        
        return True
    
    def _is_automotive_sw_related(self, keywords: List[str], error_type: str) -> bool:
        """자동차 SW 관련성 검증"""
        automotive_terms = [
            "tasking", "nxp", "polyspace", "simulink", "autosar",
            "can", "canoe", "vector", "davinci", "misra", "iso26262",
            "c166", "c251", "carm", "s32k", "s32", "tricore", "aurix",
            "compiler", "build", "linker", "assembler", "code generation",
            "automotive", "embedded", "ecu", "mcu", "vehicle"
        ]
        
        query_text = " ".join(keywords).lower()
        
        # 자동차 SW 관련 키워드가 있는지 확인
        automotive_count = sum(1 for term in automotive_terms if term in query_text)
        
        # 최소 1개 이상의 자동차 SW 관련 키워드 필요
        return automotive_count >= 1
    
    def _filter_sensitive_content(self, web_hits: List[Dict]) -> List[Dict]:
        """웹 검색 결과의 민감한 내용 필터링"""
        filtered_hits = []
        
        for hit in web_hits:
            title = hit.get("title", "").lower()
            snippet = hit.get("snippet", "").lower()
            url = hit.get("url", "").lower()
            
            # 민감한 키워드가 포함된 결과 제외
            sensitive_patterns = [
                "password", "secret", "key", "token", "credential",
                "admin", "root", "login", "auth", "security",
                "vulnerability", "exploit", "hack", "attack",
                "confidential", "proprietary", "internal"
            ]
            
            is_sensitive = any(pattern in title or pattern in snippet or pattern in url 
                             for pattern in sensitive_patterns)
            
            if not is_sensitive:
                filtered_hits.append(hit)
            else:
                print(f"민감한 내용 감지, 결과 제외: {hit.get('title', '')[:50]}...")
        
        return filtered_hits
    
    # 웹 검색 메서드들 (현재 비활성화 - KB만 사용)
    # TODO: 나중에 웹 검색 기능 추가 시 활성화
    
    def analyze_with_llm_node(self, state: CIWorkflowState) -> Dict:
        """LLM 분석 노드"""
        if not self.llm:
            # LLM이 없으면 간단한 분석 제공
            return {
                "analysis": self._fallback_analysis(state),
                "confidence": 0.7
            }
        
        prompt = self._build_analysis_prompt(state)
        
        try:
            messages = [
                SystemMessage(content="당신은 CI/CD 오류 분석 전문가입니다. 한국어로 상세한 분석과 해결책을 제시하세요."),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            return {
                "analysis": response.content,
                "confidence": self._calculate_confidence(state)
            }
            
        except Exception as e:
            print(f"LLM 분석 오류: {e}")
            return {
                "analysis": self._fallback_analysis(state),
                "confidence": 0.7
            }
    
    def _classify_error_type(self, symptoms: List[str]) -> str:
        """자동차 SW 개발 환경 오류 타입 분류"""
        error_keywords = {
            "tasking": [
                "tasking", "c166", "c251", "carm", "compiler error", 
                "tasking compiler", "code generation", "assembler error",
                "linker error", "tasking ide", "tricore", "aurix"
            ],
            "nxp": [
                "nxp", "s32", "s32k", "nxp compiler", "s32 design studio",
                "nxp mcu", "nxp ide", "nxp toolchain", "nxp debugger"
            ],
            "polyspace": [
                "polyspace", "static analysis", "code verification", 
                "polyspace bug finder", "polyspace code prover",
                "misra", "cert", "iso 26262", "polyspace error"
            ],
            "simulink": [
                "simulink", "matlab", "stateflow", "simulink error",
                "model compilation", "code generation", "targetlink",
                "embedded coder", "simulink build"
            ],
            "autosar": [
                "autosar", "vector", "davinci", "autosar cp", "autosar ap",
                "ecu extract", "bsw", "rte", "autosar configuration",
                "vector canoe", "vector cast", "autosar toolchain"
            ],
            "can": [
                "can", "canoe", "canape", "can bus", "can message",
                "can signal", "dbc", "can error", "can communication",
                "vector canoe", "peak can", "canalyzer"
            ],
            "compilation": [
                "compilation error", "build error", "make error", "makefile",
                "gcc", "g++", "compiler", "linker", "assembler",
                "build failed", "compilation failed"
            ],
            "ci": [
                "jenkins", "gitlab ci", "github actions", "azure devops",
                "pipeline", "build pipeline", "continuous integration"
            ]
        }
        
        symptoms_text = " ".join(symptoms).lower()
        
        # 우선순위별로 검사 (특정 도구가 일반적인 키워드보다 우선)
        priority_order = ["tasking", "nxp", "polyspace", "simulink", "autosar", "can", "compilation", "ci"]
        
        for error_type in priority_order:
            if error_type in error_keywords:
                keywords = error_keywords[error_type]
                if any(keyword.lower() in symptoms_text for keyword in keywords):
                    return error_type
        
        return "unknown"
    
    def _build_analysis_prompt(self, state: CIWorkflowState) -> str:
        """분석 프롬프트 구성"""
        kb_section = "\n\n".join([
            f"[KB#{i+1}] {hit['title']}\n요약: {hit['summary']}\n해결책: {hit['fix']}"
            for i, hit in enumerate(state["kb_hits"])
        ]) or "(지식베이스 결과 없음)"
        
        web_section = "\n\n".join([
            f"[WEB#{i+1}] {hit['title']}\n내용: {hit['snippet']}"
            for i, hit in enumerate(state["web_hits"])
        ]) or "(웹 검색 결과 없음)"
        
        trimmed_log = truncate_tokens(state["ci_log"], max_chars=4000)
        
        return f"""
다음 CI 오류를 분석하고 해결책을 제시해주세요:

**컨텍스트:**
- 저장소: {state.get("repository", "알 수 없음")}
- 추가 정보: {state.get("context", "없음")}
- 오류 유형: {state["error_type"]}

**CI 로그:**
{trimmed_log}

**지식베이스 검색 결과:**
{kb_section}

**웹 검색 결과:**
{web_section}

**분석 요구사항:**
1. 오류의 핵심 원인을 1-2줄로 요약
2. 관련 근거를 KB/WEB 번호로 명시
3. 단계별 해결책 제시 (명령어/설정 예시 포함)
4. 재발 방지 방법 제안
5. 추가 체크리스트 제공

한국어로 상세하고 실용적인 답변을 작성해주세요.
"""
    
    def _fallback_analysis(self, state: CIWorkflowState) -> str:
        """LLM 없을 때 대체 분석"""
        symptoms = state["symptoms"]
        error_type = state["error_type"]
        
        return f"""## 🔍 오류 분석 (로컬 분석)

**오류 유형**: {error_type}
**핵심 증상**: {symptoms[0] if symptoms else "분석 불가"}

## 🛠️ 일반적 해결책

### 1단계: 기본 확인
- 의존성 파일 존재 확인
- 패키지 설치 상태 확인
- 버전 호환성 확인

### 2단계: 재설치 시도
```bash
# Python의 경우
pip install -r requirements.txt

# Node.js의 경우  
npm install

# Docker의 경우
docker build --no-cache .
```

### 3단계: 캐시 정리
- pip cache clear
- npm cache clean
- Docker system prune

**참고**: 더 정확한 분석을 위해 OPENAI_API_KEY를 설정하세요.
"""
    
    def _calculate_confidence(self, state: CIWorkflowState) -> float:
        """분석 신뢰도 계산"""
        confidence = 0.5  # 기본값
        
        # KB 결과가 있으면 신뢰도 증가
        if state["kb_hits"]:
            confidence += 0.3
        
        # 웹 검색 결과가 있으면 신뢰도 증가
        if state["web_hits"]:
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def should_continue(self, state: CIWorkflowState) -> str:
        """워크플로우 계속 여부 결정"""
        if state["symptoms"]:
            return "continue"
        return END
    
    def create_workflow(self) -> StateGraph:
        """LangGraph 워크플로우 생성"""
        workflow = StateGraph(CIWorkflowState)
        
        # 노드 추가 (웹 검색 비활성화)
        workflow.add_node("extract_symptoms", self.extract_symptoms_node)
        workflow.add_node("search_kb", self.search_knowledge_base_node)
        workflow.add_node("analyze_llm", self.analyze_with_llm_node)
        
        # 엣지 추가 (단순화: 증상 추출 → KB 검색 → LLM 분석)
        workflow.set_entry_point("extract_symptoms")
        workflow.add_edge("extract_symptoms", "search_kb")
        workflow.add_edge("search_kb", "analyze_llm")
        workflow.add_edge("analyze_llm", END)
        
        return workflow.compile()


def create_ci_analyzer() -> CIErrorAnalyzer:
    """CI 분석기 인스턴스 생성"""
    return CIErrorAnalyzer()


def run_analysis(ci_log: str, context: str | None = None, repository: str | None = None) -> Dict:
    """CI 오류 분석 실행"""
    analyzer = create_ci_analyzer()
    workflow = analyzer.create_workflow()
    
    initial_state = {
        "ci_log": ci_log,
        "context": context or "",
        "repository": repository or "",
        "symptoms": [],
        "kb_hits": [],
        "web_hits": [],  # 웹 검색 비활성화
        "security_status": "web_disabled",  # 웹 검색 사용 안 함
        "kb_confidence": 0.0,
        "analysis": "",
        "confidence": 0.0,
        "error_type": "unknown"
    }
    
    result = workflow.invoke(initial_state)
    
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
