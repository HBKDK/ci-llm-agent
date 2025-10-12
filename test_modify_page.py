"""
수정 페이지 테스트
"""
import requests
import json
import webbrowser

BASE_URL = "http://localhost:8000"

print("=" * 60)
print("수정 페이지 테스트")
print("=" * 60)

# 1. 분석 요청
print("\n[1/3] 분석 요청 중...")
analyze_data = {
    "ci_log": """Tasking Compiler Error: code generation failed
main.c(45): error: insufficient memory for code generation
main.c(50): warning: variable 'buffer' may be uninitialized
Tasking IDE: Build failed with exit code 1""",
    "repository": "automotive-ecu",
    "job_name": "BUILD-TEST",
    "build_number": 123
}

try:
    response = requests.post(f"{BASE_URL}/analyze", json=analyze_data, timeout=30)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ 분석 완료!")
        print(f"   분석 ID: {result.get('analysis_id')}")
        print(f"   오류 타입: {result.get('error_type')}")
        
        # 2. URL 확인
        print("\n[2/3] 승인 URL:")
        approval_url = result.get('approval_url', '')
        modify_url = result.get('modify_url', '')
        
        print(f"   ✅ 바로 저장: {approval_url}")
        print(f"   ✏️  수정 후 저장: {modify_url}")
        
        # 3. 수정 페이지 열기
        print("\n[3/3] 수정 페이지 열기...")
        if modify_url:
            print(f"\n브라우저에서 수정 페이지를 엽니다:")
            print(f"   {modify_url}")
            
            # 결과 저장
            with open("modify_page_url.txt", "w", encoding="utf-8") as f:
                f.write(f"수정 페이지 URL:\n{modify_url}\n\n")
                f.write(f"승인 페이지 URL:\n{approval_url}\n\n")
                f.write(f"\n분석 결과:\n")
                f.write(json.dumps(result, indent=2, ensure_ascii=False))
            
            print(f"\n✅ modify_page_url.txt에 저장되었습니다.")
            print(f"\n브라우저를 자동으로 열까요? (y/n)")
            
            # 자동으로 브라우저 열기
            try:
                webbrowser.open(modify_url)
                print("✅ 브라우저에서 수정 페이지가 열렸습니다!")
                print("\n수정 페이지에서:")
                print("  1. 제목, 요약, 해결방법, 태그를 수정하세요")
                print("  2. '💾 수정 후 KB에 저장' 버튼을 클릭하세요")
                print("  3. 자동으로 KB에 저장됩니다!")
            except Exception as e:
                print(f"⚠️  브라우저를 자동으로 열 수 없습니다: {e}")
                print(f"\n수동으로 브라우저에서 다음 URL을 열어주세요:")
                print(f"   {modify_url}")
        else:
            print("❌ modify_url이 없습니다.")
    else:
        print(f"❌ 분석 실패: {response.status_code}")
        print(f"   {response.text}")
        
except Exception as e:
    print(f"❌ 오류: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
