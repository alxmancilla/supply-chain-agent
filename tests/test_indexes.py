from typing import Any

from supply_chain_mongodb_agent.indexes import (
    autoembed_definition,
    ensure_atlas_search_indexes,
    search_definition,
)
from supply_chain_mongodb_agent.settings import Settings


class FakeCollection:
    def __init__(self, name: str, existing: dict[str, Any] | None = None) -> None:
        self.name = name
        self.existing = existing
        self.created: list[Any] = []
        self.updated: list[tuple[str, dict[str, Any]]] = []

    def list_search_indexes(self, name: str | None = None) -> list[dict[str, Any]]:
        if self.existing is None:
            return []
        if name is not None and self.existing.get("name") != name:
            return []
        return [self.existing]

    def create_search_index(self, model: Any) -> None:
        self.created.append(model)

    def update_search_index(self, name: str, definition: dict[str, Any]) -> None:
        self.updated.append((name, definition))


def filter_paths(definition: dict[str, Any]) -> set[str]:
    return {field["path"] for field in definition["fields"] if field["type"] == "filter"}


def test_memory_and_episode_vector_indexes_include_agent_filter() -> None:
    definition = autoembed_definition("content", "voyage-4", ("realm_id", "agent_id", "user_id"))
    assert filter_paths(definition) == {"realm_id", "agent_id", "user_id"}


def test_ensure_atlas_search_indexes_updates_stale_agent_scoped_indexes() -> None:
    settings = Settings()
    stale = autoembed_definition("content", settings.atlas_embedding_model, ("realm_id", "user_id"))

    class Db:
        knowledge_corpus = FakeCollection(
            "knowledge_corpus",
            {"name": settings.knowledge_vector_index, "latestDefinition": autoembed_definition("text", settings.atlas_embedding_model, ("realm_id",))},
        )
        agent_memories = FakeCollection("agent_memories", {"name": settings.memory_vector_index, "latestDefinition": stale})
        agent_episodes = FakeCollection("agent_episodes", {"name": settings.episode_vector_index, "latestDefinition": stale})

    db = Db()
    db.knowledge_corpus.existing = {"name": settings.knowledge_search_index, "latestDefinition": search_definition()}
    results = ensure_atlas_search_indexes(db, settings)

    assert f"updated:agent_memories.{settings.memory_vector_index}" in results
    assert f"updated:agent_episodes.{settings.episode_vector_index}" in results
    assert filter_paths(db.agent_memories.updated[0][1]) == {"realm_id", "agent_id", "user_id"}