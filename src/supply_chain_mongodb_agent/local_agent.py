import re
from dataclasses import dataclass
from typing import Any

from supply_chain_mongodb_agent.seed import demo_documents
from supply_chain_mongodb_agent.settings import Settings, get_settings

TOKEN_RE = re.compile(r"[A-Z]+-[0-9]+|[a-z0-9]+")


@dataclass
class LocalDemoAgent:
    """Deterministic, credential-free agent for customer-shareable demos."""

    settings: Settings

    def invoke(self, payload: Any, config: dict[str, Any] | None = None) -> dict[str, Any]:
        question = _extract_question(payload)
        if _asks_for_approval(question):
            return _approval_interrupt(question)
        return {"messages": [{"role": "assistant", "content": self.answer(question, config)}]}

    def answer(self, question: str, config: dict[str, Any] | None = None) -> str:
        docs = demo_documents(self.settings)
        identifier = _find_identifier(question) or "SH-1043"
        shipment = _find_shipment(docs, identifier)
        part_id = (shipment or {}).get("part_id", identifier if identifier.startswith(("BRK", "CELL", "BOLT")) else "BRK-22")
        inventory = [doc for doc in docs["inventory"] if doc["part_id"] == part_id]
        days_cover = min((row["on_hand"] / row["daily_use"] for row in inventory if row["daily_use"]), default=0)
        knowledge = _lexical_search(docs["knowledge_corpus"], question + " " + part_id, "text", 3)
        memories = _lexical_search(docs["agent_memories"], question, "content", 1)
        episodes = _lexical_search(docs["agent_episodes"], question + " " + part_id, "content", 2)
        thread_id = ((config or {}).get("configurable") or {}).get("thread_id", "demo-thread")
        return _compose_answer(question, thread_id, shipment, part_id, days_cover, knowledge, memories, episodes)


def build_local_demo_agent(settings: Settings | None = None) -> LocalDemoAgent:
    return LocalDemoAgent(settings or get_settings())


def approve_local_demo(thread_id: str = "demo-thread") -> dict[str, Any]:
    return {
        "messages": [{
            "role": "assistant",
            "content": (
                f"✅ Local demo approval recorded for thread `{thread_id}`. "
                "In Atlas mode this approval resumes the persisted LangGraph checkpoint."
            ),
        }]
    }


def reject_local_demo(thread_id: str = "demo-thread") -> dict[str, Any]:
    return {
        "messages": [{
            "role": "assistant",
            "content": (
                f"🚫 Local demo rejection recorded for thread `{thread_id}`. "
                "In Atlas mode this rejection resumes the persisted LangGraph "
                "checkpoint without executing the drafted action."
            ),
        }]
    }


def _extract_question(payload: Any) -> str:
    if isinstance(payload, dict):
        messages = payload.get("messages", [])
        if messages:
            last = messages[-1]
            return last.get("content", "") if isinstance(last, dict) else str(getattr(last, "content", ""))
    return str(payload)


def _asks_for_approval(question: str) -> bool:
    text = question.lower()
    return "approval" in text or "approve" in text or "expedite" in text and "draft" in text


def _approval_interrupt(question: str) -> dict[str, Any]:
    shipment_id = _find_identifier(question) or "SH-1043"
    return {
        "__interrupt__": [{
            "value": {"action_requests": [{"name": "submit_action_for_approval", "args": {
                "action_type": "premium_freight", "shipment_id": shipment_id,
                "estimated_cost": 4200, "rationale": "Tier-1 shortage risk is below three days of cover.",
            }}]}
        }]
    }


def _find_identifier(question: str) -> str | None:
    match = re.search(r"\b(SH-[0-9]+|BRK-[0-9]+|CELL-[0-9]+|BOLT-[0-9]+)\b", question.upper())
    return match.group(1) if match else None


def _find_shipment(docs: dict[str, list[dict[str, Any]]], identifier: str) -> dict[str, Any] | None:
    return next((s for s in docs["shipments"] if identifier in {s["shipment_id"], s["part_id"]}), None)


def _tokens(text: str) -> set[str]:
    return {token.lower() for token in TOKEN_RE.findall(text)}


def _lexical_search(docs: list[dict[str, Any]], query: str, field: str, limit: int) -> list[dict[str, Any]]:
    query_tokens = _tokens(query)
    scored = [(len(query_tokens & _tokens(doc.get(field, ""))), doc) for doc in docs]
    return [doc for score, doc in sorted(scored, key=lambda item: item[0], reverse=True) if score > 0][:limit]


def _compose_answer(
    question: str,
    thread_id: str,
    shipment: dict[str, Any] | None,
    part_id: str,
    days_cover: float,
    knowledge: list[dict[str, Any]],
    memories: list[dict[str, Any]],
    episodes: list[dict[str, Any]],
) -> str:
    status = f"{shipment['shipment_id']} is {shipment['status']} by {shipment['delay_days']} days" if shipment else f"No live shipment found for {part_id}"
    risk = "high" if days_cover < 3 else "moderate" if days_cover < 7 else "low"
    recommendation = _recommendation(part_id, days_cover, shipment)
    sources = ", ".join(doc["source"] for doc in knowledge) or "seeded operational data"
    episode_line = f" Prior incident: {episodes[0]['episode_id']} — {episodes[0]['outcome']}." if episodes else ""
    memory_line = f" Planner memory: {memories[0]['content']}" if memories else ""
    return (
        "**Local demo mode — no credentials required.**\n\n"
        f"Thread `{thread_id}` used deterministic seeded data to answer: _{question}_\n\n"
        f"- **Operational state:** {status}; calculated cover is **{days_cover:.1f} days** for `{part_id}`.\n"
        f"- **Risk:** {risk}.\n"
        f"- **Recommendation:** {recommendation}\n"
        f"- **Evidence:** {sources}.{episode_line}{memory_line}\n\n"
        "Switch to `DEMO_MODE=atlas` to use MongoDBSaver checkpoints, MongoDBStore memory, Atlas Vector Search auto-embedding, native `$rerank`, and a connected LLM."
    )


def _recommendation(part_id: str, days_cover: float, shipment: dict[str, Any] | None) -> str:
    reason = (shipment or {}).get("reason", "")
    if part_id == "CELL-9" or "quality" in reason:
        return "quarantine suspect lots, request supplier 8D within 24 hours, and pull replacement supply before approving deviation use."
    if days_cover < 3:
        return "request partial release, price premium freight, and engage the approved alternate supplier before line stoppage."
    return "avoid premium freight for now, monitor ETA, and use the backup carrier only if cover drops below the policy threshold."