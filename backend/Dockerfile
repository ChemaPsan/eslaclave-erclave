FROM python:3.13-slim

ARG ERCLAVE_SERVICE_ADAPTER=admin_service_adapter

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/shared
ENV ERCLAVE_SERVICE_ADAPTER=${ERCLAVE_SERVICE_ADAPTER}

WORKDIR /app

COPY backend/pyproject.toml ./
COPY backend/alembic.ini ./
COPY backend/alembic ./alembic
COPY backend/shared ./shared
COPY backend/services ./services
COPY backend/scripts ./scripts
COPY contracts ./contracts

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

CMD python -m uvicorn services.${ERCLAVE_SERVICE_ADAPTER}:app --host 0.0.0.0 --port ${PORT:-8080}
