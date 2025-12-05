# syntax=docker/dockerfile:1.4
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 依存キャッシュを最大限活用するため requirements のみ先にコピー
COPY requirements.txt .

RUN python -m pip install --upgrade pip && \
    python -m pip install -r requirements.txt

# アプリケーション全体をコピー
COPY . .

EXPOSE 5173

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5173"]

