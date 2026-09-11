from typing import Any

from supply_chain_mongodb_agent.settings import Settings
from supply_chain_mongodb_agent.tools import build_tools


class FakeCollection:
    def __init__(self) -> None:
        self.inserted: list[dict[str, Any]] = []

    def insert_one(self, doc: dict[str, Any]) -> None:
        self.inserted.append(doc)


class FakeDb:
    def __init__(self) -> None:
        self.action_drafts = FakeCollection()
        self.agent_memories = FakeCollection()


def tool_by_name(tools: list[Any], name: str) -> Any:
    return next(tool for tool in tools if tool.name == name)


def test_action_draft_write_is_tenant_agent_and_user_scoped() -> None:
    db = FakeDb()
    settings = Settings(realm_id="realm-test", agent_id="agent-test", user_id="user-test")
    tool = tool_by_name(build_tools(db, settings), "submit_action_for_approval")

    result = tool.invoke({"action_type": "EXPEDITE", "shipment_id": "SH-1", "rationale": "low cover"})

    assert result["realm_id"] == "realm-test"
    assert result["agent_id"] == "agent-test"
    assert result["user_id"] == "user-test"
    assert db.action_drafts.inserted[0]["agent_id"] == "agent-test"


def test_memory_write_is_tenant_agent_and_user_scoped() -> None:
    db = FakeDb()
    settings = Settings(realm_id="realm-test", agent_id="agent-test", user_id="user-test")
    tool = tool_by_name(build_tools(db, settings), "remember_resolution")

    result = tool.invoke({"summary": "Prefer split shipments before premium freight."})

    assert result["status"] == "stored"
    assert db.agent_memories.inserted[0]["realm_id"] == "realm-test"
    assert db.agent_memories.inserted[0]["agent_id"] == "agent-test"
    assert db.agent_memories.inserted[0]["user_id"] == "user-test"