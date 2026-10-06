FROM oven/bun:1.4.2 AS build

WORKDIR /app

COPY package.json ./
RUN bun install

COPY . .

RUN bun run build

FROM nginx:1.27-alpine AS runtime

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=10s --timeout=5s --start-period=5s --retries=10 \
    CMD wget --spider --quiet http://127.0.0.1/ || exit 1
