FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/shared
ENV ERCLAVE_SERVICE_ADAPTER=admin_service_adapter

WORKDIR /app

COPY pyproject.toml ./
COPY shared ./shared
COPY services ./services

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

CMD python -m uvicorn services.${ERCLAVE_SERVICE_ADAPTER}:app --host 0.0.0.0 --port ${PORT:-8080}
