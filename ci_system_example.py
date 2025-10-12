#!/usr/bin/env python3
"""
CI 시스템에서 사용할 예시 코드
(Bamboo, Jenkins 등 어떤 CI든 사용 가능)
"""
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Optional


class CIErrorAnalyzer:
    """CI 시스템에서 사용하는 에이전트 클라이언트"""
    
    def __init__(
        self,
        agent_url: str = "http://ci-error-agent-service:8000",
        smtp_host: str = "smtp.gmail.com",
        smtp_port: int = 587,
        smtp_user: str = "",
        smtp_password: str = ""
    ):
        self.agent_url = agent_url
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
    
    def analyze_error(
        self,
        ci_log: str,
        context: Optional[str] = None,
        repository: Optional[str] = None,
        job_name: Optional[str] = None,
        build_number: Optional[int] = None
    ) -> Dict:
        """
        CI 오류 분석 요청
        
        Returns:
            Dict: {
                "analysis_id": int,
                "error_type": str,
                "confidence": float,
                "analysis": str,
                "approval_token": str,  # 이메일에 포함할 토큰
                "approval_url": str,    # 승인 링크
                "modify_url": str,      # 수정 링크
                "recommend_save": bool  # KB 저장 추천 여부
            }
        """
        url = f"{self.agent_url}/analyze"
        
        payload = {
            "ci_log": ci_log,
            "context": context,
            "repository": repository,
            "job_name": job_name,
            "build_number": build_number
        }
        
        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            return response.json()
        
        except Exception as e:
            print(f"분석 요청 실패: {e}")
            return None
    
    def send_error_email(
        self,
        analysis_result: Dict,
        developer_email: str,
        admin_email: str
    ):
        """
        오류 분석 결과 이메일 전송 (CI 시스템에서 실행)
        """
        # 이메일 제목
        subject = f"[CI 오류] {analysis_result['error_type'].upper()} - {analysis_result.get('repository', 'Unknown')}"
        
        # 이메일 본문 (HTML)
        html_content = f"""
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #1976d2; color: white; padding: 20px; border-radius: 5px; }}
                .content {{ background: #f5f5f5; padding: 20px; margin: 20px 0; border-radius: 5px; }}
                .error-type {{ background: #ff9800; color: white; padding: 5px 10px; border-radius: 3px; }}
                .confidence {{ background: #4caf50; color: white; padding: 5px 10px; border-radius: 3px; }}
                .btn {{ display: inline-block; padding: 14px 28px; margin: 10px 5px; text-decoration: none; border-radius: 5px; font-weight: bold; color: white; }}
                .btn-approve {{ background: #4caf50; }}
                .btn-modify {{ background: #ff9800; }}
                .analysis {{ background: white; padding: 20px; border-left: 4px solid #2196f3; white-space: pre-wrap; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚗 CI 오류 분석 결과</h1>
                    <p><strong>Repository:</strong> {analysis_result.get('repository', 'Unknown')}</p>
                    <p><strong>Job:</strong> {analysis_result.get('job_name', 'N/A')} | Build #{analysis_result.get('build_number', 'N/A')}</p>
                </div>
                
                <div class="content">
                    <p>
                        <span class="error-type">{analysis_result['error_type'].upper()}</span>
                        <span class="confidence">신뢰도: {int(analysis_result['confidence'] * 100)}%</span>
                    </p>
                    
                    <h3>🔍 추출된 증상:</h3>
                    <ul>
                    {''.join(f"<li>{s}</li>" for s in analysis_result['symptoms'][:5])}
                    </ul>
                    
                    <h3>🤖 분석 결과:</h3>
                    <div class="analysis">{analysis_result['analysis'][:800]}...</div>
                </div>
        """
        
        # 승인 링크 추가 (신뢰도가 높을 때만)
        if analysis_result.get('recommend_save'):
            html_content += f"""
                <div style="text-align: center; background: #fff3e0; padding: 30px; border-radius: 5px;">
                    <h2>💡 이 분석 결과를 KB에 저장할까요?</h2>
                    <p>다른 개발자들이 동일한 오류를 더 빠르게 해결할 수 있습니다.</p>
                    
                    <a href="{analysis_result['approval_url']}" class="btn btn-approve">
                        ✅ 승인 (KB에 저장)
                    </a>
                    <a href="{analysis_result['modify_url']}" class="btn btn-modify">
                        ✏️ 수정 후 승인
                    </a>
                    
                    <p style="font-size: 12px; color: #666; margin-top: 20px;">
                        링크는 7일 후 만료됩니다.
                    </p>
                </div>
            """
        
        html_content += """
            </div>
        </body>
        </html>
        """
        
        # MIME 메시지 생성
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = self.smtp_user
        message["To"] = f"{developer_email}, {admin_email}"
        
        html_part = MIMEText(html_content, "html", "utf-8")
        message.attach(html_part)
        
        # SMTP 전송
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(message)
            
            print(f"✅ 이메일 전송 완료: {developer_email}, {admin_email}")
            return True
        
        except Exception as e:
            print(f"❌ 이메일 전송 실패: {e}")
            return False


