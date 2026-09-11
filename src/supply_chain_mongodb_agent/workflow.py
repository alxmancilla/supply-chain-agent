def workflow_diagram_dot() -> str:
    return r"""
digraph supply_chain_agent {
  graph [rankdir=LR, bgcolor="transparent", pad="0.3", nodesep="0.5", ranksep="0.8", compound=true];
  node [shape=box, style="rounded,filled", color="#64748b", fillcolor="#f8fafc", fontname="Helvetica", fontsize=11];
  edge [color="#64748b", arrowsize="0.8", fontname="Helvetica", fontsize=10];

  subgraph cluster_states {
    label="Agent runtime states";
    color="#cbd5e1";
    style="rounded";

    request [label="1. Request received", fillcolor="#dbeafe"];
    load [label="2. Load thread state", fillcolor="#e0e7ff"];
    ops_state [label="3. Retrieve operational context", fillcolor="#fef3c7"];
    knowledge_state [label="4. Retrieve knowledge", fillcolor="#ccfbf1"];
    memory_state [label="5. Recall scoped memory", fillcolor="#ccfbf1"];
    incidents_state [label="6. Recall prior incidents", fillcolor="#ccfbf1"];
    reason [label="7. LLM reasoning", fillcolor="#fae8ff"];
    decision [label="8. Decision point", shape=diamond, fillcolor="#fef9c3"];
    pending [label="9. Pending human approval", fillcolor="#fee2e2"];
    resume [label="10. Approval resume", fillcolor="#ffedd5"];
    respond [label="11. Final response", fillcolor="#dbeafe"];
    persist [label="12. Persist state + memory", fillcolor="#e0e7ff"];
  }

  subgraph cluster_support {
    label="Framework + MongoDB support";
    color="#cbd5e1";
    style="rounded,dashed";

    deepagents [label="Deep Agents\nplanning + tool-use loop", fillcolor="#ede9fe"];
    langchain [label="LangChain\ntools + model interfaces", fillcolor="#ede9fe"];
    langgraph [label="LangGraph\nstate machine + interrupts", fillcolor="#ede9fe"];
    saver [label="MongoDBSaver\ncheckpoints", fillcolor="#dbeafe"];
    store [label="MongoDBStore\nlong-term memory", fillcolor="#dbeafe"];
    atlas_ops [label="MongoDB Atlas\nshipments, POs, inventory, suppliers", fillcolor="#fef3c7"];
    vector [label="Atlas Vector Search\nautoEmbed + rerank", fillcolor="#ccfbf1"];
    drafts [label="Action drafts\napproval records", fillcolor="#fee2e2"];
  }

  request -> load -> ops_state -> knowledge_state -> memory_state -> incidents_state -> reason -> decision;
  decision -> respond [label="read-only answer"];
  decision -> pending [label="state-changing draft"];
  pending -> resume -> respond -> persist;

  deepagents -> request [style=dashed];
  langchain -> ops_state [style=dashed];
  langchain -> reason [style=dashed];
  langgraph -> load [style=dashed];
  langgraph -> pending [style=dashed];
  langgraph -> resume [style=dashed];
  saver -> load [style=dashed];
  saver -> persist [style=dashed];
  store -> memory_state [style=dashed];
  store -> persist [style=dashed];
  atlas_ops -> ops_state [style=dashed];
  vector -> knowledge_state [style=dashed];
  vector -> memory_state [style=dashed];
  vector -> incidents_state [style=dashed];
  drafts -> pending [style=dashed];
}
"""


def workflow_notes() -> list[str]:
    return [
        "LangChain provides the tool/model interfaces used to connect the agent to MongoDB data and the configured LLM.",
        "LangGraph manages the runtime state transitions, MongoDB checkpoints, and human-approval interrupts/resume semantics.",
        "Deep Agents assembles the LangGraph agent loop that plans, calls tools, reasons over evidence, and produces the final answer.",
        "Uses MongoDB Atlas collections for operational data, memory, checkpoints, and action drafts.",
        "Retrieves knowledge, memories, and prior incidents with Atlas Vector Search auto-embedding and rerank.",
        "The state path branches at the decision point: read-only answers return immediately, while state-changing drafts pause for approval.",
        "Scopes memory/action data with realm_id, agent_id, and user_id before invoking the configured LLM.",
    ]