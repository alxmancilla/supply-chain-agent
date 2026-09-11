from supply_chain_mongodb_agent.workflow import workflow_diagram_dot, workflow_notes


def test_workflow_diagram_includes_core_agent_components() -> None:
    dot = workflow_diagram_dot()

    assert "LangGraph" in dot
    assert "Deep Agents" in dot
    assert "MongoDBSaver" in dot
    assert "MongoDBStore" in dot
    assert "Atlas Vector Search" in dot
    assert "MongoDB Atlas" in dot


def test_workflow_diagram_includes_agent_runtime_states() -> None:
    dot = workflow_diagram_dot()

    assert "Agent runtime states" in dot
    assert "Request received" in dot
    assert "Load thread state" in dot
    assert "Retrieve operational context" in dot
    assert "Recall scoped memory" in dot
    assert "Decision point" in dot
    assert "Pending human approval" in dot
    assert "Approval resume" in dot
    assert "Persist state + memory" in dot


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
    assert "state transitions" in atlas_notes
    assert "decision point" in atlas_notes
    assert "MongoDB Atlas" in atlas_notes
    assert "realm_id, agent_id, and user_id" in atlas_notes