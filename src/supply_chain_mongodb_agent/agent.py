from typing import Any

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from langgraph.checkpoint.mongodb import MongoDBSaver
from langgraph.store.mongodb import MongoDBStore
from pymongo import MongoClient

from supply_chain_mongodb_agent.db import get_database
from supply_chain_mongodb_agent.grove import build_grove_chat
from supply_chain_mongodb_agent.prompts import SYSTEM_PROMPT
from supply_chain_mongodb_agent.settings import Settings, get_settings
from supply_chain_mongodb_agent.tools import build_tools


def build_agent(client: MongoClient, settings: Settings | None = None) -> Any:
    settings = settings or get_settings()
    db = get_database(client, settings)
    store = MongoDBStore(db.deep_agent_store)
    backend = CompositeBackend(
        default=StateBackend(),
        routes={
            "/memories/": StoreBackend(
                namespace=lambda _rt: (settings.realm_id, settings.agent_id, settings.user_id),
                store=store,
            )
        },
    )
    return create_deep_agent(
        model=build_grove_chat(settings),
        tools=build_tools(db, settings),
        system_prompt=SYSTEM_PROMPT,
        checkpointer=MongoDBSaver(client, db_name=settings.mongodb_db),
        store=store,
        backend=backend,
        interrupt_on={"submit_action_for_approval": True},
    )


def extract_latest_text(result: dict[str, Any]) -> str:
    messages = result.get("messages", [])
    if not messages:
        return ""
    last = messages[-1]
    content = getattr(last, "content", None)
    if content is None and isinstance(last, dict):
        content = last.get("content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        return _visible_text_from_content_item(content)
    if isinstance(content, list):
        parts = [_visible_text_from_content_item(item) for item in content]
        return "\n".join(part for part in parts if part)
    return str(content)


def format_pending_approval(result: dict[str, Any]) -> str:
    interrupts = result.get("__interrupt__", [])
    lines: list[str] = []
    for interrupt in interrupts:
        value = getattr(interrupt, "value", {}) or {}
        for request in value.get("action_requests", []):
            args = request.get("args", {})
            lines.extend([
                "⏸️  Pending human approval",
                f"Tool: {request.get('name', 'unknown')}",
                f"Action: {args.get('action_type', 'unknown')}",
                f"Shipment: {args.get('shipment_id', 'unknown')}",
                f"Estimated cost: {args.get('estimated_cost', 0)}",
                f"Rationale: {args.get('rationale', '')}",
            ])
    if not lines:
        return ""
    lines.append("Resume with: uv run supply-chain-agent approve --thread-id <thread>")
    return "\n".join(lines)


def _visible_text_from_content_item(item: Any) -> str:
    if isinstance(item, str):
        return item
    if not isinstance(item, dict):
        return ""
    text = item.get("text")
    if isinstance(text, str):
        return text
    if item.get("type") in {"text", "output_text"} and isinstance(item.get("content"), str):
        return item["content"]
    return ""