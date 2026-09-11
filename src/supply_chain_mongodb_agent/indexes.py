from typing import Any

from pymongo.database import Database
from pymongo.errors import OperationFailure, PyMongoError
from pymongo.operations import SearchIndexModel

from supply_chain_mongodb_agent.settings import Settings, get_settings


def ensure_btree_indexes(db: Database, settings: Settings | None = None) -> list[str]:
    settings = settings or get_settings()
    created: list[str] = []
    for coll in ["suppliers", "parts", "shipments", "inventory", "purchase_orders"]:
        db[coll].create_index([("realm_id", 1)])
        created.append(f"{coll}.realm_id_1")
    db.shipments.create_index([("realm_id", 1), ("shipment_id", 1)], unique=True)
    db.parts.create_index([("realm_id", 1), ("part_id", 1)], unique=True)
    db.inventory.create_index([("realm_id", 1), ("part_id", 1), ("site", 1)], unique=True)
    db.agent_memories.create_index([("realm_id", 1), ("agent_id", 1), ("user_id", 1)])
    db.agent_episodes.create_index([("realm_id", 1), ("agent_id", 1), ("user_id", 1), ("resolved_at", -1)])
    db.action_drafts.create_index([("realm_id", 1), ("agent_id", 1), ("draft_id", 1)], unique=True)
    return created


def autoembed_definition(path: str, model: str, filter_paths: tuple[str, ...]) -> dict[str, Any]:
    return {
        "fields": [
            {"type": "autoEmbed", "modality": "text", "path": path, "model": model},
            *({"type": "filter", "path": filter_path} for filter_path in filter_paths),
        ]
    }


def search_definition() -> dict[str, Any]:
    return {"mappings": {"dynamic": False, "fields": {"text": {"type": "string"}}}}


def _search_index(collection: Any, name: str) -> dict[str, Any] | None:
    try:
        return next((index for index in collection.list_search_indexes(name) if index.get("name") == name), None)
    except (OperationFailure, PyMongoError):
        return None


def _filter_paths(definition: dict[str, Any]) -> set[str]:
    return {field.get("path", "") for field in definition.get("fields", []) if field.get("type") == "filter"}


def _ensure_search_index(collection: Any, name: str, definition: dict[str, Any], kind: str) -> str:
    existing = _search_index(collection, name)
    if existing is None:
        model = SearchIndexModel(definition=definition, name=name, type=kind)
        collection.create_search_index(model)
        return f"created:{collection.name}.{name}"

    current_definition = existing.get("latestDefinition") or existing.get("definition") or {}
    if kind == "vectorSearch" and not _filter_paths(definition) <= _filter_paths(current_definition):
        collection.update_search_index(name, definition)
        return f"updated:{collection.name}.{name}"
    if kind == "search" and current_definition and current_definition != definition:
        collection.update_search_index(name, definition)
        return f"updated:{collection.name}.{name}"
    if current_definition == {}:
        return f"exists:{collection.name}.{name}:definition-not-inspected"
    else:
        return f"exists:{collection.name}.{name}"


def ensure_atlas_search_indexes(db: Database, settings: Settings | None = None) -> list[str]:
    settings = settings or get_settings()
    return [
        _ensure_search_index(
            db.knowledge_corpus,
            settings.knowledge_vector_index,
            autoembed_definition("text", settings.atlas_embedding_model, ("realm_id",)),
            "vectorSearch",
        ),
        _ensure_search_index(
            db.agent_memories,
            settings.memory_vector_index,
            autoembed_definition("content", settings.atlas_embedding_model, ("realm_id", "agent_id", "user_id")),
            "vectorSearch",
        ),
        _ensure_search_index(
            db.agent_episodes,
            settings.episode_vector_index,
            autoembed_definition("content", settings.atlas_embedding_model, ("realm_id", "agent_id", "user_id")),
            "vectorSearch",
        ),
        _ensure_search_index(
            db.knowledge_corpus,
            settings.knowledge_search_index,
            search_definition(),
            "search",
        ),
    ]