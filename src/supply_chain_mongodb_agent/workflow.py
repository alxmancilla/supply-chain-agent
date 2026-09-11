def workflow_diagram_dot() -> str:
    return """
digraph supply_chain_agent {
  graph [rankdir=LR, bgcolor="transparent", pad="0.3", nodesep="0.5", ranksep="0.7"];
  node [shape=box, style="rounded,filled", color="#64748b", fillcolor="#f8fafc", fontname="Helvetica", fontsize=11];
  edge [color="#64748b", arrowsize="0.8", fontname="Helvetica", fontsize=10];

  user [label="User\nquestion", fillcolor="#dbeafe"];
  atlas [label="Atlas connected agent\nLangGraph + Deep Agents", fillcolor="#ede9fe"];
  state [label="MongoDB state\nMongoDBSaver + MongoDBStore", fillcolor="#e0e7ff"];
  ops [label="Operational data\nshipments, POs, inventory, suppliers", fillcolor="#fef3c7"];
  knowledge [label="Atlas Vector Search\nSOPs, contracts, playbooks", fillcolor="#ccfbf1"];
  memory [label="Scoped memory\nrealm_id + agent_id + user_id", fillcolor="#ccfbf1"];
  llm [label="Configured LLM\nreason + synthesize", fillcolor="#fae8ff"];
  approval [label="Human approval\ninterrupt before action", fillcolor="#fee2e2"];
  response [label="Final response\nrecommendation + evidence", fillcolor="#dbeafe"];

  user -> atlas;
  atlas -> state;
  atlas -> ops;
  atlas -> knowledge;
  atlas -> memory;
  state -> llm;
  ops -> llm;
  knowledge -> llm;
  memory -> llm;
  llm -> approval [label="state-changing draft"];
  approval -> response [label="approve/resume"];
  llm -> response [label="read-only answer"];
}
"""


def workflow_notes() -> list[str]:
    return [
        "LangChain provides the tool/model interfaces used to connect the agent to MongoDB data and the configured LLM.",
        "LangGraph manages stateful execution, checkpoints, and human-approval interrupts/resume semantics.",
        "Deep Agents assembles the LangGraph agent loop that plans, calls tools, reasons over evidence, and produces the final answer.",
        "Uses MongoDB Atlas collections for operational data, memory, checkpoints, and action drafts.",
        "Retrieves knowledge, memories, and prior incidents with Atlas Vector Search auto-embedding and rerank.",
        "Scopes memory/action data with realm_id, agent_id, and user_id before invoking the configured LLM.",
    ]