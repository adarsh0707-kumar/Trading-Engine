import json
from pathlib import Path


DASHBOARD = (
    Path(__file__).parents[4]
    / "infra"
    / "grafana"
    / "dashboards"
    / "trading-engine-overview.json"
)


def test_grafana_dashboard_is_valid_json():
    dashboard = json.loads(DASHBOARD.read_text(encoding="utf-8"))

    assert dashboard["title"] == "Trading Engine — Analytics Overview"
    assert dashboard["refresh"] == "5s"


def test_grafana_dashboard_contains_core_observability_panels():
    dashboard = json.loads(DASHBOARD.read_text(encoding="utf-8"))
    titles = {panel["title"] for panel in dashboard["panels"]}

    assert {
        "Trades / sec",
        "Processing latency",
        "Portfolio equity",
        "Drawdown",
        "Position",
        "Errors by type",
        "Persistence operations",
        "Risk events",
        "PostgreSQL health",
    } <= titles
