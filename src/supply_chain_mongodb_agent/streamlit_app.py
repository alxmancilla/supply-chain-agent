import streamlit as st
from langgraph.types import Command

from supply_chain_mongodb_agent.agent import (
    build_agent,
    extract_latest_text,
    format_pending_approval,
)
from supply_chain_mongodb_agent.db import get_client
from supply_chain_mongodb_agent.doctor import doctor_report
from supply_chain_mongodb_agent.local_agent import approve_local_demo, reject_local_demo
from supply_chain_mongodb_agent.settings import get_settings
from supply_chain_mongodb_agent.ui import (
    DEMO_PROMPTS,
    format_prompt_option,
    mode_name,
    mode_summary,
    readiness_status,
    readiness_summary,
)
from supply_chain_mongodb_agent.workflow import workflow_diagram_dot, workflow_notes

st.set_page_config(page_title="Supply Chain Agent", page_icon="🚚", layout="wide")


def _inject_styles() -> None:
    st.markdown(
        """
        <style>
        .hero-card {
            border: 1px solid #dbeafe;
            border-radius: 20px;
            padding: 1.4rem 1.6rem;
            background: linear-gradient(135deg, #eff6ff 0%, #f8fafc 58%, #ecfeff 100%);
        }
        .hero-card h1 { margin-bottom: 0.2rem; }
        .muted { color: #475569; }
        .pill {
            display: inline-block;
            border-radius: 999px;
            padding: 0.18rem 0.65rem;
            background: #dbeafe;
            color: #1e40af;
            font-size: 0.82rem;
            font-weight: 700;
            margin-right: 0.35rem;
        }
        .section-card {
            border: 1px solid #e2e8f0;
            border-radius: 16px;
            padding: 1rem;
            background: #ffffff;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _init_session_state() -> None:
    st.session_state.setdefault("last_answer", "")
    st.session_state.setdefault("last_error", "")
    st.session_state.setdefault("last_metadata", {})


def _run_agent(question: str, thread_id: str) -> None:
    spinner = (
        "Reasoning with local sample data..."
        if settings.demo_mode == "local"
        else "Reasoning with MongoDB Atlas + LLM..."
    )
    with st.spinner(spinner):
        client = None if settings.demo_mode == "local" else get_client(settings)
        try:
            agent = build_agent(client, settings)
            result = agent.invoke(
                {"messages": [{"role": "user", "content": question}]},
                config={"configurable": {"thread_id": thread_id}},
            )
            st.session_state.last_answer = (
                extract_latest_text(result) or format_pending_approval(result)
            )
            st.session_state.last_error = ""
            st.session_state.last_metadata = {
                "mode": settings.demo_mode,
                "thread_id": thread_id,
                "database": settings.mongodb_db,
                "realm_id": settings.realm_id,
                "agent_id": settings.agent_id,
                "user_id": settings.user_id,
            }
        except Exception as exc:  # noqa: BLE001 - UI boundary needs guided errors.
            st.session_state.last_answer = ""
            st.session_state.last_error = exc.__class__.__name__
        finally:
            if client is not None:
                client.close()


def _resume_action(thread_id: str, decision: str) -> None:
    local_result = approve_local_demo if decision == "approve" else reject_local_demo
    decision_label = "approval" if decision == "approve" else "rejection"
    spinner = (
        f"Recording local {decision_label}..."
        if settings.demo_mode == "local"
        else f"Resuming persisted LangGraph checkpoint with {decision_label}..."
    )
    with st.spinner(spinner):
        client = None if settings.demo_mode == "local" else get_client(settings)
        try:
            if settings.demo_mode == "local":
                result = local_result(thread_id)
            else:
                agent = build_agent(client, settings)
                result = agent.invoke(
                    Command(resume={"decisions": [{"type": decision}]}),
                    config={"configurable": {"thread_id": thread_id}},
                )
            st.session_state.last_answer = (
                extract_latest_text(result) or format_pending_approval(result)
                or f"{decision_label.title()} recorded for thread `{thread_id}`."
            )
            st.session_state.last_error = ""
            st.session_state.last_metadata = {
                "mode": settings.demo_mode,
                "thread_id": thread_id,
                "decision": decision,
            }
        except Exception as exc:  # noqa: BLE001 - UI boundary needs guided errors.
            st.session_state.last_error = exc.__class__.__name__
        finally:
            if client is not None:
                client.close()


def _render_answer_panel() -> None:
    if st.session_state.last_error:
        st.error(f"Request failed: {st.session_state.last_error}")
        st.caption("Run `uv run supply-chain-agent doctor` for safe readiness checks.")
        return
    if not st.session_state.last_answer:
        st.info("Choose a scenario, then ask the agent to generate a recommendation.")
        return
    if "Pending human approval" in st.session_state.last_answer:
        st.warning("This response is paused for human approval.")
    else:
        st.success("Agent response ready")
    st.markdown(st.session_state.last_answer)
    with st.expander("Run details"):
        st.json(st.session_state.last_metadata)


def _render_sidebar() -> str:
    with st.sidebar:
        st.header("Demo controls")
        st.metric("Runtime", mode_name(settings.demo_mode))
        st.caption(mode_summary(settings.demo_mode))
        thread_id = st.text_input("Thread ID", "demo-thread")

        st.divider()
        st.subheader("Scoped actor")
        st.caption(f"Realm: `{settings.realm_id}`")
        st.caption(f"Agent: `{settings.agent_id}`")
        st.caption(f"User: `{settings.user_id}`")

        st.divider()
        st.subheader("What to demo")
        st.caption("1. Ask a disruption question")
        st.caption("2. Inspect cited reasoning")
        st.caption("3. Trigger approval with the approval workflow prompt")
        st.caption("4. Approve or reject using the same thread ID")
        return thread_id


settings = get_settings()
_inject_styles()
_init_session_state()
thread_id = _render_sidebar()

st.markdown(
    f"""
    <div class="hero-card">
      <span class="pill">{mode_name(settings.demo_mode)}</span>
      <span class="pill">Atlas-ready</span>
      <span class="pill">Human-in-the-loop</span>
      <h1>🚚 Supply Chain Resolution Agent</h1>
      <p class="muted">
        A stateful agent demo for disruption analysis, evidence retrieval,
        memory recall, and approval-gated actions on MongoDB Atlas.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("")
metric_cols = st.columns(4)
metric_cols[0].metric("Operational data", "Shipments + inventory")
metric_cols[1].metric("Knowledge", "Vector Search")
metric_cols[2].metric("State", "LangGraph")
metric_cols[3].metric("Memory", "MongoDBStore")

ask_tab, workflow_tab, readiness_tab = st.tabs([
    "💬 Ask Agent",
    "🧭 Workflow",
    "✅ Readiness",
])

with ask_tab:
    st.subheader("Run a guided disruption scenario")
    selected_prompt = st.selectbox(
        "Scenario",
        DEMO_PROMPTS,
        format_func=format_prompt_option,
    )
    st.caption(selected_prompt.intent)
    question = st.text_area(
        "Question for the agent",
        selected_prompt.question,
        height=140,
        help="Use the approval workflow prompt to demonstrate pause/resume.",
    )
    ask_col, approve_col, reject_col, clear_col = st.columns([0.34, 0.26, 0.26, 0.14])
    if ask_col.button("Ask agent", type="primary", width="stretch"):
        _run_agent(question, thread_id)
    if approve_col.button("Approve pending action", width="stretch"):
        _resume_action(thread_id, "approve")
    if reject_col.button("Reject pending action", width="stretch"):
        _resume_action(thread_id, "reject")
    if clear_col.button("Clear", width="stretch"):
        st.session_state.last_answer = ""
        st.session_state.last_error = ""
        st.session_state.last_metadata = {}

    st.divider()
    _render_answer_panel()

with workflow_tab:
    st.subheader("How the agent works")
    st.caption(
        "The main path is shown first; framework and MongoDB services appear as "
        "supporting callouts so the workflow is easier to follow."
    )
    st.graphviz_chart(workflow_diagram_dot(), width="stretch")

    role_cols = st.columns(2)
    role_cols[0].info(
        "**Agent frameworks**\n\n"
        "**LangChain:** tool wrappers and model interfaces.\n\n"
        "**LangGraph:** state transitions, checkpoints, interrupts.\n\n"
        "**Deep Agents:** planning and tool-use loop."
    )
    role_cols[1].info("**MongoDB Atlas**\n\nOperational data, vector search, checkpoints, and memory.")

    with st.expander("Architecture notes", expanded=True):
        for note in workflow_notes():
            st.markdown(f"- {note}")

with readiness_tab:
    st.subheader("Readiness dashboard")
    st.caption("Non-sensitive status only; secrets are never printed.")
    checks = doctor_report(settings)
    summary = readiness_summary(checks)

    status_cols = st.columns(3)
    status_cols[0].metric("Status", readiness_status(checks))
    status_cols[1].metric("Passing checks", summary["passing"])
    status_cols[2].metric("Failing checks", summary["failing"])

    for check in checks:
        icon = "✅" if check["ok"] else "⚠️"
        with st.container(border=True):
            st.markdown(f"{icon} **{check['name']}**")
            st.caption(check["detail"])

    with st.expander("Raw readiness payload"):
        st.json(checks)
