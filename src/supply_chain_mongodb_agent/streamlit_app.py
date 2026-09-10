import streamlit as st

from supply_chain_mongodb_agent.agent import (
    build_agent,
    extract_latest_text,
    format_pending_approval,
)
from supply_chain_mongodb_agent.db import get_client
from supply_chain_mongodb_agent.doctor import doctor_report
from supply_chain_mongodb_agent.settings import get_settings

st.set_page_config(page_title="Supply Chain Agent", page_icon="🚚")
st.title("🚚 Supply Chain Resolution Agent")
st.caption("MongoDB Atlas operational data + state + memory + auto-embedding + rerank")

settings = get_settings()
st.info(
    "Running in credential-free local demo mode. Set `DEMO_MODE=atlas` for MongoDB Atlas + Grove."
    if settings.demo_mode == "local"
    else "Running in connected Atlas/Grove mode."
)
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
    spinner = "Reasoning with local sample data..." if settings.demo_mode == "local" else "Reasoning with MongoDB + Grove..."
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

with st.expander("Readiness checks"):
    st.json(doctor_report(settings))