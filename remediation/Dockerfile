FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY operator.py .

RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup appuser

USER appuser

CMD ["python", "operator.py"]