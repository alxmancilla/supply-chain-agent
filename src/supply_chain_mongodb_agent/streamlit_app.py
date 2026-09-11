import streamlit as st
from langgraph.types import Command

from supply_chain_mongodb_agent.agent import (
    build_agent,
    extract_latest_text,
    format_pending_approval,
)
from supply_chain_mongodb_agent.db import get_client
from supply_chain_mongodb_agent.doctor import doctor_report
from supply_chain_mongodb_agent.local_agent import approve_local_demo
from supply_chain_mongodb_agent.settings import get_settings
from supply_chain_mongodb_agent.workflow import workflow_diagram_dot, workflow_notes

st.set_page_config(page_title="Supply Chain Agent", page_icon="🚚")
st.title("🚚 Supply Chain Resolution Agent")
st.caption("MongoDB Atlas operational data + state + memory + auto-embedding + rerank")

settings = get_settings()
st.info(
    "Running in credential-free local demo mode. Set `DEMO_MODE=atlas` for MongoDB Atlas + LLM."
    if settings.demo_mode == "local"
    else "Running in connected Atlas/LLM mode."
)
ask_tab, workflow_tab, readiness_tab = st.tabs(["Ask Agent", "Workflow", "Readiness"])

with ask_tab:
    examples = [
        "Shipment SH-1043 for BRK-22 is 6 days late. What are my options?",
        "Have we handled a BRK-22 port delay before? What worked last time?",
        "Compare this CELL-9 quality hold with prior incidents and recommend next steps.",
        "Shipment SH-3110 is delayed. Do we need premium freight?",
        "Draft an approval request to expedite SH-1043 with premium freight because BRK-22 has under 3 days of cover.",
    ]
    example = st.selectbox("Try a demo query", examples)
    question = st.text_area("Ask about a disruption", example, height=110)
    thread_id = st.text_input("Thread ID", "demo-thread")

    if st.button("Ask agent"):
        spinner = "Reasoning with local sample data..." if settings.demo_mode == "local" else "Reasoning with MongoDB + LLM..."
        with st.spinner(spinner):
            client = None if settings.demo_mode == "local" else get_client(settings)
            try:
                agent = build_agent(client, settings)
                result = agent.invoke(
                    {"messages": [{"role": "user", "content": question}]},
                    config={"configurable": {"thread_id": thread_id}},
                )
                answer = extract_latest_text(result) or format_pending_approval(result)
                st.markdown(answer)
                with st.expander("Demo metadata"):
                    st.json({"mode": settings.demo_mode, "thread_id": thread_id, "db": settings.mongodb_db})
            except Exception as exc:  # noqa: BLE001 - UI boundary should show guided errors.
                st.error(f"Demo request failed: {exc.__class__.__name__}")
                st.caption("Run `uv run supply-chain-agent doctor` for non-sensitive readiness checks.")
            finally:
                if client is not None:
                    client.close()

    if st.button("Approve pending action"):
        spinner = "Recording local approval..." if settings.demo_mode == "local" else "Resuming persisted LangGraph checkpoint..."
        with st.spinner(spinner):
            client = None if settings.demo_mode == "local" else get_client(settings)
            try:
                if settings.demo_mode == "local":
                    result = approve_local_demo(thread_id)
                else:
                    agent = build_agent(client, settings)
                    result = agent.invoke(
                        Command(resume={"decisions": [{"type": "approve"}]}),
                        config={"configurable": {"thread_id": thread_id}},
                    )
                st.markdown(extract_latest_text(result) or format_pending_approval(result))
            except Exception as exc:  # noqa: BLE001 - UI boundary should show guided errors.
                st.error(f"Approval resume failed: {exc.__class__.__name__}")
                st.caption("Use the same thread ID that produced the pending approval.")
            finally:
                if client is not None:
                    client.close()

with workflow_tab:
    st.subheader("Agent workflow")
    st.graphviz_chart(workflow_diagram_dot(), width="stretch")
    for note in workflow_notes():
        st.markdown(f"- {note}")

with readiness_tab:
    st.subheader("Readiness checks")
    st.caption("Non-sensitive status only; secrets are never printed.")
    st.json(doctor_report(settings))
