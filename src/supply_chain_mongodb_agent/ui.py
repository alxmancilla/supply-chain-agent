from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DemoPrompt:
    label: str
    question: str
    intent: str


VALUE_PILLARS: tuple[tuple[str, str], ...] = (
    (
        "MongoDB Atlas",
        "Operational data, checkpoints, memory, and approval drafts in one place.",
    ),
    (
        "Atlas Vector Search",
        "Retrieves policies, planner memories, and prior incidents with auto-embedding.",
    ),
    (
        "LangChain tools",
        "Connects the LLM to safe read tools and approval-gated write tools.",
    ),
    (
        "LangGraph state",
        "Persists thread state so approval and rejection can resume the same workflow.",
    ),
)


TOOL_EVIDENCE: dict[str, tuple[str, str]] = {
    "get_supply_chain_snapshot": (
        "Operational data",
        "shipments, parts, inventory, purchase_orders, suppliers",
    ),
    "search_supply_chain_knowledge": (
        "Atlas Vector Search",
        "knowledge_corpus",
    ),
    "recall_planner_memory": (
        "Planner memory",
        "agent_memories",
    ),
    "recall_prior_incidents": (
        "Prior incidents",
        "agent_episodes",
    ),
    "submit_action_for_approval": (
        "Approval draft",
        "action_drafts",
    ),
    "remember_resolution": (
        "Memory write",
        "agent_memories",
    ),
}


DEMO_PROMPTS: tuple[DemoPrompt, ...] = (
    DemoPrompt(
        "Late critical shipment",
        "Shipment SH-1043 for BRK-22 is 6 days late. What are my options?",
        "Prioritize recovery options with supporting evidence.",
    ),
    DemoPrompt(
        "Prior incident recall",
        "Have we handled a BRK-22 port delay before? What worked last time?",
        "Show long-term memory and prior incident retrieval.",
    ),
    DemoPrompt(
        "Planner memory",
        "Do I have any planner preferences relevant to premium freight?",
        "Show user-scoped memory stored and retrieved from MongoDB Atlas.",
    ),
    DemoPrompt(
        "Quality hold comparison",
        "Compare this CELL-9 quality hold with prior incidents and recommend next steps.",
        "Compare current disruption patterns against historical episodes.",
    ),
    DemoPrompt(
        "Premium freight decision",
        "Shipment SH-3110 is delayed. Do we need premium freight?",
        "Explain whether a state-changing action is justified.",
    ),
    DemoPrompt(
        "Full platform story",
        "For SH-1043, use live data, playbooks, planner memory, and prior incidents to recommend the lowest-risk action.",
        "Show operational data, vector search, memory, and agent reasoning together.",
    ),
    DemoPrompt(
        "Approval workflow",
        "Draft an approval request to expedite SH-1043 with premium freight because "
        "BRK-22 has under 3 days of cover.",
        "Demonstrate human-in-the-loop approval before action.",
    ),
)


def format_prompt_option(prompt: DemoPrompt) -> str:
    return prompt.label


def evidence_from_result(result: dict[str, Any]) -> list[dict[str, str]]:
    seen: set[str] = set()
    evidence: list[dict[str, str]] = []
    for tool_name in _tool_names_from_result(result):
        if tool_name in seen:
            continue
        seen.add(tool_name)
        label, source = TOOL_EVIDENCE.get(tool_name, ("Agent tool", tool_name))
        evidence.append({"capability": label, "source": source, "tool": tool_name})
    return evidence


def thread_state_summary(metadata: dict[str, Any]) -> dict[str, str]:
    pending = metadata.get("pending_approval")
    decision = metadata.get("decision")
    if pending:
        state = "Paused for approval"
    elif decision:
        state = f"Resumed with {decision}"
    else:
        state = "Completed response"
    return {
        "Thread": str(metadata.get("thread_id", "unknown")),
        "State": state,
        "Checkpoint": "MongoDBSaver",
    }


