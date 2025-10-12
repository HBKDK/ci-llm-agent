"""
전체 기능 테스트 스크립트
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def print_section(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def test_health():
    """헬스 체크 테스트"""
    print_section("1. 헬스 체크 테스트")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✅ Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_analyze():
    """CI 오류 분석 테스트"""
    print_section("2. CI 오류 분석 테스트")
    
    test_data = {
        "ci_log": """Tasking Compiler Error: code generation failed
main.c(45): error: insufficient memory for code generation
main.c(50): warning: variable 'buffer' may be uninitialized
Tasking IDE: Build failed with exit code 1
Compiler options: -O2 -W1""",
        "repository": "automotive-ecu-project",
        "job_name": "BUILD-MAIN",
        "build_number": 123
    }
    
    try:
        print("📤 요청 데이터:")
        print(json.dumps(test_data, indent=2, ensure_ascii=False))
        
        response = requests.post(f"{BASE_URL}/analyze", json=test_data, timeout=60)
        print(f"\n✅ Status: {response.status_code}")
        
        result = response.json()
        print("\n📥 응답 결과:")
        print(f"   분석 ID: {result.get('analysis_id')}")
        print(f"   오류 타입: {result.get('error_type')}")
        print(f"   신뢰도: {result.get('confidence')}")
        print(f"   KB 신뢰도: {result.get('kb_confidence')}")
        print(f"   보안 상태: {result.get('security_status')}")
        print(f"   저장 권장: {result.get('recommend_save')}")
        
        if result.get('analysis'):
            print(f"\n   분석 내용 (처음 200자):")
            print(f"   {result['analysis'][:200]}...")
        
        if result.get('approval_token'):
            print(f"\n   승인 토큰: {result['approval_token'][:50]}...")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_kb_list():
    """KB 목록 조회 테스트"""
    print_section("3. KB 목록 조회 테스트")
    try:
        response = requests.get(f"{BASE_URL}/kb/list")
        print(f"✅ Status: {response.status_code}")
        
        result = response.json()
        print(f"   총 항목 수: {result.get('total')}")
        
        if result.get('entries'):
            print(f"\n   첫 번째 항목:")
            first = result['entries'][0]
            print(f"   - 제목: {first.get('title')}")
            print(f"   - 태그: {first.get('tags')}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_nxp_error():
    """NXP 오류 테스트"""
    print_section("4. NXP 오류 분석 테스트")
    
    test_data = {
        "ci_log": """NXP S32K144: compilation error
undefined reference to 'GPIO_Init'
undefined reference to 'ADC_Config'
S32K SDK library not linked
linking failed with exit code 1""",
        "repository": "nxp-automotive",
        "job_name": "BUILD-S32K",
        "build_number": 456
    }
    
    try:
        response = requests.post(f"{BASE_URL}/analyze", json=test_data, timeout=60)
        print(f"✅ Status: {response.status_code}")
        
        result = response.json()
        print(f"   오류 타입: {result.get('error_type')}")
        print(f"   신뢰도: {result.get('confidence')}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_polyspace_error():
    """Polyspace 오류 테스트"""
    print_section("5. Polyspace 오류 분석 테스트")
    
    test_data = {
        "ci_log": """Polyspace Bug Finder Analysis Results:
Rule 8.5: MISRA-C violation detected
File: src/can_handler.c, Line 123
Variable 'can_message' has external linkage but no definition
Polyspace: Static analysis failed
ISO 26262 compliance check failed""",
        "repository": "automotive-compliance",
        "job_name": "POLYSPACE-CHECK",
        "build_number": 789
    }
    
    try:
        response = requests.post(f"{BASE_URL}/analyze", json=test_data, timeout=60)
        print(f"✅ Status: {response.status_code}")
        
        result = response.json()
        print(f"   오류 타입: {result.get('error_type')}")
        print(f"   신뢰도: {result.get('confidence')}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("\n" + "🧪" * 30)
    print("   CI 오류 분석 에이전트 - 전체 기능 테스트")
    print("🧪" * 30)
    
    results = {}
    
    # 테스트 실행
    results['health'] = test_health()
    time.sleep(1)
    
    results['analyze'] = test_analyze()
    time.sleep(1)
    
    results['kb_list'] = test_kb_list()
    time.sleep(1)
    
    results['nxp'] = test_nxp_error()
    time.sleep(1)
    
    results['polyspace'] = test_polyspace_error()
    
    # 결과 요약
    print_section("테스트 결과 요약")
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name:15s}: {status}")
    
    print(f"\n   총 {total}개 테스트 중 {passed}개 통과")
    
    if passed == total:
        print("\n🎉 모든 테스트 통과! 🎉")
    else:
        print(f"\n⚠️  {total - passed}개 테스트 실패")
    
    # 결과 파일 저장
    with open("test_results.json", "w", encoding="utf-8") as f:
        json.dump({
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "details": results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 결과가 test_results.json에 저장되었습니다.")

if __name__ == "__main__":
    main()
