# 1. 가벼운 파이썬 3.10 이미지 사용
FROM python:3.10-slim

# 2. 컨테이너 내부 작업 디렉토리 설정
WORKDIR /app

# 3. 라이브러리 설치 (캐시 최적화를 위해 복사 먼저 수행)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 소스 코드 전체 복사
COPY . .

# 5. FastAPI 실행 (포트 8000)
# --host 0.0.0.0은 외부 접속을 허용하기 위해 필수입니다.
CMD ["uvicorn", "streaming_server:app", "--host", "0.0.0.0", "--port", "8000"]
