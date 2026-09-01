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
    db.agent_memories.create_index([("realm_id", 1), ("user_id", 1)])
    db.agent_episodes.create_index([("realm_id", 1), ("user_id", 1), ("resolved_at", -1)])
    db.action_drafts.create_index([("realm_id", 1), ("draft_id", 1)], unique=True)
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


def _search_index_exists(collection: Any, name: str) -> bool:
    try:
        return any(index.get("name") == name for index in collection.list_search_indexes(name))
    except (OperationFailure, PyMongoError):
        return False


def _ensure_search_index(collection: Any, name: str, definition: dict[str, Any], kind: str) -> str:
    if _search_index_exists(collection, name):
        return f"exists:{collection.name}.{name}"
    model = SearchIndexModel(definition=definition, name=name, type=kind)
    collection.create_search_index(model)
    return f"created:{collection.name}.{name}"


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
            autoembed_definition("content", settings.atlas_embedding_model, ("realm_id", "user_id")),
            "vectorSearch",
        ),
        _ensure_search_index(
            db.agent_episodes,
            settings.episode_vector_index,
            autoembed_definition("content", settings.atlas_embedding_model, ("realm_id", "user_id")),
            "vectorSearch",
        ),
        _ensure_search_index(
            db.knowledge_corpus,
            settings.knowledge_search_index,
            search_definition(),
            "search",
        ),
    ]