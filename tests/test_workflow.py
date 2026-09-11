from supply_chain_mongodb_agent.settings import Settings
from supply_chain_mongodb_agent.workflow import workflow_diagram_dot, workflow_notes


def test_workflow_diagram_includes_core_agent_components() -> None:
    dot = workflow_diagram_dot(Settings(demo_mode="atlas"))

    assert "LangGraph deep agent" in dot
    assert "Atlas Vector Search" in dot
    assert "Scoped memory" in dot
    assert "Human approval" in dot
    assert "Configured LLM" in dot


def test_workflow_diagram_is_mode_aware() -> None:
    local_dot = workflow_diagram_dot(Settings(demo_mode="local"))
    atlas_dot = workflow_diagram_dot(Settings(demo_mode="atlas"))

    assert "Local deterministic path" in local_dot
    assert "Atlas connected path" in atlas_dot


def test_workflow_notes_are_mode_aware() -> None:
    local_notes = "\n".join(workflow_notes(Settings(demo_mode="local")))
    atlas_notes = "\n".join(workflow_notes(Settings(demo_mode="atlas")))

    assert "no MongoDB" in local_notes
    assert "realm_id, agent_id, and user_id" in atlas_notes