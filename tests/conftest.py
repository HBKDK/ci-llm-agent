"""
Pytest 설정 및 공통 fixtures
"""
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.models import Base

# 테스트용 환경변수 설정
os.environ["USE_SQLITE"] = "true"
os.environ["LLM_PROVIDER"] = "private"
os.environ["PRIVATE_LLM_BASE_URL"] = ""
os.environ["SEARCH_ENGINE"] = "none"
os.environ["JWT_SECRET_KEY"] = "test-secret-key"
os.environ["BASE_URL"] = "http://localhost:8000"


@pytest.fixture(scope="session")
def test_db():
    """테스트용 DB 세션"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture
def sample_ci_log():
    """테스트용 CI 로그"""
    return """
Tasking C166 Compiler Error:
main.c(45): error: code generation failed
main.c(45): error: insufficient memory for code generation
Tasking IDE: Build failed with exit code 1
Compiler options: -O2 -W1
"""


@pytest.fixture
def sample_nxp_log():
    """NXP 테스트 로그"""
    return """
NXP S32K144: compilation error
undefined reference to `GPIO_Init'
undefined reference to `ADC_Config'
S32K SDK library not linked
linking failed with exit code 1
"""


@pytest.fixture
def sample_polyspace_log():
    """Polyspace 테스트 로그"""
    return """
Polyspace Bug Finder Analysis Results:
Rule 8.5: MISRA-C violation detected
File: src/can_handler.c, Line 123
Variable 'can_message' has external linkage but no definition
Polyspace: Static analysis failed
ISO 26262 compliance check failed
"""
