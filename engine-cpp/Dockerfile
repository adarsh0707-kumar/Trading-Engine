FROM debian:bookworm-slim AS build

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src
COPY . .

RUN cmake -S . -B build \
        -DCMAKE_BUILD_TYPE=Release \
        -DENABLE_NETWORKING=ON \
    && cmake --build build --parallel --target engine

FROM debian:bookworm-slim AS runtime

RUN apt-get update \
    && apt-get install -y --no-install-recommends netcat-openbsd \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --system --create-home --uid 10001 engine \
    && mkdir -p /var/lib/trading-engine \
    && chown engine:engine /var/lib/trading-engine

WORKDIR /app
COPY --from=build --chown=engine:engine /src/build/engine /app/engine

ENV ENGINE_BIND_ADDRESS=0.0.0.0
EXPOSE 9000

USER engine
ENTRYPOINT ["/app/engine"]