def mode_name(demo_mode: str) -> str:
    return "Atlas connected"


def mode_summary(demo_mode: str) -> str:
    return "Connected runtime using MongoDB Atlas, LangGraph state, and an LLM."


def hero_summary(demo_mode: str) -> str:
    return (
        "A MongoDB + LangChain demo: MongoDB Atlas stores operational data, "
        "vector-search knowledge, memory, checkpoints, and approval-gated action "
        "drafts while LangChain and LangGraph orchestrate the agent workflow."
    )


def mode_metrics(demo_mode: str) -> tuple[tuple[str, str], ...]:
    return (
        ("Data", "MongoDB Atlas"),
        ("Retrieval", "Atlas Vector Search"),
        ("State", "MongoDBSaver"),
        ("Memory", "MongoDBStore"),
    )


def workflow_intro(demo_mode: str) -> str:
    return (
        "This shows how MongoDB Atlas and LangChain work together: tools read Atlas data, "
        "Vector Search retrieves context, LangGraph checkpoints state, and human approval "
        "resumes the same workflow."
    )


def readiness_summary(checks: list[dict[str, Any]]) -> dict[str, int]:
    total = len(checks)
    passing = sum(1 for check in checks if check.get("ok"))
    return {"total": total, "passing": passing, "failing": total - passing}


def readiness_status(checks: list[dict[str, Any]]) -> str:
    summary = readiness_summary(checks)
    if summary["failing"] == 0:
        return "Ready"
    return f"Needs attention: {summary['failing']} check(s) failing"


def error_guidance(error_name: str, demo_mode: str) -> list[str]:
    guidance = ["Run `uv run supply-chain-agent validate` for safe readiness checks."]
    if "Authentication" in error_name or "Unauthorized" in error_name:
        guidance.append(
            "Check `LLM_API_KEY`, `LLM_BASE_URL`, and `LLM_API_KEY_HEADER` in `.env`."
        )
    elif "OperationFailure" in error_name:
        guidance.append(
            "Check Atlas Search / Vector Search indexes with "
            "`uv run supply-chain-agent validate`."
        )
    elif "ServerSelection" in error_name or "Connection" in error_name:
        guidance.append(
            "Check `MONGODB_URI`, Atlas network access, and your IP access list."
        )
    else:
        guidance.append(
            "If this happened during approval, reuse the same Thread ID that created the pending request."
        )
    return guidance


def _tool_names_from_result(result: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for message in result.get("messages", []):
        for call in _message_tool_calls(message):
            name = _tool_call_name(call)
            if name:
                names.append(name)
        name = _message_field(message, "name")
        if name and _message_field(message, "type") == "tool":
            names.append(str(name))
    for interrupt in result.get("__interrupt__", []):
        value = getattr(interrupt, "value", None)
        if value is None and isinstance(interrupt, dict):
            value = interrupt.get("value")
        if isinstance(value, dict):
            for request in value.get("action_requests", []):
                if isinstance(request, dict) and request.get("name"):
                    names.append(str(request["name"]))
    return names


def _message_tool_calls(message: Any) -> list[Any]:
    tool_calls = _message_field(message, "tool_calls")
    if isinstance(tool_calls, list):
        return tool_calls
    additional = _message_field(message, "additional_kwargs")
    if isinstance(additional, dict) and isinstance(additional.get("tool_calls"), list):
        return additional["tool_calls"]
    return []


def _tool_call_name(call: Any) -> str:
    if isinstance(call, dict):
        if call.get("name"):
            return str(call["name"])
        function = call.get("function")
        if isinstance(function, dict) and function.get("name"):
            return str(function["name"])
    return str(getattr(call, "name", "") or "")


def _message_field(message: Any, field: str) -> Any:
    value = getattr(message, field, None)
    if value is None and isinstance(message, dict):
        value = message.get(field)
    return value
