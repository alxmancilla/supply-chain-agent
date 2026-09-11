# Demo Script

This project has two good demo paths:

- A **local beginner path** that needs no credentials and is safe for anyone to run.
- An **Atlas showcase path** that uses MongoDB Atlas, Atlas Vector Search, rerank, LangGraph state, memory, and a configured LLM.

## 1. Local Beginner Path

Use this path when someone is new to agentic development or just wants to see the workflow immediately.

```bash
uv sync
uv run supply-chain-agent doctor
uv run supply-chain-agent demo --local
```

What this shows:

- The agent reads operational supply-chain facts.
- It combines live-style data with policy/playbook context.
- It recalls a prior incident.
- It pauses before a state-changing action.
- It can resume a simulated approval.

Try the approval resume:

```bash
uv run supply-chain-agent approve --thread-id demo-thread
```

Ask a single question:

```bash
uv run supply-chain-agent ask "Shipment SH-3110 is delayed. Do we need premium freight?"
```

## 2. Atlas Showcase Path

Use this path when you want to show the real MongoDB value: operational data, state, memory, vector retrieval, and rerank.

Create your environment file:

```bash
cp .env.example .env
```

Set these values in `.env`:

```bash
DEMO_MODE=atlas
MONGODB_URI=<your-atlas-connection-string>
MONGODB_DB=supply_chain_agent
LLM_API_KEY=<your-llm-api-key>
LLM_MODEL=<your-model>
```

If your LLM provider uses a custom base URL or API-key header, also set:

```bash
LLM_BASE_URL=<your-provider-url>
LLM_API_KEY_HEADER=api-key
LLM_USE_RESPONSES_API=true
```

Prepare Atlas:

```bash
uv run supply-chain-agent doctor
uv run supply-chain-agent seed
uv run supply-chain-agent indexes
uv run supply-chain-agent doctor
```

If `doctor` says indexes are not ready yet, wait a minute and rerun it. Atlas Search indexes can exist before they are queryable.

Run the guided Atlas walkthrough:

```bash
uv run supply-chain-agent demo --thread-id atlas-demo-001
```

Approve the pending action:

```bash
uv run supply-chain-agent approve --thread-id atlas-demo-001
```

## 3. Streamlit Demo

Start the UI:

```bash
uv run python -m streamlit run src/supply_chain_mongodb_agent/streamlit_app.py
```

Demo flow:

1. Pick the late `SH-1043` example.
2. Ask the agent.
3. Pick the approval request example.
4. Ask the agent again.
5. Click **Approve pending action** using the same thread ID.
6. Open **Readiness checks** to show local or Atlas configuration status.

## 4. What Just Happened

In Atlas mode, the agent uses these pieces:

- `get_supply_chain_snapshot`: reads shipment, part, supplier, PO, and inventory data.
- `search_supply_chain_knowledge`: retrieves SOPs, contracts, and playbooks with Atlas Vector Search.
- `recall_planner_memory`: retrieves agent/user-scoped long-term memory.
- `recall_prior_incidents`: retrieves agent/user-scoped resolved incidents.
- `submit_action_for_approval`: drafts a state-changing action and pauses for human approval.
- `MongoDBSaver`: persists LangGraph thread state.
- `MongoDBStore`: persists long-term agent memory.

## Troubleshooting

Run this first:

```bash
uv run supply-chain-agent doctor
```

Common fixes:

- Missing LLM key: set `LLM_API_KEY` in `.env`.
- MongoDB connection fails: check `MONGODB_URI`, network access, and Atlas IP access list.
- No seed data: run `uv run supply-chain-agent seed`.
- Missing indexes: run `uv run supply-chain-agent indexes`.
- Indexes not ready: wait and rerun `uv run supply-chain-agent doctor`.
- Approval does not resume: use the same `--thread-id` that created the pending approval.
