# Build from repository root:
#   docker build --platform linux/amd64 -f backend/Dockerfile -t capstone-api .
FROM python:3.12-slim-bookworm

WORKDIR /app

RUN apt-get -o Acquire::Retries=5 update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend /app/backend

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

EXPOSE 8080
ENV PORT=8080

CMD ["sh", "-c", "exec uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
