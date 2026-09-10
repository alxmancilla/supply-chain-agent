from supply_chain_mongodb_agent.agent import (
    extract_latest_text,
    format_pending_approval,
)


class Msg:
    content = "hello"


def test_extract_latest_text_from_message_object() -> None:
    assert extract_latest_text({"messages": [Msg()]}) == "hello"


def test_extract_latest_text_from_dict_message() -> None:
    assert extract_latest_text({"messages": [{"content": "hi"}]}) == "hi"


def test_extract_latest_text_skips_encrypted_reasoning_items() -> None:
    result = {"messages": [{"content": [
        {"type": "reasoning", "encrypted_content": "redacted"},
        {"type": "output_text", "text": "visible answer"},
    ]}]}
    assert extract_latest_text(result) == "visible answer"


def test_format_pending_approval() -> None:
    class Interrupt:
        def __init__(self) -> None:
            self.value = {
                "action_requests": [{
                    "name": "submit_action_for_approval",
                    "args": {
                        "action_type": "EXPEDITE",
                        "shipment_id": "SH-1",
                        "rationale": "low cover",
                        "estimated_cost": 10,
                    },
                }]
            }

    formatted = format_pending_approval({"__interrupt__": [Interrupt()]})
    assert "Pending human approval" in formatted
    assert "SH-1" in formatted


def test_format_pending_approval_supports_dict_interrupts() -> None:
    formatted = format_pending_approval({"__interrupt__": [{"value": {"action_requests": [{"name": "submit_action_for_approval", "args": {"shipment_id": "SH-2"}}]}}]})
    assert "Pending human approval" in formatted
    assert "SH-2" in formatted