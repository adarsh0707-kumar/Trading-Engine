FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src

RUN python -m pip install --no-cache-dir .

ENV ANALYTICS_GATEWAY_HOST=0.0.0.0 \
    ANALYTICS_GATEWAY_PORT=8000 \
    TRADING_ENGINE_METRICS_HOST=0.0.0.0 \
    TRADING_ENGINE_METRICS_PORT=9101 \
    TRADING_ENGINE_DATABASE_URL=postgresql://trading_engine:trading_engine@postgres:5432/trading_engine

EXPOSE 8000 9101

HEALTHCHECK --interval=5s --timeout=3s --start-period=10s --retries=20 \
    CMD python -c "import socket; socket.create_connection(('127.0.0.1', 8000), 2).close()"

CMD ["python", "-m", "analytics.main"]
