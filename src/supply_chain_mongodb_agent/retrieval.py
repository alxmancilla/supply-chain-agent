from typing import Any

from pymongo.collection import Collection
from pymongo.errors import OperationFailure

from supply_chain_mongodb_agent.settings import Settings, get_settings


def knowledge_pipeline(query: str, settings: Settings | None = None, limit: int = 5) -> list[dict[str, Any]]:
    settings = settings or get_settings()
    vector_stage: dict[str, Any] = {
        "index": settings.knowledge_vector_index,
        "path": "text",
        "query": query,
        "model": settings.atlas_embedding_model,
        "numCandidates": max(limit * 20, 100),
        "limit": max(limit * 4, limit),
        "filter": {"realm_id": settings.realm_id},
    }
    pipeline: list[dict[str, Any]] = [
        {"$vectorSearch": vector_stage},
        {"$set": {"text": {"$ifNull": ["$text", ""]}}},
    ]
    if settings.atlas_native_rerank_enabled:
        pipeline.extend([
            {"$rerank": {"model": settings.atlas_rerank_model, "query": {"text": query}, "numDocsToRerank": min(limit * 4, 1000), "path": "text"}},
            {"$addFields": {"rerank_score": {"$meta": "score"}}},
        ])
    pipeline.extend([
        {"$limit": limit},
        {"$project": {"_id": 0, "doc_id": 1, "source": 1, "text": 1, "rerank_score": 1}},
    ])
    return pipeline


def memory_pipeline(query: str, settings: Settings | None = None, limit: int = 3) -> list[dict[str, Any]]:
    settings = settings or get_settings()
    return [
        {"$vectorSearch": {"index": settings.memory_vector_index, "path": "content", "query": query, "model": settings.atlas_embedding_model, "numCandidates": max(limit * 20, 100), "limit": limit, "filter": {"realm_id": settings.realm_id, "user_id": settings.user_id}}},
        {"$project": {"_id": 0, "memory_id": 1, "content": 1}},
    ]


def episode_pipeline(query: str, settings: Settings | None = None, limit: int = 3) -> list[dict[str, Any]]:
    settings = settings or get_settings()
    return [
        {"$vectorSearch": {"index": settings.episode_vector_index, "path": "content", "query": query, "model": settings.atlas_embedding_model, "numCandidates": max(limit * 20, 100), "limit": limit, "filter": {"realm_id": settings.realm_id, "user_id": settings.user_id}}},
        {"$project": {"_id": 0, "episode_id": 1, "incident_type": 1, "related_parts": 1, "outcome": 1, "content": 1, "resolved_at": 1}},
    ]


def run_pipeline_with_rerank_fallback(collection: Collection, pipeline: list[dict[str, Any]]) -> list[dict[str, Any]]:
    try:
        return list(collection.aggregate(pipeline))
    except OperationFailure as exc:
        if not any("$rerank" in stage for stage in pipeline):
            raise
        fallback = [stage for stage in pipeline if "$rerank" not in stage and "$addFields" not in stage]
        try:
            return list(collection.aggregate(fallback))
        except OperationFailure:
            raise exc