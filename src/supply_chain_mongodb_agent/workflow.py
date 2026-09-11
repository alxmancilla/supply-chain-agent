def workflow_diagram_dot() -> str:
    return r"""
digraph supply_chain_agent {
  graph [rankdir=LR, bgcolor="transparent", pad="0.25", nodesep="0.45", ranksep="0.8", compound=true, splines=polyline];
  node [shape=box, style="rounded,filled", color="#94a3b8", fillcolor="#f8fafc", fontname="Helvetica", fontsize=11, margin="0.12,0.08"];
  edge [color="#2563eb", arrowsize="0.8", fontname="Helvetica", fontsize=10, penwidth=2];

  subgraph cluster_states {
    label="Agent runtime states — primary path";
    color="#bfdbfe";
    fillcolor="#eff6ff";
    style="rounded,filled";

    request [label=<<B>1. Request received</B><BR/><FONT POINT-SIZE="9">User asks about a disruption</FONT>>, fillcolor="#dbeafe"];
    load [label=<<B>2. Load thread state</B><BR/><FONT POINT-SIZE="9">Resume context from MongoDBSaver</FONT>>, fillcolor="#e0e7ff"];
    context [label=<<B>3. Gather context</B><BR/><FONT POINT-SIZE="9">Ops data + knowledge + memory</FONT>>, fillcolor="#ccfbf1"];
    reason [label=<<B>4. Reason with LLM</B><BR/><FONT POINT-SIZE="9">Synthesize facts and evidence</FONT>>, fillcolor="#fae8ff"];
    decision [label=<<B>5. Decision point</B><BR/><FONT POINT-SIZE="9">Answer or propose action?</FONT>>, shape=diamond, fillcolor="#fef9c3", margin="0.18,0.08"];
    answer [label=<<B>6A. Read-only answer</B><BR/><FONT POINT-SIZE="9">Return recommendation + citations</FONT>>, fillcolor="#dbeafe"];
    draft [label=<<B>6B. Draft action</B><BR/><FONT POINT-SIZE="9">Create pending approval record</FONT>>, fillcolor="#fee2e2"];
    approval [label=<<B>7. Pending human approval</B><BR/><FONT POINT-SIZE="9">LangGraph interrupt pauses thread</FONT>>, fillcolor="#fecaca"];
    resume [label=<<B>8. Approval resume</B><BR/><FONT POINT-SIZE="9">Continue same thread after approval</FONT>>, fillcolor="#ffedd5"];
    persist [label=<<B>9. Persist outcome</B><BR/><FONT POINT-SIZE="9">Checkpoint + memory/action history</FONT>>, fillcolor="#e0e7ff"];
  }

  subgraph cluster_support {
    label="Framework + MongoDB support — how each state is powered";
    color="#cbd5e1";
    fillcolor="#f8fafc";
    style="rounded,filled,dashed";

    deepagents [label=<<B>Deep Agents</B><BR/><FONT POINT-SIZE="9">Planning + tool-use loop</FONT>>, fillcolor="#ede9fe"];
    langchain [label=<<B>LangChain</B><BR/><FONT POINT-SIZE="9">Tools + model interfaces</FONT>>, fillcolor="#ede9fe"];
    langgraph [label=<<B>LangGraph</B><BR/><FONT POINT-SIZE="9">State machine + interrupts</FONT>>, fillcolor="#ede9fe"];
    mongodb [label=<<B>MongoDB Atlas</B><BR/><FONT POINT-SIZE="9">Ops data + action drafts</FONT><BR/><FONT POINT-SIZE="9">MongoDBSaver checkpoints + MongoDBStore memory</FONT>>, fillcolor="#dcfce7"];
    vector [label=<<B>Atlas Vector Search</B><BR/><FONT POINT-SIZE="9">autoEmbed + rerank</FONT>>, fillcolor="#ccfbf1"];
    scope [label=<<B>Scoped data boundary</B><BR/><FONT POINT-SIZE="9">realm_id + agent_id + user_id</FONT>>, fillcolor="#fef3c7"];
  }

  legend [label="Solid blue arrows = agent state transitions\nDashed gray arrows = supporting framework/data services", shape=note, fillcolor="#ffffff", color="#cbd5e1", fontsize=10];

  request -> load -> context -> reason -> decision;
  decision -> answer [label="read-only"];
  decision -> draft [label="needs approval"];
  draft -> approval -> resume -> persist;
  answer -> persist;

  deepagents -> request [style=dashed, color="#94a3b8", penwidth=1];
  langchain -> context [style=dashed, color="#94a3b8", penwidth=1];
  langchain -> reason [style=dashed, color="#94a3b8", penwidth=1];
  langgraph -> load [style=dashed, color="#94a3b8", penwidth=1];
  langgraph -> approval [style=dashed, color="#94a3b8", penwidth=1];
  langgraph -> resume [style=dashed, color="#94a3b8", penwidth=1];
  mongodb -> load [style=dashed, color="#94a3b8", penwidth=1];
  mongodb -> context [style=dashed, color="#94a3b8", penwidth=1];
  mongodb -> persist [style=dashed, color="#94a3b8", penwidth=1];
  vector -> context [style=dashed, color="#94a3b8", penwidth=1];
  scope -> context [style=dashed, color="#94a3b8", penwidth=1];
}
"""


def workflow_notes() -> list[str]:
    return [
        "LangChain provides the tool/model interfaces used to connect the agent to MongoDB data and the configured LLM.",
        "LangGraph manages the runtime state transitions, MongoDB checkpoints, and human-approval interrupts/resume semantics.",
        "Deep Agents assembles the LangGraph agent loop that plans, calls tools, reasons over evidence, and produces the final answer.",
        "The diagram emphasizes the main state path first; supporting framework and MongoDB services appear as dashed callouts.",
        "Uses MongoDB Atlas collections for operational data, memory, checkpoints, and action drafts.",
        "Retrieves knowledge, memories, and prior incidents with Atlas Vector Search auto-embedding and rerank.",
        "The state path branches at the decision point: read-only answers return immediately, while state-changing drafts pause for approval.",
        "Scopes memory/action data with realm_id, agent_id, and user_id before invoking the configured LLM.",
    ]