# ==========================================
# Bamboo에서 사용할 예시 코드
# ==========================================

def bamboo_on_build_failure(log_file_path: str):
    """
    Bamboo 빌드 실패 시 호출되는 함수
    
    Bamboo Script Task에서 호출:
    python ci_system_example.py "${bamboo.buildResultKey}" "${bamboo.planRepository.repositoryUrl}"
    """
    # 로그 파일 읽기
    with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
        ci_log = f.read()
    
    # CI 메타데이터
    import os
    job_name = os.getenv("bamboo_shortJobName", "Unknown Job")
    build_number = int(os.getenv("bamboo_buildNumber", "0"))
    repository = os.getenv("bamboo_planRepository_repositoryUrl", "Unknown Repo")
    
    # 개발자 이메일 (Bamboo 변수에서)
    developer_email = os.getenv("bamboo_ManualBuildTriggerReason_userName", "developer@company.com") + "@company.com"
    admin_email = "admin@company.com"
    
    # 에이전트 초기화
    analyzer = CIErrorAnalyzer(
        agent_url="http://ci-error-agent-service:8000",
        smtp_host="smtp.company.com",
        smtp_port=587,
        smtp_user="noreply@company.com",
        smtp_password=os.getenv("SMTP_PASSWORD", "")
    )
    
    # 1. 오류 분석 요청
    print("🔍 CI 오류 분석 요청...")
    result = analyzer.analyze_error(
        ci_log=ci_log,
        context=f"Bamboo Build Failure",
        repository=repository,
        job_name=job_name,
        build_number=build_number
    )
    
    if not result:
        print("❌ 분석 실패")
        return
    
    print(f"✅ 분석 완료:")
    print(f"   분석 ID: {result['analysis_id']}")
    print(f"   오류 타입: {result['error_type']}")
    print(f"   신뢰도: {result['confidence']:.2f}")
    print(f"   KB 저장 추천: {result['recommend_save']}")
    
    # 2. 이메일 전송
    print("📧 이메일 전송 중...")
    email_sent = analyzer.send_error_email(
        analysis_result=result,
        developer_email=developer_email,
        admin_email=admin_email
    )
    
    if email_sent:
        print(f"✅ 이메일 전송 완료")
        if result['recommend_save']:
            print(f"   승인 링크: {result['approval_url']}")
            print(f"   수정 링크: {result['modify_url']}")
    
    return result


# ==========================================
# 간단한 사용 예시
# ==========================================

if __name__ == "__main__":
    """
    테스트 실행 예시
    """
    import sys
    
    # 테스트용 CI 로그
    test_log = """
Tasking C166 Compiler Error:
main.c(45): error: code generation failed
main.c(45): error: insufficient memory for code generation
Tasking IDE: Build failed with exit code 1
Compiler options: -O2 -W1
"""
    
    # 에이전트 초기화
    analyzer = CIErrorAnalyzer(
        agent_url="http://localhost:8000",  # 로컬 테스트용
        smtp_host="smtp.gmail.com",
        smtp_port=587,
        smtp_user="your-email@gmail.com",
        smtp_password="your-app-password"
    )
    
    # 분석 요청
    result = analyzer.analyze_error(
        ci_log=test_log,
        context="테스트 빌드",
        repository="automotive-ecu",
        job_name="BUILD-COMPILE",
        build_number=123
    )
    
    if result:
        print(f"\n✅ 분석 완료!")
        print(f"   오류 타입: {result['error_type']}")
        print(f"   신뢰도: {result['confidence']:.2f}")
        
        if result['recommend_save']:
            print(f"\n📧 이메일에 포함할 링크:")
            print(f"   승인: {result['approval_url']}")
            print(f"   수정: {result['modify_url']}")
            
            # 이메일 전송
            analyzer.send_error_email(
                analysis_result=result,
                developer_email="developer@company.com",
                admin_email="admin@company.com"
            )


