FROM debian:bookworm-slim AS build

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential cmake \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src
COPY . .

RUN cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DENABLE_NETWORKING=ON \
    && cmake --build build -j"$(nproc)" --target engine

FROM debian:bookworm-slim
WORKDIR /app
COPY --from=build /src/build/engine /app/engine
ENV ENGINE_BIND_ADDRESS=0.0.0.0
EXPOSE 9000
ENTRYPOINT ["/app/engine"]
