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
