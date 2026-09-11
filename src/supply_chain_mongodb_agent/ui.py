from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DemoPrompt:
    label: str
    question: str
    intent: str


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
        "Approval workflow",
        "Draft an approval request to expedite SH-1043 with premium freight because "
        "BRK-22 has under 3 days of cover.",
        "Demonstrate human-in-the-loop approval before action.",
    ),
)


def format_prompt_option(prompt: DemoPrompt) -> str:
    return f"{prompt.label} — {prompt.intent}"


def mode_name(demo_mode: str) -> str:
    return "Local demo" if demo_mode == "local" else "Atlas connected"


def mode_summary(demo_mode: str) -> str:
    if demo_mode == "local":
        return "Credential-free deterministic walkthrough using bundled sample data."
    return "Connected runtime using MongoDB Atlas, LangGraph state, and an LLM."


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
    guidance = ["Run `uv run supply-chain-agent doctor` for safe readiness checks."]
    if demo_mode == "local":
        guidance.append("Local mode should not require Atlas or LLM credentials; retry from a fresh thread ID.")
        return guidance
    if "Authentication" in error_name or "Unauthorized" in error_name:
        guidance.append("Check `LLM_API_KEY`, `LLM_BASE_URL`, and `LLM_API_KEY_HEADER` in `.env`.")
    elif "OperationFailure" in error_name:
        guidance.append("Check Atlas Search / Vector Search indexes with `uv run supply-chain-agent indexes`.")
    elif "ServerSelection" in error_name or "Connection" in error_name:
        guidance.append("Check `MONGODB_URI`, Atlas network access, and your IP access list.")
    else:
        guidance.append("If this happened during approval, reuse the same Thread ID that created the pending request.")
    return guidance
