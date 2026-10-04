FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN python -m pip install --no-cache-dir .
ENV ANALYTICS_GATEWAY_HOST=gateway ANALYTICS_GATEWAY_PORT=8000 TRADING_ENGINE_METRICS_HOST=0.0.0.0 TRADING_ENGINE_METRICS_PORT=9101 TRADING_ENGINE_DATABASE_URL=postgresql://trading_engine:trading_engine@postgres:5432/trading_engine
EXPOSE 8000 9101
CMD ["python", "-m", "analytics.main"]
