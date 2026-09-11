from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from langchain_core.tools import tool
from pymongo.database import Database

from supply_chain_mongodb_agent.retrieval import (
    episode_pipeline,
    knowledge_pipeline,
    memory_pipeline,
    run_pipeline_with_rerank_fallback,
)
from supply_chain_mongodb_agent.settings import Settings, get_settings


def build_tools(db: Database, settings: Settings | None = None) -> list[Any]:
    settings = settings or get_settings()

    @tool
    def get_supply_chain_snapshot(identifier: str) -> dict[str, Any]:
        """Fetch live shipment, PO, supplier, part, and inventory facts by shipment or part ID."""
        scope = {"realm_id": settings.realm_id}
        shipment = db.shipments.find_one(scope | {"shipment_id": identifier}, {"_id": 0})
        if shipment is None:
            shipment = db.shipments.find_one(scope | {"part_id": identifier}, {"_id": 0})
        part_id = (shipment or {}).get("part_id", identifier)
        supplier_id = (shipment or {}).get("supplier_id")
        return {
            "shipment": shipment,
            "part": db.parts.find_one(scope | {"part_id": part_id}, {"_id": 0}),
            "inventory": list(db.inventory.find(scope | {"part_id": part_id}, {"_id": 0})),
            "purchase_orders": list(db.purchase_orders.find(scope | {"part_id": part_id}, {"_id": 0})),
            "supplier": db.suppliers.find_one(scope | {"supplier_id": supplier_id}, {"_id": 0}) if supplier_id else None,
        }

    @tool
    def search_supply_chain_knowledge(query: str, limit: int = 5) -> list[dict[str, Any]]:
        """Search SOPs, contracts, and playbooks using Atlas auto-embedding and native rerank."""
        return run_pipeline_with_rerank_fallback(db.knowledge_corpus, knowledge_pipeline(query, settings, limit))

    @tool
    def recall_planner_memory(query: str, limit: int = 3) -> list[dict[str, Any]]:
        """Recall agent/user-scoped long-term memories from MongoDB Atlas Vector Search."""
        return run_pipeline_with_rerank_fallback(db.agent_memories, memory_pipeline(query, settings, limit))

    @tool
    def recall_prior_incidents(query: str, limit: int = 3) -> list[dict[str, Any]]:
        """Recall prior resolved supply-chain incidents from episodic memory."""
        return run_pipeline_with_rerank_fallback(db.agent_episodes, episode_pipeline(query, settings, limit))

    @tool
    def submit_action_for_approval(action_type: str, shipment_id: str, rationale: str, estimated_cost: float = 0.0) -> dict[str, Any]:
        """Draft a state-changing action. Human approval is required before execution."""
        draft = {
            "realm_id": settings.realm_id,
            "agent_id": settings.agent_id,
            "user_id": settings.user_id,
            "draft_id": f"draft-{uuid4().hex[:10]}",
            "action_type": action_type,
            "shipment_id": shipment_id,
            "rationale": rationale,
            "estimated_cost": estimated_cost,
            "status": "pending_approval",
            "created_at": datetime.now(UTC),
        }
        db.action_drafts.insert_one(draft)
        return {k: v for k, v in draft.items() if k != "_id"}

    @tool
    def remember_resolution(summary: str) -> dict[str, str]:
        """Persist a useful planner preference or resolved-incident lesson to long-term memory."""
        memory_id = f"mem-{uuid4().hex[:10]}"
        db.agent_memories.insert_one({
            "realm_id": settings.realm_id,
            "agent_id": settings.agent_id,
            "user_id": settings.user_id,
            "memory_id": memory_id,
            "content": summary,
            "created_at": datetime.now(UTC),
        })
        return {"memory_id": memory_id, "status": "stored"}

    return [
        get_supply_chain_snapshot,
        search_supply_chain_knowledge,
        recall_planner_memory,
        recall_prior_incidents,
        submit_action_for_approval,
        remember_resolution,
    ]