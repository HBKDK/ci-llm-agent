"""
PostgreSQL 데이터베이스 모델
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class KnowledgeBase(Base):
    """지식베이스 테이블"""
    __tablename__ = "knowledge_base"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(512), nullable=False, index=True)
    summary = Column(Text, nullable=False)
    fix = Column(Text, nullable=False)
    tags = Column(String(512), nullable=True, index=True)
    error_type = Column(String(50), nullable=True, index=True)
    
    # 메타데이터
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100), nullable=True)
    is_approved = Column(Boolean, default=False)
    auto_learned = Column(Boolean, default=False)
    
    # 사용 통계
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime, nullable=True)
    
    # 관계
    analysis_history = relationship("AnalysisHistory", back_populates="kb_entry")


class AnalysisHistory(Base):
    """분석 이력 테이블"""
    __tablename__ = "analysis_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ci_log = Column(Text, nullable=False)
    context = Column(Text, nullable=True)
    repository = Column(String(200), nullable=True)
    
    # 분석 결과
    error_type = Column(String(50), nullable=True, index=True)
    symptoms = Column(Text, nullable=True)  # JSON 형태
    analysis = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    kb_confidence = Column(Float, nullable=True)
    security_status = Column(String(50), nullable=True)
    
    # KB 연결
    kb_entry_id = Column(Integer, ForeignKey("knowledge_base.id"), nullable=True)
    kb_entry = relationship("KnowledgeBase", back_populates="analysis_history")
    
    # 메타데이터
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    job_name = Column(String(200), nullable=True)
    build_number = Column(Integer, nullable=True)
    
    # 이메일 전송 여부
    email_sent = Column(Boolean, default=False)
    email_sent_at = Column(DateTime, nullable=True)


class PendingApproval(Base):
    """승인 대기 테이블"""
    __tablename__ = "pending_approvals"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 분석 이력 연결
    analysis_id = Column(Integer, ForeignKey("analysis_history.id"), nullable=False)
    
    # KB 항목 정보
    title = Column(String(512), nullable=False)
    summary = Column(Text, nullable=False)
    fix = Column(Text, nullable=False)
    tags = Column(String(512), nullable=True)
    error_type = Column(String(50), nullable=True)
    
    # 승인 정보
    token = Column(String(500), unique=True, nullable=False, index=True)
    token_expires_at = Column(DateTime, nullable=False)
    
    approved_by = Column(String(100), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    approval_status = Column(String(20), default="pending")  # pending, approved, rejected, expired
    
    # 수정 내용 (승인자가 수정할 수 있음)
    modified_title = Column(String(512), nullable=True)
    modified_summary = Column(Text, nullable=True)
    modified_fix = Column(Text, nullable=True)
    modified_tags = Column(String(512), nullable=True)
    
    # 메타데이터
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 이메일 정보
    recipient_email = Column(String(200), nullable=True)
    admin_email = Column(String(200), nullable=True)

