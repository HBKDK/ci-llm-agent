"""
서버 시작 스크립트 (오류 메시지 확인용)
"""
import os
import sys

# 환경변수 설정
os.environ["USE_SQLITE"] = "true"
os.environ["LLM_PROVIDER"] = ""  # LLM 비활성화 (fallback 사용)
os.environ["PRIVATE_LLM_BASE_URL"] = ""
os.environ["SEARCH_ENGINE"] = "none"
os.environ["JWT_SECRET_KEY"] = "test-secret-key"
os.environ["BASE_URL"] = "http://localhost:8000"

print("=" * 60)
print("Starting server...")
print("=" * 60)

try:
    # Import 테스트
    print("\n1. Testing imports...")
    from app.main_simple import app
    print("   ✅ FastAPI app imported")
    
    from app.db.connection import init_db
    print("   ✅ DB connection imported")
    
    # DB 초기화
    print("\n2. Initializing database...")
    init_db()
    print("   ✅ Database initialized")
    
    # 서버 시작
    print("\n3. Starting uvicorn server...")
    print("   URL: http://localhost:8000")
    print("   Docs: http://localhost:8000/docs")
    print("   Stop: Ctrl+C")
    print("=" * 60)
    print()
    
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000, 
        log_level="info",
        access_log=True,
        log_config={
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
                "file": {
                    "formatter": "default",
                    "class": "logging.FileHandler",
                    "filename": "server.log",
                },
            },
            "root": {
                "level": "INFO",
                "handlers": ["default", "file"],
            },
        }
    )
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
