from supply_chain_mongodb_agent.agent import (
    build_agent,
    extract_latest_text,
    format_pending_approval,
)
from supply_chain_mongodb_agent.doctor import doctor_ok, doctor_report
from supply_chain_mongodb_agent.llm import build_chat_model
from supply_chain_mongodb_agent.local_agent import approve_local_demo
from supply_chain_mongodb_agent.settings import Settings


def test_local_agent_answers_without_credentials() -> None:
    settings = Settings(demo_mode="local", llm_api_key=None, grove_api_key=None)
    agent = build_agent(None, settings)
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "Shipment SH-1043 for BRK-22 is late. What are my options?"}]},
        config={"configurable": {"thread_id": "t1"}},
    )
    answer = extract_latest_text(result)
    assert "Local demo mode" in answer
    assert "SH-1043" in answer
    assert "SOP-EXP-01" in answer or "AVL-BRK-22" in answer


def test_local_agent_formats_pending_approval() -> None:
    settings = Settings(demo_mode="local", llm_api_key=None, grove_api_key=None)
    agent = build_agent(None, settings)
    result = agent.invoke({"messages": [{"role": "user", "content": "Draft an approval request to expedite SH-1043"}]})
    formatted = format_pending_approval(result)
    assert "Pending human approval" in formatted
    assert "SH-1043" in formatted


def test_local_approval_resume_is_simulated() -> None:
    answer = extract_latest_text(approve_local_demo("abc"))
    assert "abc" in answer
    assert "Local demo approval" in answer


def test_local_doctor_is_ok_without_credentials() -> None:
    checks = doctor_report(Settings(demo_mode="local", llm_api_key=None, grove_api_key=None))
    assert doctor_ok(checks)
    assert {check["name"] for check in checks} >= {"demo_mode", "sample_data", "credentials"}


def test_placeholder_llm_key_is_not_configured() -> None:
    settings = Settings(demo_mode="atlas", llm_api_key="<your-llm-api-key>", grove_api_key=None)
    assert not settings.llm_api_key_configured
    try:
        build_chat_model(settings)
    except ValueError as exc:
        assert "LLM_API_KEY" in str(exc)
    else:
        raise AssertionError("placeholder LLM key should not build a chat model")


def test_llm_settings_support_openai_compatible_provider() -> None:
    settings = Settings(
        demo_mode="atlas",
        llm_api_key="test-key",
        llm_base_url="https://llm.example/v1/",
        llm_model="provider-model",
        llm_use_responses_api=False,
        grove_api_key=None,
    )
    assert settings.llm_api_key_configured
    assert settings.effective_llm_provider == "openai_compatible"
    assert settings.effective_llm_base_url == "https://llm.example/v1"
    assert settings.effective_llm_model == "provider-model"
    assert build_chat_model(settings).model_name == "provider-model"