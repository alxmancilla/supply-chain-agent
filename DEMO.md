# Demo Script

This is an **Atlas-only** healthcare distribution demo path that uses MongoDB
Atlas, Atlas Vector Search, rerank, LangGraph state, memory, and a configured LLM.

## What You Are About to Show

In plain English, this demo shows an AI agent solving a healthcare distribution
disruption:

1. A user asks about a late shipment, allocation shortage, or cold-chain hold.
2. The agent checks operational facts such as shipments, inventory, manufacturers/distribution partners, and POs.
3. It retrieves relevant policies, playbooks, memories, and prior incidents.
4. It recommends a next step with supporting evidence.
5. If the next step changes business state, it drafts the action and pauses for human approval.

The story is McKesson-style healthcare distribution, but it intentionally avoids
PHI, patient-specific details, and clinical recommendations. The agent supports
operations decisions; humans remain responsible for final actions.

MongoDB matters because the connected demo uses it for live-style business data,
retrieval, long-term memory, LangGraph checkpoints, and pending approval records.
LangChain connects the agent to tools and the LLM. LangGraph keeps the workflow
stateful and resumable.

## 5-Minute Presenter Flow

1. Start with **Readiness** to show Atlas data, LLM configuration, and the three M0-compatible Vector Search indexes are ready.
2. Choose **Late critical shipment** to show the agent grounding its answer in operational MongoDB collections.
3. Choose **Full platform story** to show operational data, playbooks, planner memory, prior incidents, and LLM reasoning working together.
4. Choose **Planner memory** or **Prior incident recall** to make memory easy to explain.
5. Choose **Approval workflow**, then approve or reject using the same Thread ID to show MongoDB-backed LangGraph checkpoints.
6. Open **Workflow** to explain how MongoDB Atlas, LangChain, LangGraph, and Deep Agents fit together.
7. Close with the platform message: MongoDB stores data, vector-search context, memory, checkpoints, and approval records for the agent.

## 1. Atlas Showcase Path

Use this path when you want to show the real MongoDB value: operational data, state, memory, vector retrieval, and rerank.

Atlas mode is **M0-compatible by default** because it creates three Vector
Search indexes, which fits the Free cluster's three Search / Vector Search index
limit. For smoother live demos, higher limits, and less resource contention,
**M10+ is still recommended**.

Create your environment file:

```bash
cp .env.example .env
```

Set these values in `.env`:

```bash
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
uv run supply-chain-agent validate
```

`validate` seeds the scoped demo data, ensures the three M0-compatible Vector
Search indexes, and reruns readiness checks without printing secrets. If indexes
are not ready yet, wait a minute and rerun it. Atlas Search indexes can exist
before they are queryable.

Run the guided Atlas walkthrough:

```bash
uv run supply-chain-agent demo --thread-id atlas-demo-001
```

Approve the pending action from the CLI walkthrough. Streamlit demonstrates both
approval and rejection; the CLI walkthrough demonstrates approval resume.

```bash
uv run supply-chain-agent approve --thread-id atlas-demo-001
```

## 2. Streamlit Demo

Start the UI:

```bash
uv run supply-chain-agent serve --wait-indexes-seconds 300
```

Use `serve` for every backend restart. It runs the Atlas validation task before
Streamlit starts, so the demo verifies data and indexes each time.

Demo flow:

1. Open **Readiness** and confirm the validation checks are green.
2. Open **Ask Agent** and choose scenarios from the simple picker.
3. Ask **Late critical shipment** to show operational data grounding.
4. Ask **Full platform story** to show retrieval, memory, and reasoning together.
5. Ask **Approval workflow**, then click **Approve pending action** or **Reject pending action** using the same Thread ID.
6. Open **Workflow** to explain LangChain, LangGraph, Deep Agents, and MongoDB Atlas.
7. Close by naming the MongoDB benefits: operational data, vector search, memory, checkpoints, and approval history in Atlas.

## 3. What Just Happened

In Atlas mode, the agent uses these pieces:

- `get_supply_chain_snapshot`: reads shipment, product, manufacturer/distribution partner, PO, and inventory data.
- `search_supply_chain_knowledge`: retrieves SOPs, contracts, and playbooks with Atlas Vector Search.
- `recall_planner_memory`: retrieves agent/user-scoped long-term memory.
- `recall_prior_incidents`: retrieves agent/user-scoped resolved incidents.
- `submit_action_for_approval`: drafts a state-changing action and pauses for human approval.
- `MongoDBSaver`: persists LangGraph thread state.
- `MongoDBStore`: persists long-term agent memory.
- The Streamlit UI can resume the pending action with approval or rejection.

## Troubleshooting

Run this first:

```bash
uv run supply-chain-agent validate
```

Common fixes:

- Missing LLM key: set `LLM_API_KEY` in `.env`.
- MongoDB connection fails: check `MONGODB_URI`, network access, and Atlas IP access list.
- No seed data: run `uv run supply-chain-agent validate`.
- Missing indexes: run `uv run supply-chain-agent validate`.
- Indexes not ready: wait and rerun `uv run supply-chain-agent validate`.
- Approval/rejection does not resume: use the same thread ID that created the pending approval.
