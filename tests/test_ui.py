from supply_chain_mongodb_agent.ui import (
    DEMO_PROMPTS,
    VALUE_PILLARS,
    error_guidance,
    evidence_from_result,
    format_prompt_option,
    hero_summary,
    mode_metrics,
    mode_name,
    mode_summary,
    readiness_status,
    readiness_summary,
    thread_state_summary,
    workflow_intro,
)


def test_demo_prompts_include_approval_workflow() -> None:
    labels = [prompt.label for prompt in DEMO_PROMPTS]

    assert "Approval workflow" in labels
    assert "Planner memory" in labels
    assert "Full platform story" in labels
    assert any("approval" in prompt.intent.lower() for prompt in DEMO_PROMPTS)


def test_demo_story_highlights_mongodb_langchain_value() -> None:
    pillar_text = "\n".join(f"{title}: {body}" for title, body in VALUE_PILLARS)

    assert "MongoDB Atlas" in pillar_text
    assert "Atlas Vector Search" in pillar_text
    assert "LangChain tools" in pillar_text
    assert "LangGraph state" in pillar_text


def test_format_prompt_option_uses_simple_label() -> None:
    option = format_prompt_option(DEMO_PROMPTS[0])

    assert option == DEMO_PROMPTS[0].label
    assert DEMO_PROMPTS[0].intent not in option


def test_evidence_from_result_summarizes_tool_calls() -> None:
    result = {
        "messages": [
            {
                "tool_calls": [
                    {"name": "get_supply_chain_snapshot"},
                    {"name": "recall_prior_incidents"},
                    {"name": "get_supply_chain_snapshot"},
                ]
            }
        ]
    }

    evidence = evidence_from_result(result)

    assert evidence == [
        {
            "capability": "Operational data",
            "source": "shipments, products, inventory, purchase_orders, manufacturers",
            "tool": "get_supply_chain_snapshot",
        },
        {
            "capability": "Prior incidents",
            "source": "agent_episodes",
            "tool": "recall_prior_incidents",
        },
    ]


def test_evidence_from_result_includes_approval_interrupts() -> None:
    result = {
        "__interrupt__": [
            {"value": {"action_requests": [{"name": "submit_action_for_approval"}]}}
        ]
    }

    assert evidence_from_result(result)[0]["source"] == "action_drafts"


def test_thread_state_summary_describes_checkpoint_state() -> None:
    assert thread_state_summary({"thread_id": "t-1"})["State"] == "Completed response"
    assert (
        thread_state_summary({"thread_id": "t-1", "pending_approval": True})["State"]
        == "Paused for approval"
    )
    assert (
        thread_state_summary({"thread_id": "t-1", "decision": "reject"})["State"]
        == "Resumed with reject"
    )


def test_mode_copy_is_demo_friendly() -> None:
    assert mode_name("atlas") == "Atlas connected"
    assert "MongoDB Atlas" in mode_summary("atlas")
    assert "MongoDB Atlas" in hero_summary("atlas")
    assert "healthcare distribution" in hero_summary("atlas")
    assert "MongoDB Atlas and LangChain" in workflow_intro("atlas")


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

    assert "validate" in auth_guidance
    assert "LLM_API_KEY" in auth_guidance
    assert "indexes" in index_guidance
