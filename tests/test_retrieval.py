from supply_chain_mongodb_agent.retrieval import (
    episode_pipeline,
    knowledge_pipeline,
    memory_pipeline,
)
from supply_chain_mongodb_agent.settings import Settings


def test_knowledge_pipeline_uses_autoembed_query_and_rerank() -> None:
    settings = Settings(realm_id="r1", atlas_native_rerank_enabled=True)
    pipeline = knowledge_pipeline("late shipment", settings, limit=4)
    vector = pipeline[0]["$vectorSearch"]
    assert vector["query"] == "late shipment"
    assert vector["model"] == "voyage-4"
    assert vector["numCandidates"] >= 100
    assert vector["filter"] == {"realm_id": "r1"}
    assert any("$rerank" in stage for stage in pipeline)


def test_memory_pipeline_is_user_scoped() -> None:
    settings = Settings(realm_id="r1", user_id="u1")
    vector = memory_pipeline("preference", settings)[0]["$vectorSearch"]
    assert vector["numCandidates"] >= 100
    assert vector["filter"] == {"realm_id": "r1", "user_id": "u1"}


def test_episode_pipeline_is_user_scoped() -> None:
    settings = Settings(realm_id="r1", user_id="u1")
    vector = episode_pipeline("prior BRK-22 delay", settings)[0]["$vectorSearch"]
    assert vector["index"] == "agent_episodes_autoembed"
    assert vector["path"] == "content"
    assert vector["filter"] == {"realm_id": "r1", "user_id": "u1"}