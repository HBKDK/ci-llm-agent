"""
LangGraph 워크플로우 시각화 및 디버깅 도구
"""
import os
from typing import Dict, Any
from app.graph.workflow import CIErrorAnalyzer


def visualize_workflow():
    """워크플로우 그래프 시각화"""
    analyzer = CIErrorAnalyzer()
    workflow = analyzer.create_workflow()
    
    # 그래프 이미지 생성
    try:
        from IPython.display import Image, display
        img_path = workflow.get_graph().draw_mermaid_png()
        return img_path
    except ImportError:
        print("IPython이 설치되지 않았습니다. pip install ipython으로 설치하세요.")
        return None


def get_workflow_info() -> Dict[str, Any]:
    """워크플로우 정보 반환"""
    analyzer = CIErrorAnalyzer()
    workflow = analyzer.create_workflow()
    
    graph = workflow.get_graph()
    
    return {
        "nodes": list(graph.nodes.keys()),
        "edges": [(edge.source, edge.target) for edge in graph.edges],
        "entry_point": graph.first,
        "end_points": graph.last,
        "total_nodes": len(graph.nodes),
        "total_edges": len(graph.edges)
    }


def debug_workflow_step_by_step(ci_log: str, context: str = None, repository: str = None):
    """워크플로우를 단계별로 디버깅"""
    analyzer = CIErrorAnalyzer()
    workflow = analyzer.create_workflow()
    
    initial_state = {
        "ci_log": ci_log,
        "context": context,
        "repository": repository,
        "symptoms": [],
        "kb_hits": [],
        "web_hits": [],
        "analysis": "",
        "confidence": 0.0,
        "error_type": "unknown"
    }
    
    print("🔍 워크플로우 단계별 디버깅")
    print("=" * 50)
    
    # 각 노드를 개별적으로 실행하여 결과 확인
    print("1️⃣ 증상 추출 단계")
    state_after_symptoms = analyzer.extract_symptoms_node(initial_state.copy())
    print(f"   추출된 증상: {state_after_symptoms['symptoms']}")
    print(f"   오류 타입: {state_after_symptoms['error_type']}")
    print()
    
    print("2️⃣ 지식베이스 검색 단계")
    state_after_kb = analyzer.search_knowledge_base_node(state_after_symptoms.copy())
    print(f"   KB 검색 결과: {len(state_after_kb['kb_hits'])}개")
    for i, hit in enumerate(state_after_kb['kb_hits'][:2]):
        print(f"   - {i+1}. {hit['title']} (점수: {hit.get('score', 0):.3f})")
    print()
    
    print("3️⃣ 웹 검색 단계")
    state_after_web = analyzer.search_web_node(state_after_symptoms.copy())
    print(f"   웹 검색 결과: {len(state_after_web['web_hits'])}개")
    for i, hit in enumerate(state_after_web['web_hits'][:2]):
        print(f"   - {i+1}. {hit['title']}")
    print()
    
    print("4️⃣ LLM 분석 단계")
    final_state = analyzer.analyze_with_llm_node(state_after_kb.copy())
    final_state['web_hits'] = state_after_web['web_hits']  # 웹 결과 병합
    print(f"   분석 완료 - 신뢰도: {final_state['confidence']:.2f}")
    print(f"   분석 결과 미리보기: {final_state['analysis'][:200]}...")
    print()
    
    print("✅ 전체 워크플로우 실행")
    full_result = workflow.invoke(initial_state)
    print(f"   최종 신뢰도: {full_result['confidence']:.2f}")
    print(f"   최종 오류 타입: {full_result['error_type']}")
    
    return full_result


def test_workflow_with_samples():
    """샘플 데이터로 워크플로우 테스트"""
    test_cases = [
        {
            "name": "Python ModuleNotFoundError",
            "ci_log": "ModuleNotFoundError: No module named 'fastapi'\nTraceback (most recent call last):\n  File \"/app/main.py\", line 1, in <module>\n    from fastapi import FastAPI\nModuleNotFoundError: No module named 'fastapi'",
            "context": "Docker 컨테이너에서 실행 중",
            "repository": "my-api-project"
        },
        {
            "name": "Node.js 의존성 오류",
            "ci_log": "npm ERR! code ERESOLVE\nnpm ERR! ERESOLVE unable to resolve dependency tree\nnpm ERR! While resolving: my-app@1.0.0\nnpm ERR! Found: react@18.2.0\nnpm ERR! Could not resolve dependency:\nnpm ERR! peer react@\">=16.9.0\" from react-router-dom@6.8.1",
            "context": "React 프로젝트 빌드 실패",
            "repository": "my-react-app"
        },
        {
            "name": "Docker 빌드 실패",
            "ci_log": "Step 3/5 : RUN pip install -r requirements.txt\n ---> Running in abc123\nERROR: Could not find a version that satisfies the requirement fastapi==0.104.1\nERROR: No matching distribution found for fastapi==0.104.1\nThe command '/bin/sh -c pip install -r requirements.txt' returned a non-zero code: 1",
            "context": "Docker 이미지 빌드 중",
            "repository": "my-docker-app"
        }
    ]
    
    print("🧪 워크플로우 테스트 시작")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 테스트 케이스 {i}: {test_case['name']}")
        print("-" * 40)
        
        result = debug_workflow_step_by_step(
            ci_log=test_case['ci_log'],
            context=test_case['context'],
            repository=test_case['repository']
        )
        
        print(f"   ✅ 완료 - 신뢰도: {result['confidence']:.2f}")
    
    print(f"\n🎉 모든 테스트 케이스 완료!")


if __name__ == "__main__":
    # 워크플로우 정보 출력
    info = get_workflow_info()
    print("🔧 워크플로우 정보:")
    print(f"   노드 수: {info['total_nodes']}")
    print(f"   엣지 수: {info['total_edges']}")
    print(f"   시작점: {info['entry_point']}")
    print(f"   종료점: {info['end_points']}")
    
    # 샘플 테스트 실행
    test_workflow_with_samples()

