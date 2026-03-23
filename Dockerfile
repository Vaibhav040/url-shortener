# ------- Stage 1: Builder -------
FROM python:3.12-slim AS builder

WORKDIR /build

COPY app/requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

# ------- Stage 2: Runtime -------

FROM python:3.12-slim AS runtime

WORKDIR /app

RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup appuser

COPY --from=builder /install /ust/local
COPY app/ .

RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn","main:app", "--host", "0.0.0.0", "--port", "8000"]