def workflow_diagram_dot() -> str:
    return r"""
digraph supply_chain_agent {
  graph [rankdir=TB, bgcolor="transparent", pad="0.25", nodesep="0.35", ranksep="0.55", compound=true, splines=ortho];
  node [shape=box, style="rounded,filled", color="#94a3b8", fillcolor="#f8fafc", fontname="Helvetica", fontsize=11, margin="0.14,0.08"];
  edge [color="#2563eb", arrowsize="0.75", fontname="Helvetica", fontsize=10, penwidth=2];

  title [label=<<B>Atlas-only supply-chain resolution agent</B><BR/><FONT POINT-SIZE="9">MongoDB Atlas + LangGraph + Deep Agents + OpenAI-compatible LLM</FONT>>, shape=plain, fontsize=14];

  subgraph cluster_entry {
    label="1. Demo entry + setup";
    color="#bfdbfe";
    fillcolor="#eff6ff";
    style="rounded,filled";

    entry [label=<<B>Streamlit UI / CLI</B><BR/><FONT POINT-SIZE="9">Ask, approve, reject, inspect readiness</FONT>>, fillcolor="#dbeafe"];
    config [label=<<B>Required Atlas + LLM config</B><BR/><FONT POINT-SIZE="9">MONGODB_URI + LLM_API_KEY</FONT>>, fillcolor="#e0e7ff"];
    bootstrap [label=<<B>Bootstrap once</B><BR/><FONT POINT-SIZE="9">seed data + 3 Vector Search indexes</FONT>>, fillcolor="#ccfbf1"];
    doctor [label=<<B>Readiness checks</B><BR/><FONT POINT-SIZE="9">Non-sensitive setup status</FONT>>, fillcolor="#fef9c3"];
  }

  subgraph cluster_runtime {
    label="2. LangGraph agent runtime — main path";
    color="#bfdbfe";
    fillcolor="#eff6ff";
    style="rounded,filled";

    request [label=<<B>Request received</B><BR/><FONT POINT-SIZE="9">Disruption question or action request</FONT>>, fillcolor="#dbeafe"];
    load [label=<<B>Load thread checkpoint</B><BR/><FONT POINT-SIZE="9">MongoDBSaver resumes conversation state</FONT>>, fillcolor="#e0e7ff"];
    context [label=<<B>Gather scoped context</B><BR/><FONT POINT-SIZE="9">Ops data + policy + memory + episodes</FONT>>, fillcolor="#ccfbf1"];
    reason [label=<<B>Reason with LLM</B><BR/><FONT POINT-SIZE="9">Deep Agents plans and uses tools</FONT>>, fillcolor="#fae8ff"];
    decision [label=<<B>Decision point</B><BR/><FONT POINT-SIZE="9">Answer now or draft an action?</FONT>>, shape=diamond, fillcolor="#fef9c3", margin="0.18,0.08"];
    answer [label=<<B>Read-only answer</B><BR/><FONT POINT-SIZE="9">Recommendation with evidence</FONT>>, fillcolor="#dbeafe"];
    draft [label=<<B>Draft action</B><BR/><FONT POINT-SIZE="9">Premium freight / supplier escalation</FONT>>, fillcolor="#fee2e2"];
    approval [label=<<B>Human approval interrupt</B><BR/><FONT POINT-SIZE="9">Thread pauses before business-state change</FONT>>, fillcolor="#fecaca"];
    resume [label=<<B>Resume same thread</B><BR/><FONT POINT-SIZE="9">Approve or reject decision</FONT>>, fillcolor="#ffedd5"];
    persist [label=<<B>Persist outcome</B><BR/><FONT POINT-SIZE="9">Checkpoint + memory + action history</FONT>>, fillcolor="#e0e7ff"];
  }

  subgraph cluster_atlas {
    label="3. MongoDB Atlas services";
    color="#bbf7d0";
    fillcolor="#f0fdf4";
    style="rounded,filled";

    ops [label=<<B>Operational collections</B><BR/><FONT POINT-SIZE="9">shipments, inventory, suppliers</FONT>>, fillcolor="#dcfce7"];
    knowledge [label=<<B>Atlas Vector Search</B><BR/><FONT POINT-SIZE="9">autoEmbed knowledge + native rerank</FONT>>, fillcolor="#ccfbf1"];
    memory [label=<<B>MongoDBStore memory</B><BR/><FONT POINT-SIZE="9">agent_memories + agent_episodes</FONT>>, fillcolor="#dcfce7"];
    checkpoints [label=<<B>MongoDBSaver checkpoints</B><BR/><FONT POINT-SIZE="9">Durable LangGraph thread state</FONT>>, fillcolor="#e0e7ff"];
    actions [label=<<B>Action drafts</B><BR/><FONT POINT-SIZE="9">Approval records and outcomes</FONT>>, fillcolor="#fee2e2"];
    scope [label=<<B>Scoped data boundary</B><BR/><FONT POINT-SIZE="9">realm_id + agent_id + user_id</FONT>>, fillcolor="#fef3c7"];
  }

  subgraph cluster_frameworks {
    label="4. Framework layer";
    color="#cbd5e1";
    fillcolor="#f8fafc";
    style="rounded,filled,dashed";

    langchain [label=<<B>LangChain</B><BR/><FONT POINT-SIZE="9">Tools + model interfaces</FONT>>, fillcolor="#ede9fe"];
    langgraph [label=<<B>LangGraph</B><BR/><FONT POINT-SIZE="9">State machine + interrupts</FONT>>, fillcolor="#ede9fe"];
    deepagents [label=<<B>Deep Agents</B><BR/><FONT POINT-SIZE="9">Planning + tool-use loop</FONT>>, fillcolor="#ede9fe"];
  }

  legend [label="Solid blue arrows = primary runtime flow\nDashed gray arrows = setup, framework, or Atlas support", shape=note, fillcolor="#ffffff", color="#cbd5e1", fontsize=10];

  title -> entry;
  config -> entry [style=dashed, color="#94a3b8", penwidth=1];
  bootstrap -> entry [style=dashed, color="#94a3b8", penwidth=1];
  doctor -> entry [style=dashed, color="#94a3b8", penwidth=1];
  entry -> request;
  request -> load -> context -> reason -> decision;
  decision -> answer [label="read-only"];
  decision -> draft [label="needs approval"];
  draft -> approval -> resume -> persist;
  answer -> persist;

  checkpoints -> load [style=dashed, color="#94a3b8", penwidth=1];
  ops -> context [style=dashed, color="#94a3b8", penwidth=1];
  knowledge -> context [style=dashed, color="#94a3b8", penwidth=1];
  memory -> context [style=dashed, color="#94a3b8", penwidth=1];
  scope -> context [style=dashed, color="#94a3b8", penwidth=1];
  actions -> draft [style=dashed, color="#94a3b8", penwidth=1];
  persist -> checkpoints [style=dashed, color="#94a3b8", penwidth=1];
  persist -> memory [style=dashed, color="#94a3b8", penwidth=1];
  persist -> actions [style=dashed, color="#94a3b8", penwidth=1];

  langchain -> reason [style=dashed, color="#94a3b8", penwidth=1];
  langchain -> context [style=dashed, color="#94a3b8", penwidth=1];
  deepagents -> reason [style=dashed, color="#94a3b8", penwidth=1];
  langgraph -> load [style=dashed, color="#94a3b8", penwidth=1];
  langgraph -> approval [style=dashed, color="#94a3b8", penwidth=1];
  langgraph -> resume [style=dashed, color="#94a3b8", penwidth=1];

  legend -> persist [style=dashed, color="#cbd5e1", penwidth=1];
}
"""


def workflow_notes() -> list[str]:
    return [
        "The workflow is Atlas-only: Streamlit and the CLI always use MongoDB Atlas plus the configured OpenAI-compatible LLM.",
        "Setup is separated from runtime: configure Atlas/LLM credentials, seed data, create three M0-compatible Vector Search indexes, then run readiness checks.",
        "The solid blue path shows the durable LangGraph thread lifecycle from request, checkpoint load, context gathering, reasoning, decision point, and persistence.",
        "Read-only questions return an evidence-backed answer; state-changing recommendations draft an action and pause at a human approval interrupt.",
        "Approval and rejection both resume the same persisted LangGraph thread through MongoDBSaver checkpoints.",
        "MongoDB Atlas stores operational data, Atlas Vector Search knowledge, MongoDBStore memory, prior episodes, checkpoints, and action drafts.",
        "LangChain provides tool/model interfaces, LangGraph handles state and interrupts, and Deep Agents drives the planning/tool-use loop.",
        "All memory and action data is scoped with realm_id, agent_id, and user_id before invoking the configured LLM.",
    ]
