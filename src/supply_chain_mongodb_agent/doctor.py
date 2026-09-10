from typing import Any

from pymongo.errors import PyMongoError

from supply_chain_mongodb_agent.db import get_client, get_database
from supply_chain_mongodb_agent.seed import demo_documents
from supply_chain_mongodb_agent.settings import Settings, get_settings


def doctor_report(settings: Settings | None = None) -> list[dict[str, Any]]:
    """Return non-sensitive readiness checks for local and Atlas demo modes."""
    settings = settings or get_settings()
    checks = [
        _check("demo_mode", True, f"running in {settings.demo_mode!r} mode"),
        _check("sample_data", _sample_data_ready(settings), "deterministic sample documents are available"),
    ]
    if settings.demo_mode == "local":
        checks.extend([
            _check("credentials", True, "not required in local mode"),
            _check("atlas_features", True, "simulated locally; enable DEMO_MODE=atlas for real Atlas AI features"),
        ])
        return checks

    checks.append(_check("llm_provider", True, settings.effective_llm_provider))
    checks.append(_check("llm_base_url", True, "configured" if settings.effective_llm_base_url_configured else "default provider URL"))
    checks.append(_check(
        "llm_auth_strategy",
        True,
        "custom API-key header" if settings.effective_llm_api_key_header else "standard bearer token",
    ))
    checks.append(_check(
        "llm_api_key",
        settings.llm_api_key_configured,
        "configured" if settings.llm_api_key_configured else "missing or placeholder",
    ))
    try:
        client = get_client(settings)
        db = get_database(client, settings)
        client.admin.command("ping")
        checks.append(_check("mongodb_connection", True, f"connected to database {settings.mongodb_db!r}"))
        checks.append(_check("seed_data", db.shipments.count_documents({"realm_id": settings.realm_id}) > 0, "shipments collection has demo data"))
        checks.append(_check("search_indexes", _has_search_indexes(db, settings), "Atlas Search / Vector Search indexes detected"))
        client.close()
    except PyMongoError as exc:
        checks.append(_check("mongodb_connection", False, exc.__class__.__name__))
    return checks


def doctor_ok(checks: list[dict[str, Any]]) -> bool:
    return all(check["ok"] for check in checks)


def _sample_data_ready(settings: Settings) -> bool:
    docs = demo_documents(settings)
    return all(docs.get(name) for name in ("shipments", "knowledge_corpus", "agent_memories", "agent_episodes"))


def _has_search_indexes(db: Any, settings: Settings) -> bool:
    expected = {settings.knowledge_vector_index, settings.memory_vector_index, settings.episode_vector_index}
    found: set[str] = set()
    for collection in (db.knowledge_corpus, db.agent_memories, db.agent_episodes):
        found.update(index.get("name", "") for index in collection.list_search_indexes())
    return expected <= found


def _check(name: str, ok: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "ok": ok, "detail": detail}