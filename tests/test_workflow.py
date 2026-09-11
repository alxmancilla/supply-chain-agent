from supply_chain_mongodb_agent.workflow import workflow_diagram_dot, workflow_notes


def test_workflow_diagram_includes_core_agent_components() -> None:
    dot = workflow_diagram_dot()

    assert "Atlas connected agent" in dot
    assert "MongoDB state" in dot
    assert "Atlas Vector Search" in dot
    assert "Scoped memory" in dot
    assert "Human approval" in dot
    assert "Configured LLM" in dot


def test_workflow_diagram_only_shows_atlas_flow() -> None:
    dot = workflow_diagram_dot()

    assert "DEMO_MODE=local" not in dot
    assert "Local agent" not in dot
    assert "Mode router" not in dot


def test_workflow_notes_describe_atlas_architecture() -> None:
    atlas_notes = "\n".join(workflow_notes())

    assert "LangChain" in atlas_notes
    assert "LangGraph" in atlas_notes
    assert "Deep Agents" in atlas_notes
    assert "MongoDB Atlas" in atlas_notes
    assert "realm_id, agent_id, and user_id" in atlas_notes