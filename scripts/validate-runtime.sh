#!/usr/bin/env bash
set -Eeuo pipefail

# Read-only smoke checks for an already-running local Docker Compose stack.
# This script never starts/stops containers, generates orders, resets risk state,
# or changes persisted data.

GATEWAY_URL="${GATEWAY_URL:-http://127.0.0.1:8080}"
DASHBOARD_URL="${DASHBOARD_URL:-http://127.0.0.1:5173}"
ANALYTICS_METRICS_URL="${ANALYTICS_METRICS_URL:-http://127.0.0.1:9101/metrics}"

command -v python3 >/dev/null || { echo "ERROR: python3 is required" >&2; exit 2; }
command -v docker >/dev/null || { echo "ERROR: docker is required" >&2; exit 2; }

echo "Runtime smoke validation (read-only)"
echo "Gateway: $GATEWAY_URL"
echo "Dashboard: $DASHBOARD_URL"
echo "Analytics metrics: $ANALYTICS_METRICS_URL"
echo

GATEWAY_URL="$GATEWAY_URL" DASHBOARD_URL="$DASHBOARD_URL" ANALYTICS_METRICS_URL="$ANALYTICS_METRICS_URL" python3 - <<'PY'
import json
import os
import sys
import urllib.error
import urllib.request

gateway = os.environ["GATEWAY_URL"].rstrip("/")
dashboard = os.environ["DASHBOARD_URL"].rstrip("/")
metrics = os.environ["ANALYTICS_METRICS_URL"]

checks = [
    ("Gateway health", gateway + "/api/health", "json"),
    ("Gateway readiness", gateway + "/api/ready", "json"),
    ("Market REST snapshot", gateway + "/api/v1/market", "json"),
    ("Recent trades REST snapshot", gateway + "/api/v1/trades", "json"),
    ("Dashboard HTTP", dashboard + "/", "html"),
    ("Analytics Prometheus metrics", metrics, "metrics"),
]

failed = 0
for label, url, expected in checks:
    try:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "trading-engine-runtime-smoke/1.0"},
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            body = response.read()
            if not 200 <= response.status < 300:
                raise RuntimeError(f"unexpected HTTP {response.status}")
            if expected == "json":
                value = json.loads(body)
                if not isinstance(value, (dict, list)):
                    raise RuntimeError("JSON response must be an object or array")
                detail = f"HTTP {response.status}, valid JSON"
                if label == "Gateway readiness":
                    detail += f": {json.dumps(value, separators=(',', ':'))}"
            elif expected == "html":
                if not body.strip():
                    raise RuntimeError("empty response body")
                detail = f"HTTP {response.status}, {len(body)} bytes"
            else:
                if not body.strip():
                    raise RuntimeError("empty metrics response")
                detail = f"HTTP {response.status}, {len(body)} bytes"
            print(f"PASS  {label}: {detail}")
    except (urllib.error.URLError, TimeoutError, ValueError, RuntimeError) as exc:
        failed += 1
        print(f"FAIL  {label}: {exc}", file=sys.stderr)

if failed:
    print(f"\n{failed} HTTP check(s) failed.", file=sys.stderr)
    sys.exit(1)

print("\nAll HTTP smoke checks passed.")
PY

echo
echo "Checking PostgreSQL readiness and a read-only query..."
docker compose exec -T postgres pg_isready -U trading_engine -d trading_engine
docker compose exec -T postgres psql -v ON_ERROR_STOP=1 -U trading_engine -d trading_engine -tAc 'SELECT 1;' | grep -qx '1'
echo "PASS  PostgreSQL accepts connections and SELECT 1 returns 1."
echo
echo "PASS  Runtime smoke validation complete."
echo "Note: this checks service reachability/contracts, not a new trade, risk event, or browser-level recovery."
