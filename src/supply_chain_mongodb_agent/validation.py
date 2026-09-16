from time import monotonic, sleep
from typing import Any

from supply_chain_mongodb_agent.db import get_client, get_database
from supply_chain_mongodb_agent.doctor import doctor_ok, doctor_report
from supply_chain_mongodb_agent.indexes import (
    ensure_atlas_search_indexes,
    ensure_btree_indexes,
)
from supply_chain_mongodb_agent.seed import seed_demo_data
from supply_chain_mongodb_agent.settings import Settings, get_settings


def validate_atlas_setup(
    settings: Settings | None = None,
    *,
    wait_indexes_seconds: int = 0,
    poll_seconds: int = 10,
) -> dict[str, Any]:
    """Idempotently prepare and verify the Atlas demo before serving it."""
    settings = settings or get_settings()
    client = get_client(settings)
    try:
        db = get_database(client, settings)
        client.admin.command("ping")
        btree_indexes = ensure_btree_indexes(db, settings)
        seeded = seed_demo_data(db, settings)
        search_indexes = ensure_atlas_search_indexes(db, settings)
    finally:
        client.close()

    checks = _doctor_report_with_index_wait(settings, wait_indexes_seconds, poll_seconds)
    return {
        "ok": doctor_ok(checks),
        "btree_indexes": btree_indexes,
        "seeded": seeded,
        "search_indexes": search_indexes,
        "checks": checks,
    }


def _doctor_report_with_index_wait(
    settings: Settings,
    wait_indexes_seconds: int,
    poll_seconds: int,
) -> list[dict[str, Any]]:
    deadline = monotonic() + max(wait_indexes_seconds, 0)
    checks = doctor_report(settings)
    while _search_indexes_pending(checks) and monotonic() < deadline:
        sleep(max(poll_seconds, 1))
        checks = doctor_report(settings)
    return checks


def _search_indexes_pending(checks: list[dict[str, Any]]) -> bool:
    return any(
        check["name"] == "search_indexes"
        and not check["ok"]
        and any(status in check["detail"] for status in ("missing indexes", "not ready", "stale index definitions"))
        for check in checks
    )