"""
간소화된 FastAPI - CI 시스템에서 REST API로만 사용
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import json
import os

from app.db.connection import get_db, init_db
from app.db.models import AnalysisHistory, PendingApproval, KnowledgeBase
from app.auth.jwt_handler import create_approval_token, verify_approval_token
from app.graph.workflow import CIErrorAnalyzer
from app.services.n8n_client import n8n_client
from app.utils.text import extract_symptoms
from app.kb.db import search_kb

app = FastAPI(
    title="CI Error Analysis Agent",
    version="2.0.0",
    description="자동차 SW CI 오류 분석 에이전트"
)


class AnalyzeRequest(BaseModel):
    """분석 요청"""
    ci_log: str
    context: Optional[str] = None
    repository: Optional[str] = None
    job_name: Optional[str] = None
    build_number: Optional[int] = None


class AnalyzeResponse(BaseModel):
    """분석 응답 (CI 시스템에서 사용)"""
    analysis_id: int
    error_type: str
    confidence: float
    kb_confidence: float
    security_status: str
    symptoms: list
    analysis: str
    
    # 승인 토큰 (이메일에 포함시킬 용도)
    approval_token: Optional[str] = None
    approval_url: Optional[str] = None
    modify_token: Optional[str] = None
    modify_url: Optional[str] = None
    
    # KB 저장 추천 여부
    recommend_save: bool = False


@app.on_event("startup")
async def startup_event():
    """시작 시 DB 초기화"""
    init_db()
    print("✅ 데이터베이스 초기화 완료")


@app.get("/")
async def root():
    """헬스 체크"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "mode": "rest-api-only"
    }


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_ci_error(
    request: AnalyzeRequest,
    db: Session = Depends(get_db)
):
    """
    CI 오류 분석 (KB 우선, 필요시 n8n LLM 호출)
    
    CI 시스템에서 호출:
    1. 증상 추출 및 KB 검색
    2. KB 신뢰도 < 0.8이면 n8n LLM 분석 호출
    3. 분석 결과 반환 (approval_token 포함)
    """
    # 1. 증상 추출
    analyzer = CIErrorAnalyzer()
    symptoms = extract_symptoms(request.ci_log)
    error_type = analyzer._classify_error_type(symptoms)
    
    # 2. KB 검색
    query = "\n".join(symptoms)
    kb_hits = search_kb(query=query, top_k=5)
    kb_confidence = analyzer._calculate_kb_confidence(kb_hits)
    
    # 3. KB 결과 또는 n8n LLM 분석
    if kb_confidence >= 0.8:
        # KB에서 충분한 답을 찾음
        best_hit = kb_hits[0]
        analysis = f"""KB에서 유사한 사례를 찾았습니다:

**문제 유형**: {best_hit['title']}
**해결 방법**: {best_hit['fix']}

추가 참고사항:
{best_hit['summary']}

이 해결책을 적용해보시고, 문제가 지속되면 추가 로그를 제공해주세요."""
        
        result = {
            "symptoms": symptoms,
            "kb_hits": kb_hits,
            "web_hits": [],
            "security_status": "kb_analyzed",
            "kb_confidence": kb_confidence,
            "analysis": analysis,
            "confidence": kb_confidence,
            "error_type": error_type
        }
    else:
        # KB에서 답을 찾지 못함 - n8n LLM 분석 호출
        try:
            n8n_result = await n8n_client.call_llm_analysis(
                ci_log=request.ci_log,
                symptoms=symptoms,
                error_type=error_type,
                context=request.context,
                repository=request.repository
            )
            
            result = {
                "symptoms": symptoms,
                "kb_hits": kb_hits,
                "web_hits": [],
                "security_status": "llm_analyzed",
                "kb_confidence": kb_confidence,
                "analysis": n8n_result["analysis"],
                "confidence": n8n_result["confidence"],
                "error_type": error_type
            }
            
        except HTTPException as e:
            # n8n 호출 실패 - fallback 분석
            analysis = f"""KB에서 해당 오류에 대한 해결책을 찾지 못했고, LLM 분석도 실패했습니다.

**추출된 증상**:
{chr(10).join(f"- {symptom}" for symptom in symptoms[:5])}

**오류 유형**: {error_type}

**오류**: {e.detail}

개발팀에 문의하거나 추가 컨텍스트를 제공해주세요."""
            
            result = {
                "symptoms": symptoms,
                "kb_hits": kb_hits,
                "web_hits": [],
                "security_status": "analysis_failed",
                "kb_confidence": kb_confidence,
                "analysis": analysis,
                "confidence": 0.1,
                "error_type": error_type
            }
    
    # 4. 분석 이력 DB 저장
    analysis_history = AnalysisHistory(
        ci_log=request.ci_log,
        context=request.context,
        repository=request.repository,
        job_name=request.job_name,
        build_number=request.build_number,
        error_type=result["error_type"],
        symptoms=json.dumps(result["symptoms"], ensure_ascii=False),
        analysis=result["analysis"],
        confidence=result["confidence"],
        kb_confidence=result["kb_confidence"],
        security_status=result["security_status"]
    )
    db.add(analysis_history)
    db.commit()
    db.refresh(analysis_history)
    
    # 5. 승인 토큰 생성 (신뢰도 0.6 이상일 때만)
    approval_token = None
    approval_url = None
    modify_token = None
    modify_url = None
    recommend_save = False
    
    if result["confidence"] >= 0.6:
        # 승인 대기 항목 생성
        pending = PendingApproval(
            analysis_id=analysis_history.id,
            title=f"{result['error_type'].upper()}: {result['symptoms'][0] if result['symptoms'] else 'Unknown'}",
            summary="\n".join(result['symptoms'][:3]) if result['symptoms'] else request.ci_log[:200],
            fix=result['analysis'],
            tags=result['error_type'],
            error_type=result['error_type'],
            token="",  # 임시
            token_expires_at=datetime.utcnow() + timedelta(days=7)
        )
        db.add(pending)
        db.flush()
        
        # JWT 토큰 생성
        approval_token = create_approval_token(
            analysis_id=analysis_history.id,
            pending_approval_id=pending.id,
            admin_email="admin"
        )
        
        modify_token = create_approval_token(
            analysis_id=analysis_history.id,
            pending_approval_id=pending.id,
            admin_email="admin"
        )
        
        pending.token = approval_token
        db.commit()
        
        # URL 생성 (CI 시스템이 이메일에 포함)
        base_url = os.getenv("BASE_URL", "http://localhost:8000")
        approval_url = f"{base_url}/approve/{approval_token}"
        modify_url = f"{base_url}/modify/{modify_token}"
        recommend_save = True
    
    # 6. 응답 반환
    return AnalyzeResponse(
        analysis_id=analysis_history.id,
        error_type=result["error_type"],
        confidence=result["confidence"],
        kb_confidence=result["kb_confidence"],
        security_status=result["security_status"],
        symptoms=result["symptoms"],
        analysis=result["analysis"],
        approval_token=approval_token,
        approval_url=approval_url,
        modify_token=modify_token,
        modify_url=modify_url,
        recommend_save=recommend_save
    )


