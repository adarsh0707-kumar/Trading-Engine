FROM oven/bun:1.4.2
WORKDIR /app
COPY package.json bun.lock ./
RUN bun install --frozen-lockfile
COPY . .
RUN bun run build
ENV GATEWAY_HOST=0.0.0.0 GATEWAY_PORT=8080 ENGINE_HOST=engine ENGINE_PORT=9000 ANALYTICS_HOST=analytics ANALYTICS_PORT=8000 RATE_LIMIT_ENABLED=true AUTH_ENABLED=false AUTH_ENFORCEMENT_ENABLED=false
EXPOSE 8080
CMD ["bun", "src/server.ts"]
