from supply_chain_mongodb_agent.agent import build_agent
from supply_chain_mongodb_agent.doctor import (
    _search_index_check,
    _seed_data_check,
)
from supply_chain_mongodb_agent.llm import build_chat_model
from supply_chain_mongodb_agent.settings import Settings


def test_settings_ignore_legacy_mode_input() -> None:
    settings = Settings(demo_mode="unsupported")

    assert settings.demo_mode == "atlas"


def test_atlas_agent_requires_mongodb_client() -> None:
    try:
        build_agent(None, Settings())
    except ValueError as exc:
        assert "MongoDB client" in str(exc)
    else:
        raise AssertionError("Atlas agent should require a MongoDB client")


def test_search_index_check_reports_missing_indexes() -> None:
    class Collection:
        def list_search_indexes(self) -> list[dict[str, str]]:
            return []

    class Db:
        knowledge_corpus = Collection()
        agent_memories = Collection()
        agent_episodes = Collection()

    result = _search_index_check(Db(), Settings())
    assert not result["ok"]
    assert "missing indexes" in result["detail"]


def test_seed_data_check_requires_agent_scoped_memory() -> None:
    class Collection:
        def __init__(self, count: int) -> None:
            self.count = count

        def count_documents(self, query: dict[str, str]) -> int:
            if "agent_id" in query and query["agent_id"] != "agent-test":
                return 0
            return self.count

    class Db:
        shipments = Collection(1)
        knowledge_corpus = Collection(1)
        agent_memories = Collection(1)
        agent_episodes = Collection(1)

    result = _seed_data_check(
        Db(),
        Settings(realm_id="realm-test", agent_id="agent-test", user_id="user-test"),
    )
    assert result["ok"]
    missing = _seed_data_check(
        Db(),
        Settings(realm_id="realm-test", agent_id="other-agent", user_id="user-test"),
    )
    assert not missing["ok"]
    assert "agent_memories" in missing["detail"]


def test_search_index_check_reports_indexes_not_ready() -> None:
    class Collection:
        def __init__(self, name: str) -> None:
            self.name = name

        def list_search_indexes(self) -> list[dict[str, str]]:
            return [{"name": self.name, "status": "BUILDING"}]

    class Db:
        knowledge_corpus = Collection("knowledge_corpus_autoembed")
        agent_memories = Collection("agent_memories_autoembed")
        agent_episodes = Collection("agent_episodes_autoembed")

    result = _search_index_check(Db(), Settings())
    assert not result["ok"]
    assert "not ready" in result["detail"]


def test_search_index_check_accepts_queryable_building_indexes() -> None:
    class Collection:
        def __init__(self, name: str, filters: tuple[str, ...]) -> None:
            self.name = name
            self.filters = filters

        def list_search_indexes(self) -> list[dict[str, object]]:
            return [{
                "name": self.name,
                "status": "BUILDING",
                "queryable": True,
                "latestDefinition": {"fields": [{"type": "filter", "path": path} for path in self.filters]},
            }]

    class Db:
        knowledge_corpus = Collection("knowledge_corpus_autoembed", ("realm_id",))
        agent_memories = Collection("agent_memories_autoembed", ("realm_id", "agent_id", "user_id"))
        agent_episodes = Collection("agent_episodes_autoembed", ("realm_id", "agent_id", "user_id"))

    result = _search_index_check(Db(), Settings())
    assert result["ok"]


def test_search_index_check_reports_stale_filter_definitions() -> None:
    class Collection:
        def __init__(self, name: str, filters: tuple[str, ...]) -> None:
            self.name = name
            self.filters = filters

        def list_search_indexes(self) -> list[dict[str, object]]:
            return [{
                "name": self.name,
                "status": "READY",
                "latestDefinition": {"fields": [{"type": "filter", "path": path} for path in self.filters]},
            }]

    class Db:
        knowledge_corpus = Collection("knowledge_corpus_autoembed", ("realm_id",))
        agent_memories = Collection("agent_memories_autoembed", ("realm_id", "user_id"))
        agent_episodes = Collection("agent_episodes_autoembed", ("realm_id", "user_id"))

    result = _search_index_check(Db(), Settings())
    assert not result["ok"]
    assert "stale index definitions" in result["detail"]
    assert "agent_id" in result["detail"]


def test_placeholder_llm_key_is_not_configured() -> None:
    settings = Settings(llm_api_key="<your-llm-api-key>", grove_api_key=None)
    assert not settings.llm_api_key_configured
    try:
        build_chat_model(settings)
    except ValueError as exc:
        assert "Atlas demo" in str(exc)
    else:
        raise AssertionError("placeholder LLM key should not build a chat model")


def test_llm_settings_auto_detect_header_gateway() -> None:
    settings = Settings(
        llm_api_key="test-key",
        llm_base_url="https://gateway.azure-api.net/openai/v1",
        llm_model="provider-model",
        llm_use_responses_api=False,
        grove_api_key=None,
    )

    assert settings.effective_llm_api_key_header == "api-key"
    assert settings.effective_llm_use_responses_api is True