from supply_chain_mongodb_agent.ui import (
    DEMO_PROMPTS,
    error_guidance,
    format_prompt_option,
    hero_summary,
    mode_metrics,
    mode_name,
    mode_summary,
    readiness_status,
    readiness_summary,
    workflow_intro,
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
    assert mode_name("atlas") == "Atlas connected"
    assert "MongoDB Atlas" in mode_summary("atlas")
    assert "MongoDB Atlas" in hero_summary("atlas")
    assert "connected Atlas runtime" in workflow_intro("atlas")


def test_mode_metrics_describe_atlas_runtime() -> None:
    atlas_metrics = dict(mode_metrics("atlas"))

    assert atlas_metrics["Data"] == "MongoDB Atlas"
    assert atlas_metrics["Retrieval"] == "Atlas Vector Search"


def test_readiness_summary_and_status() -> None:
    checks = [
        {"name": "one", "ok": True, "detail": "ready"},
        {"name": "two", "ok": False, "detail": "missing"},
    ]

    assert readiness_summary(checks) == {"total": 2, "passing": 1, "failing": 1}
    assert readiness_status(checks) == "Needs attention: 1 check(s) failing"
    assert readiness_status(checks[:1]) == "Ready"


def test_error_guidance_points_to_common_atlas_fixes() -> None:
    auth_guidance = "\n".join(error_guidance("OpenAIAuthenticationError", "atlas"))
    index_guidance = "\n".join(error_guidance("OperationFailure", "atlas"))

    assert "doctor" in auth_guidance
    assert "LLM_API_KEY" in auth_guidance
    assert "indexes" in index_guidance
