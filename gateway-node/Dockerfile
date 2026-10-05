FROM oven/bun:1.4.2 AS dependencies

WORKDIR /app
COPY package.json bun.lock ./
RUN bun install --frozen-lockfile

FROM oven/bun:1.4.2 AS build

WORKDIR /app
COPY --from=dependencies /app/node_modules ./node_modules
COPY package.json bun.lock ./
COPY src ./src
COPY tests ./tests
COPY tsconfig.json ./

RUN bun run build

FROM oven/bun:1.4.2 AS runtime

WORKDIR /app
COPY --from=dependencies /app/node_modules ./node_modules
COPY package.json bun.lock ./
COPY --from=build /app/src ./src
COPY tsconfig.json ./

ENV GATEWAY_HOST=0.0.0.0 \
    GATEWAY_PORT=8080 \
    ENGINE_HOST=engine \
    ENGINE_PORT=9000 \
    ANALYTICS_HOST=analytics \
    ANALYTICS_PORT=8000 \
    RATE_LIMIT_ENABLED=true \
    AUTH_ENABLED=false \
    AUTH_ENFORCEMENT_ENABLED=false

EXPOSE 8080

HEALTHCHECK --interval=5s --timeout=5s --start-period=10s --retries=20 \
    CMD bun -e "fetch('http://127.0.0.1:8080/api/health').then(r => { if (!r.ok) process.exit(1) }).catch(() => process.exit(1))"

CMD ["bun", "src/server.ts"]
