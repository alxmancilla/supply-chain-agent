import streamlit as st
from langgraph.types import Command

from supply_chain_mongodb_agent.agent import (
    build_agent,
    extract_latest_text,
    format_pending_approval,
)
from supply_chain_mongodb_agent.db import get_client, get_database
from supply_chain_mongodb_agent.doctor import doctor_report
from supply_chain_mongodb_agent.settings import get_settings
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
from supply_chain_mongodb_agent.workflow import workflow_diagram_dot

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
        .story-card {
            border: 1px solid #bae6fd;
            border-radius: 14px;
            padding: 0.85rem;
            background: #f0f9ff;
            min-height: 8rem;
        }
        .story-card strong { color: #075985; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _init_session_state() -> None:
    st.session_state.setdefault("last_answer", "")
    st.session_state.setdefault("last_error", "")
    st.session_state.setdefault("last_metadata", {})
    st.session_state.setdefault("last_evidence", [])
    st.session_state.setdefault("last_action_draft", {})


def _run_agent(question: str, thread_id: str) -> None:
    with st.spinner("Reasoning with MongoDB Atlas + LLM..."):
        client = get_client(settings)
        try:
            agent = build_agent(client, settings)
            result = agent.invoke(
                {"messages": [{"role": "user", "content": question}]},
                config={"configurable": {"thread_id": thread_id}},
            )
            st.session_state.last_answer = extract_latest_text(
                result
            ) or format_pending_approval(result)
            st.session_state.last_error = ""
            pending_approval = "Pending human approval" in st.session_state.last_answer
            st.session_state.last_metadata = {
                "mode": settings.demo_mode,
                "thread_id": thread_id,
                "database": settings.mongodb_db,
                "realm_id": settings.realm_id,
                "agent_id": settings.agent_id,
                "user_id": settings.user_id,
                "pending_approval": pending_approval,
            }
            st.session_state.last_evidence = evidence_from_result(result)
            st.session_state.last_action_draft = _latest_action_draft(client)
        except Exception as exc:  # noqa: BLE001 - UI boundary needs guided errors.
            st.session_state.last_answer = ""
            st.session_state.last_error = exc.__class__.__name__
        finally:
            if client is not None:
                client.close()


def _resume_action(thread_id: str, decision: str) -> None:
    decision_label = "approval" if decision == "approve" else "rejection"
    with st.spinner(
        f"Resuming persisted LangGraph checkpoint with {decision_label}..."
    ):
        client = get_client(settings)
        try:
            agent = build_agent(client, settings)
            result = agent.invoke(
                Command(resume={"decisions": [{"type": decision}]}),
                config={"configurable": {"thread_id": thread_id}},
            )
            st.session_state.last_answer = (
                extract_latest_text(result)
                or format_pending_approval(result)
                or f"{decision_label.title()} recorded for thread `{thread_id}`."
            )
            st.session_state.last_error = ""
            st.session_state.last_metadata = {
                "mode": settings.demo_mode,
                "thread_id": thread_id,
                "decision": decision,
                "pending_approval": False,
            }
            st.session_state.last_evidence = evidence_from_result(result)
            st.session_state.last_action_draft = _latest_action_draft(client)
        except Exception as exc:  # noqa: BLE001 - UI boundary needs guided errors.
            st.session_state.last_error = exc.__class__.__name__
        finally:
            if client is not None:
                client.close()


def _render_answer_panel() -> None:
    if st.session_state.last_error:
        st.error(f"Request failed: {st.session_state.last_error}")
        for guidance in error_guidance(st.session_state.last_error, settings.demo_mode):
            st.caption(guidance)
        return
    if not st.session_state.last_answer:
        st.info("Choose a scenario, then ask the agent to generate a recommendation.")
        return
    if "Pending human approval" in st.session_state.last_answer:
        st.warning("This response is paused for human approval.")
    else:
        st.success("Agent response ready")
    st.markdown(st.session_state.last_answer)
    _render_evidence_panel()


def _render_evidence_panel() -> None:
    with st.expander("Evidence and state", expanded=True):
        state_cols = st.columns(3)
        for column, (label, value) in zip(
            state_cols,
            thread_state_summary(st.session_state.last_metadata).items(),
            strict=True,
        ):
            column.metric(label, value)

        evidence = st.session_state.last_evidence
        if evidence:
            st.dataframe(evidence, width="stretch", hide_index=True)
        else:
            st.caption("No MongoDB-backed tool evidence was captured for this turn.")

        draft = st.session_state.last_action_draft
        if draft:
            st.markdown("**Latest approval draft**")
            st.json(draft)


def _latest_action_draft(client: object) -> dict[str, object]:
    db = get_database(client, settings)
    draft = db.action_drafts.find_one(
        {
            "realm_id": settings.realm_id,
            "agent_id": settings.agent_id,
            "user_id": settings.user_id,
        },
        projection={"_id": 0},
        sort=[("created_at", -1)],
    )
    if not draft:
        return {}
    return {key: _json_safe(value) for key, value in draft.items()}


def _json_safe(value: object) -> object:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


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
        return thread_id


settings = get_settings()
_inject_styles()
_init_session_state()
thread_id = _render_sidebar()

st.markdown(
    f"""
    <div class="hero-card">
      <span class="pill">{mode_name(settings.demo_mode)}</span>
      <span class="pill">MongoDB + LangChain</span>
      <span class="pill">Atlas-ready</span>
      <span class="pill">Human-in-the-loop</span>
      <h1>🚚 Supply Chain Resolution Agent</h1>
      <p class="muted">{hero_summary(settings.demo_mode)}</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("")
pillar_cols = st.columns(4)
for column, (title, body) in zip(pillar_cols, VALUE_PILLARS, strict=True):
    column.markdown(
        f"""
        <div class="story-card">
          <strong>{title}</strong><br />
          <span class="muted">{body}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.write("")
metric_cols = st.columns(4)
for column, (label, value) in zip(
    metric_cols, mode_metrics(settings.demo_mode), strict=True
):
    column.metric(label, value)

ask_tab, workflow_tab, readiness_tab = st.tabs(
    [
        "💬 Ask Agent",
        "🧭 Workflow",
        "✅ Readiness",
    ]
)

with ask_tab:
    st.subheader("Ask the agent")
    selected_prompt = st.selectbox(
        "Scenario",
        DEMO_PROMPTS,
        format_func=format_prompt_option,
    )
    question = st.text_area(
        "Question for the agent",
        selected_prompt.question,
        height=140,
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
        st.session_state.last_evidence = []
        st.session_state.last_action_draft = {}

    st.divider()
    _render_answer_panel()

with workflow_tab:
    st.subheader("How the agent works")
    st.info(workflow_intro(settings.demo_mode))
    st.graphviz_chart(workflow_diagram_dot(), width="stretch")

    role_cols = st.columns(2)
    role_cols[0].info(
        "**Agent frameworks**\n\n"
        "**LangChain:** turns MongoDB reads/writes into safe agent tools "
        "and connects the LLM.\n\n"
        "**LangGraph:** state transitions, checkpoints, interrupts.\n\n"
        "**Deep Agents:** planning and tool-use loop."
    )
    role_cols[1].info(
        "**MongoDB Atlas**\n\n"
        "Operational collections, Atlas Vector Search, MongoDBStore memory, "
        "MongoDBSaver checkpoints, and approval drafts."
    )

with readiness_tab:
    st.subheader("Readiness dashboard")
    st.caption(
        "Non-sensitive status only; secrets are never printed. `serve` runs this "
        "validation before startup."
    )
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
