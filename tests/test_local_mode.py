from typer.testing import CliRunner

from supply_chain_mongodb_agent.agent import (
    build_agent,
    extract_latest_text,
    format_pending_approval,
)
from supply_chain_mongodb_agent.cli import app
from supply_chain_mongodb_agent.doctor import (
    _search_index_check,
    _seed_data_check,
    doctor_ok,
    doctor_report,
)
from supply_chain_mongodb_agent.llm import build_chat_model
from supply_chain_mongodb_agent.local_agent import approve_local_demo
from supply_chain_mongodb_agent.settings import Settings

runner = CliRunner()


def test_local_agent_answers_without_credentials() -> None:
    settings = Settings(demo_mode="local", llm_api_key=None, grove_api_key=None)
    agent = build_agent(None, settings)
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "Shipment SH-1043 for BRK-22 is late. What are my options?"}]},
        config={"configurable": {"thread_id": "t1"}},
    )
    answer = extract_latest_text(result)
    assert "Local demo mode" in answer
    assert "SH-1043" in answer
    assert "SOP-EXP-01" in answer or "AVL-BRK-22" in answer


def test_guided_demo_runs_without_credentials() -> None:
    result = runner.invoke(app, ["demo", "--local", "--thread-id", "walkthrough"], env={"DEMO_MODE": "atlas", "LLM_API_KEY": "", "GROVE_API_KEY": ""})
    assert result.exit_code == 0
    assert "Thread: walkthrough" in result.output
    assert "No credentials, database, or LLM are required" in result.output
    assert "SH-1043" in result.output
    assert "Pending human approval" in result.output


def test_local_agent_formats_pending_approval() -> None:
    settings = Settings(demo_mode="local", llm_api_key=None, grove_api_key=None)
    agent = build_agent(None, settings)
    result = agent.invoke({"messages": [{"role": "user", "content": "Draft an approval request to expedite SH-1043"}]})
    formatted = format_pending_approval(result)
    assert "Pending human approval" in formatted
    assert "SH-1043" in formatted


def test_local_approval_resume_is_simulated() -> None:
    answer = extract_latest_text(approve_local_demo("abc"))
    assert "abc" in answer
    assert "Local demo approval" in answer


def test_local_doctor_is_ok_without_credentials() -> None:
    checks = doctor_report(Settings(demo_mode="local", llm_api_key=None, grove_api_key=None))
    assert doctor_ok(checks)
    assert {check["name"] for check in checks} >= {"demo_mode", "sample_data", "credentials"}


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

    result = _seed_data_check(Db(), Settings(realm_id="realm-test", agent_id="agent-test", user_id="user-test"))
    assert result["ok"]
    missing = _seed_data_check(Db(), Settings(realm_id="realm-test", agent_id="other-agent", user_id="user-test"))
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
    settings = Settings(demo_mode="atlas", llm_api_key="<your-llm-api-key>", grove_api_key=None)
    assert not settings.llm_api_key_configured
    try:
        build_chat_model(settings)
    except ValueError as exc:
        assert "LLM_API_KEY" in str(exc)
    else:
        raise AssertionError("placeholder LLM key should not build a chat model")


def test_llm_settings_support_openai_compatible_provider() -> None:
    settings = Settings(
        demo_mode="atlas",
        llm_api_key="test-key",
        llm_base_url="https://llm.example/v1/",
        llm_model="provider-model",
        llm_use_responses_api=False,
        grove_api_key=None,
    )
    assert settings.llm_api_key_configured
    assert settings.effective_llm_provider == "openai_compatible"
    assert settings.effective_llm_base_url == "https://llm.example/v1"
    assert settings.effective_llm_model == "provider-model"
    assert build_chat_model(settings).model_name == "provider-model"


def test_llm_settings_auto_detect_header_gateway() -> None:
    settings = Settings(
        demo_mode="atlas",
        llm_api_key="test-key",
        llm_base_url="https://gateway.azure-api.net/openai/v1",
        llm_model="provider-model",
        llm_use_responses_api=False,
        grove_api_key=None,
    )
    assert settings.effective_llm_api_key_header == "api-key"
    assert settings.effective_llm_use_responses_api is True
