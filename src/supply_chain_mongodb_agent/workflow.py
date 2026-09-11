from supply_chain_mongodb_agent.settings import Settings


def workflow_diagram_dot(settings: Settings) -> str:
    mode_label = "Local deterministic path" if settings.demo_mode == "local" else "Atlas connected path"
    return f"""
digraph supply_chain_agent {{
  graph [rankdir=LR, bgcolor="transparent", pad="0.3", nodesep="0.5", ranksep="0.7"];
  node [shape=box, style="rounded,filled", color="#64748b", fillcolor="#f8fafc", fontname="Helvetica", fontsize=11];
  edge [color="#64748b", arrowsize="0.8", fontname="Helvetica", fontsize=10];

  user [label="User\nquestion", fillcolor="#dbeafe"];
  mode [label="Mode router\n{mode_label}", fillcolor="#e0e7ff"];
  local [label="Local agent\nseeded data + deterministic reasoning", fillcolor="#dcfce7"];
  atlas [label="LangGraph deep agent\nMongoDBSaver + MongoDBStore", fillcolor="#ede9fe"];
  ops [label="Operational data\nshipments, POs, inventory, suppliers", fillcolor="#fef3c7"];
  knowledge [label="Atlas Vector Search\nSOPs, contracts, playbooks", fillcolor="#ccfbf1"];
  memory [label="Scoped memory\nrealm_id + agent_id + user_id", fillcolor="#ccfbf1"];
  llm [label="Configured LLM\nreason + synthesize", fillcolor="#fae8ff"];
  approval [label="Human approval\ninterrupt before action", fillcolor="#fee2e2"];
  response [label="Final response\nrecommendation + evidence", fillcolor="#dbeafe"];

  user -> mode;
  mode -> local [label="DEMO_MODE=local"];
  mode -> atlas [label="DEMO_MODE=atlas"];
  local -> response;
  atlas -> ops;
  atlas -> knowledge;
  atlas -> memory;
  ops -> llm;
  knowledge -> llm;
  memory -> llm;
  llm -> approval [label="state-changing draft"];
  approval -> response [label="approve/resume"];
  llm -> response [label="read-only answer"];
}}
"""


def workflow_notes(settings: Settings) -> list[str]:
    if settings.demo_mode == "local":
        return [
            "Uses deterministic in-process sample data; no MongoDB, LLM, or network credentials are required.",
            "Simulates retrieval, prior incidents, planner memory, and human approval for safe workshops.",
            "Best path for prospects who want to clone and run immediately.",
        ]
    return [
        "Uses MongoDB Atlas collections for operational data, memory, checkpoints, and action drafts.",
        "Retrieves knowledge, memories, and prior incidents with Atlas Vector Search auto-embedding and rerank.",
        "Scopes memory/action data with realm_id, agent_id, and user_id before invoking the configured LLM.",
    ]