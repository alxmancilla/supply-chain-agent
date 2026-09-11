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
        seed_check = _seed_data_check(db, settings)
        checks.append(_check("seed_data", seed_check["ok"], seed_check["detail"]))
        index_check = _search_index_check(db, settings)
        checks.append(_check("search_indexes", index_check["ok"], index_check["detail"]))
        client.close()
    except PyMongoError as exc:
        checks.append(_check("mongodb_connection", False, exc.__class__.__name__))
    return checks


def doctor_ok(checks: list[dict[str, Any]]) -> bool:
    return all(check["ok"] for check in checks)


def _sample_data_ready(settings: Settings) -> bool:
    docs = demo_documents(settings)
    return all(docs.get(name) for name in ("shipments", "knowledge_corpus", "agent_memories", "agent_episodes"))


def _seed_data_check(db: Any, settings: Settings) -> dict[str, Any]:
    realm_scope = {"realm_id": settings.realm_id}
    actor_scope = realm_scope | {"agent_id": settings.agent_id, "user_id": settings.user_id}
    required = {
        "shipments": (db.shipments, realm_scope),
        "knowledge_corpus": (db.knowledge_corpus, realm_scope),
        "agent_memories": (db.agent_memories, actor_scope),
        "agent_episodes": (db.agent_episodes, actor_scope),
    }
    missing = [name for name, (collection, query) in required.items() if collection.count_documents(query) == 0]
    if missing:
        return {"ok": False, "detail": f"missing scoped demo data: {', '.join(missing)}; run `uv run supply-chain-agent seed`"}
    return {"ok": True, "detail": "scoped demo data is available"}


def _search_index_check(db: Any, settings: Settings) -> dict[str, Any]:
    expected = {
        settings.knowledge_vector_index: (db.knowledge_corpus, {"realm_id"}),
        settings.memory_vector_index: (db.agent_memories, {"realm_id", "agent_id", "user_id"}),
        settings.episode_vector_index: (db.agent_episodes, {"realm_id", "agent_id", "user_id"}),
    }
    found: dict[str, str] = {}
    stale: list[str] = []
    for name, (collection, required_filters) in expected.items():
        for index in collection.list_search_indexes():
            index_name = index.get("name", "")
            if not index_name:
                continue
            found[index_name] = "QUERYABLE" if index.get("queryable") is True else index.get("status") or "exists"
            if index_name == name:
                filter_paths = _search_index_filter_paths(index)
                missing_filters = sorted(required_filters - filter_paths) if filter_paths is not None else []
                if filter_paths is not None and missing_filters:
                    stale.append(f"{name} missing filters: {', '.join(missing_filters)}")
    missing = sorted(set(expected) - set(found))
    if missing:
        return {"ok": False, "detail": f"missing indexes: {', '.join(missing)}; run `uv run supply-chain-agent indexes`"}
    if stale:
        return {"ok": False, "detail": f"stale index definitions: {'; '.join(stale)}; rerun `uv run supply-chain-agent indexes`"}
    not_ready = sorted(name for name in expected if str(found[name]).upper() not in {"READY", "QUERYABLE", "TRUE", "EXISTS"})
    if not_ready:
        return {"ok": False, "detail": f"indexes found but not ready yet: {', '.join(not_ready)}; wait and rerun doctor"}
    return {"ok": True, "detail": "Atlas Search / Vector Search indexes detected"}


def _search_index_filter_paths(index: dict[str, Any]) -> set[str] | None:
    definition = index.get("latestDefinition") or index.get("definition") or {}
    if not definition:
        return None
    return {field.get("path", "") for field in definition.get("fields", []) if field.get("type") == "filter"}


def _check(name: str, ok: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "ok": ok, "detail": detail}
