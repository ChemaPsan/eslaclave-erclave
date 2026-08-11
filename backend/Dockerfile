FROM python:3.13-slim

ARG ERCLAVE_SERVICE_ADAPTER=admin_service_adapter

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/shared
ENV ERCLAVE_SERVICE_ADAPTER=${ERCLAVE_SERVICE_ADAPTER}

WORKDIR /app

COPY pyproject.toml ./
COPY alembic.ini ./
COPY alembic ./alembic
COPY shared ./shared
COPY services ./services

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

CMD python -m uvicorn services.${ERCLAVE_SERVICE_ADAPTER}:app --host 0.0.0.0 --port ${PORT:-8080}
