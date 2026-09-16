from supply_chain_mongodb_agent.workflow import workflow_diagram_dot, workflow_notes


def test_workflow_diagram_includes_core_agent_components() -> None:
    dot = workflow_diagram_dot()

    assert "Atlas-only supply-chain resolution agent" in dot
    assert "LangGraph" in dot
    assert "Deep Agents" in dot
    assert "MongoDBSaver" in dot
    assert "MongoDBStore" in dot
    assert "Atlas Vector Search" in dot
    assert "MongoDB Atlas services" in dot
    assert "Scoped data boundary" in dot


def test_workflow_diagram_includes_agent_runtime_states() -> None:
    dot = workflow_diagram_dot()

    assert "LangGraph agent runtime" in dot
    assert "Request received" in dot
    assert "Load thread checkpoint" in dot
    assert "Gather scoped context" in dot
    assert "Reason with LLM" in dot
    assert "Decision point" in dot
    assert "Read-only answer" in dot
    assert "Draft action" in dot
    assert "Human approval interrupt" in dot
    assert "Resume same thread" in dot
    assert "Persist outcome" in dot


def test_workflow_diagram_includes_visual_legend() -> None:
    dot = workflow_diagram_dot()

    assert "rankdir=TB" in dot
    assert "splines=ortho" in dot
    assert "Solid blue arrows" in dot
    assert "Dashed gray arrows" in dot


def test_workflow_diagram_separates_setup_runtime_and_support() -> None:
    dot = workflow_diagram_dot()

    assert "Demo entry + setup" in dot
    assert "Bootstrap once" in dot
    assert "3 Vector Search indexes" in dot
    assert "Readiness checks" in dot
    assert "Framework layer" in dot


def test_workflow_diagram_only_shows_atlas_flow() -> None:
    dot = workflow_diagram_dot()

    assert "Mode router" not in dot
    assert "DEMO_MODE=local" not in dot
    assert "Local agent" not in dot


def test_workflow_notes_describe_atlas_architecture() -> None:
    atlas_notes = "\n".join(workflow_notes())

    assert "LangChain" in atlas_notes
    assert "LangGraph" in atlas_notes
    assert "Deep Agents" in atlas_notes
    assert "Atlas-only" in atlas_notes
    assert "M0-compatible" in atlas_notes
    assert "solid blue path" in atlas_notes
    assert "decision point" in atlas_notes
    assert "MongoDB Atlas" in atlas_notes
    assert "realm_id, agent_id, and user_id" in atlas_notes
