from supply_chain_mongodb_agent.ui import (
    DEMO_PROMPTS,
    format_prompt_option,
    mode_name,
    mode_summary,
    readiness_status,
    readiness_summary,
)


def test_demo_prompts_include_approval_workflow() -> None:
    labels = [prompt.label for prompt in DEMO_PROMPTS]

    assert "Approval workflow" in labels
    assert any("approval" in prompt.intent.lower() for prompt in DEMO_PROMPTS)


def test_format_prompt_option_combines_label_and_intent() -> None:
    option = format_prompt_option(DEMO_PROMPTS[0])

    assert DEMO_PROMPTS[0].label in option
    assert DEMO_PROMPTS[0].intent in option


def test_mode_copy_is_demo_friendly() -> None:
    assert mode_name("local") == "Local demo"
    assert mode_name("atlas") == "Atlas connected"
    assert "Credential-free" in mode_summary("local")
    assert "MongoDB Atlas" in mode_summary("atlas")


def test_readiness_summary_and_status() -> None:
    checks = [
        {"name": "one", "ok": True, "detail": "ready"},
        {"name": "two", "ok": False, "detail": "missing"},
    ]

    assert readiness_summary(checks) == {"total": 2, "passing": 1, "failing": 1}
    assert readiness_status(checks) == "Needs attention: 1 check(s) failing"
    assert readiness_status(checks[:1]) == "Ready"