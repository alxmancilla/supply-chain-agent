from supply_chain_mongodb_agent.seed import (
    demo_documents,
    episode_documents,
    knowledge_documents,
)
from supply_chain_mongodb_agent.settings import Settings


def test_seed_documents_are_tenant_scoped() -> None:
    settings = Settings(realm_id="realm-test", user_id="u1")
    docs = demo_documents(settings)
    assert docs["shipments"][0]["realm_id"] == "realm-test"
    assert docs["agent_memories"][0]["user_id"] == "u1"
    assert docs["agent_episodes"][0]["user_id"] == "u1"


def test_knowledge_docs_include_supply_chain_playbook() -> None:
    docs = knowledge_documents(Settings())
    assert any("Tier-1" in doc["text"] for doc in docs)


def test_episode_docs_cover_multiple_incident_types() -> None:
    incident_types = {doc["incident_type"] for doc in episode_documents(Settings())}
    assert {"logistics_delay", "quality_hold", "low_risk_delay"} <= incident_types