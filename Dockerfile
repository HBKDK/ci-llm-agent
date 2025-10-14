FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성 설치 (PostgreSQL 클라이언트만)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY app/ ./app/
COPY data/ ./data/

# 데이터 디렉토리 생성
RUN mkdir -p /app/data

# 환경변수 설정
ENV PYTHONUNBUFFERED=1
ENV SEARCH_ENGINE=auto
ENV USE_SQLITE=false

# 포트 노출
EXPOSE 8000

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/')"

# 애플리케이션 실행
CMD ["uvicorn", "app.main_simple:app", "--host", "0.0.0.0", "--port", "8000"]

