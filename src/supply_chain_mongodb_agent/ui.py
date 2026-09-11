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