@app.get("/approve/{token}")
async def approve_kb_save(
    token: str,
    db: Session = Depends(get_db)
):
    """
    이메일에서 승인 링크 클릭 시 호출
    KB에 저장하고 확인 페이지 표시
    """
    # 토큰 검증
    payload = verify_approval_token(token)
    
    if payload is None or "error" in payload:
        return HTMLResponse(
            content=f"<h2>❌ {payload.get('error', '유효하지 않은 토큰')}</h2>",
            status_code=400
        )
    
    # 승인 대기 항목 조회
    pending = db.query(PendingApproval).filter(
        PendingApproval.id == payload["pending_approval_id"]
    ).first()
    
    if not pending:
        raise HTTPException(status_code=404, detail="승인 대기 항목을 찾을 수 없습니다.")
    
    # 이미 처리된 경우
    if pending.approval_status != "pending":
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=f"""
        <html>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h2>ℹ️ 이미 처리된 항목입니다</h2>
            <p>상태: {pending.approval_status}</p>
            <p>처리 시간: {pending.approved_at}</p>
        </body>
        </html>
        """)
    
    # 만료 확인
    if datetime.utcnow() > pending.token_expires_at:
        pending.approval_status = "expired"
        db.commit()
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content="""
        <html>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h2>⏰ 토큰이 만료되었습니다</h2>
            <p>승인 기한이 지났습니다.</p>
        </body>
        </html>
        """, status_code=400)
    
    # KB에 저장
    kb_entry = KnowledgeBase(
        title=pending.modified_title or pending.title,
        summary=pending.modified_summary or pending.summary,
        fix=pending.modified_fix or pending.fix,
        tags=pending.modified_tags or pending.tags,
        error_type=pending.error_type,
        created_by=payload.get("admin_email", "admin"),
        is_approved=True,
        auto_learned=True
    )
    db.add(kb_entry)
    
    # 승인 상태 업데이트
    pending.approval_status = "approved"
    pending.approved_by = payload.get("admin_email", "admin")
    pending.approved_at = datetime.utcnow()
    
    db.commit()
    db.refresh(kb_entry)
    
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial; text-align: center; padding: 50px; background: #f5f5f5; }}
            .container {{ background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 600px; margin: 0 auto; }}
            h1 {{ color: #4caf50; }}
            .info {{ background: #e8f5e9; padding: 20px; border-radius: 5px; margin: 20px 0; }}
            .detail {{ text-align: left; margin: 10px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>✅ KB에 저장 완료!</h1>
            <div class="info">
                <h2>{kb_entry.title}</h2>
                <div class="detail">
                    <strong>KB ID:</strong> {kb_entry.id}<br>
                    <strong>오류 타입:</strong> {kb_entry.error_type}<br>
                    <strong>승인자:</strong> {pending.approved_by}<br>
                    <strong>승인 시간:</strong> {pending.approved_at.strftime("%Y-%m-%d %H:%M:%S")}
                </div>
            </div>
            <p>이제 다른 개발자들도 이 해결책을 활용할 수 있습니다.</p>
            <p style="color: #666; font-size: 12px;">이 창을 닫아도 됩니다.</p>
        </div>
    </body>
    </html>
    """)


@app.get("/modify/{token}")
async def modify_before_approve(
    token: str,
    db: Session = Depends(get_db)
):
    """
    수정 페이지 표시 (이메일에서 수정 링크 클릭 시)
    """
    payload = verify_approval_token(token)
    
    if payload is None or "error" in payload:
        from fastapi.responses import HTMLResponse
        return HTMLResponse(
            content=f"<h2>❌ {payload.get('error', '유효하지 않은 토큰')}</h2>",
            status_code=400
        )
    
    pending = db.query(PendingApproval).filter(
        PendingApproval.id == payload["pending_approval_id"]
    ).first()
    
    if not pending:
        raise HTTPException(status_code=404, detail="승인 대기 항목을 찾을 수 없습니다.")
    
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial; max-width: 900px; margin: 30px auto; padding: 20px; background: #f5f5f5; }}
            .container {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #1976d2; }}
            .form-group {{ margin: 20px 0; }}
            label {{ display: block; font-weight: bold; margin-bottom: 8px; color: #555; }}
            input, textarea {{ width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 5px; font-size: 14px; }}
            textarea {{ min-height: 150px; font-family: monospace; }}
            .btn {{ background: #4caf50; color: white; padding: 14px 28px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; margin-top: 20px; }}
            .btn:hover {{ background: #45a049; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>✏️ KB 항목 수정</h1>
            <p>내용을 수정한 후 저장하면 KB에 반영됩니다.</p>
            
            <form id="modifyForm">
                <div class="form-group">
                    <label>제목:</label>
                    <input type="text" id="title" value="{pending.title}" />
                </div>
                
                <div class="form-group">
                    <label>요약 (증상 설명):</label>
                    <textarea id="summary">{pending.summary}</textarea>
                </div>
                
                <div class="form-group">
                    <label>해결 방법:</label>
                    <textarea id="fix">{pending.fix}</textarea>
                </div>
                
                <div class="form-group">
                    <label>태그 (쉼표로 구분):</label>
                    <input type="text" id="tags" value="{pending.tags}" />
                </div>
                
                <button type="button" class="btn" onclick="submitAndApprove()">💾 수정 후 KB에 저장</button>
            </form>
        </div>
        
        <script>
            async function submitAndApprove() {{
                const data = {{
                    title: document.getElementById('title').value,
                    summary: document.getElementById('summary').value,
                    fix: document.getElementById('fix').value,
                    tags: document.getElementById('tags').value
                }};
                
                // 1. 수정 내용 저장
                const modifyResponse = await fetch('/api/modify/{token}', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify(data)
                }});
                
                if (!modifyResponse.ok) {{
                    alert('수정 저장 실패');
                    return;
                }}
                
                // 2. 승인 (자동으로 KB에 저장)
                window.location.href = '/approve/{token}';
            }}
        </script>
    </body>
    </html>
    """)


@app.post("/api/modify/{token}")
async def save_modification(
    token: str,
    modification: dict,
    db: Session = Depends(get_db)
):
    """수정 내용 저장 (내부 API)"""
    payload = verify_approval_token(token)
    
    if payload is None or "error" in payload:
        raise HTTPException(status_code=400, detail="유효하지 않은 토큰")
    
    pending = db.query(PendingApproval).filter(
        PendingApproval.id == payload["pending_approval_id"]
    ).first()
    
    if not pending:
        raise HTTPException(status_code=404, detail="승인 대기 항목을 찾을 수 없습니다.")
    
    # 수정 내용 저장
    pending.modified_title = modification.get("title")
    pending.modified_summary = modification.get("summary")
    pending.modified_fix = modification.get("fix")
    pending.modified_tags = modification.get("tags")
    
    db.commit()
    
    return {"status": "success", "message": "수정 내용 저장 완료"}


@app.get("/kb/list")
async def list_kb(
    skip: int = 0,
    limit: int = 100,
    error_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """KB 목록 조회"""
    query = db.query(KnowledgeBase).filter(KnowledgeBase.is_approved == True)
    
    if error_type:
        query = query.filter(KnowledgeBase.error_type == error_type)
    
    total = query.count()
    entries = query.order_by(KnowledgeBase.created_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "entries": [
            {
                "id": e.id,
                "title": e.title,
                "summary": e.summary,
                "fix": e.fix,
                "tags": e.tags,
                "error_type": e.error_type,
                "created_at": e.created_at.isoformat(),
                "usage_count": e.usage_count
            }
            for e in entries
        ]
    }


@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """상세 헬스 체크"""
    try:
        kb_count = db.query(KnowledgeBase).count()
        analysis_count = db.query(AnalysisHistory).count()
        pending_count = db.query(PendingApproval).filter(
            PendingApproval.approval_status == "pending"
        ).count()
        
        return {
            "status": "healthy",
            "database": "connected",
            "kb_entries": kb_count,
            "analysis_history": analysis_count,
            "pending_approvals": pending_count
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


