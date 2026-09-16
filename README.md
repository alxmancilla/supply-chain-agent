# Supply Chain Resolution Agent

Customer-shareable demo showing best practices for a stateful supply-chain agent
with MongoDB operational data, agent memory, retrieval, and human approval.

This repo is intentionally demo-first. It is an **Atlas-only** showcase using
MongoDB Atlas, Atlas Vector Search automated embeddings, native `$rerank`,
MongoDB-backed LangGraph state, MongoDB-backed long-term memory, and a
configurable OpenAI-compatible LLM. If you are presenting the project, start
with `DEMO.md`.

## New to agents, MongoDB, or LangChain?

Think of this demo as a workflow that lets an AI assistant solve a supply-chain
disruption with guardrails:

- An **agent** is an LLM-driven workflow that can decide when to call tools,
  inspect evidence, and produce a recommendation.
- A **tool** is a safe function the agent can call, such as reading shipment
  status or drafting an approval request.
- **Retrieval** means finding the most relevant policies, playbooks, memories,
  or prior incidents before the agent answers.
- **Memory** means the agent can use prior planner preferences and resolved
  incidents instead of treating every question as brand new.
- **State** means the agent can pause and resume the same thread, which is what
  makes human approval possible.

The frameworks and database pieces have specific jobs:

- **MongoDB Atlas** stores operational data, knowledge, memories, checkpoints,
  and pending approval drafts in the connected demo.
- **Atlas Vector Search** helps retrieve relevant knowledge and prior incidents.
- **LangChain** provides the LLM and tool interfaces.
- **LangGraph** manages state, checkpoints, interrupts, and resume behavior.
- **Deep Agents** provides the planning and tool-use loop used by the agent.

## What it demonstrates

- Operational supply-chain data: suppliers, parts, inventory, shipments, POs.
- Agent tools that separate reads from state-changing actions.
- Tenant and actor scoping with `realm_id`, `agent_id`, and `user_id`.
- Human-in-the-loop approval for business-state changes.
- MongoDBSaver checkpoints for stateful LangGraph execution.
- MongoDBStore memory for long-term agent memory.
- Atlas Vector Search `autoEmbed` and native `$rerank`.

## Quickstart

Copy the example environment file:

```bash
uv sync
cp .env.example .env
```

Fill in the required Atlas and LLM values in `.env`. Keep real secrets in
`.env` only; `.env` should remain untracked.

- `MONGODB_URI`
- `MONGODB_DB`
- `LLM_API_KEY`
- `LLM_MODEL`
- `LLM_BASE_URL`, optional for providers that do not use the default OpenAI API

Then bootstrap data and indexes:

```bash
uv run supply-chain-agent doctor
uv run supply-chain-agent seed
uv run supply-chain-agent indexes
uv run supply-chain-agent doctor
```

`indexes` creates three Atlas Vector Search definitions for `autoEmbed`.
Native `$rerank` must also be enabled in Atlas Project Settings on MongoDB 8.3+.

The Atlas demo is **M0-compatible by default** because it creates three Vector
Search indexes, which fits the Free cluster's three Search / Vector Search index
limit. For smoother live demos, higher limits, and less resource contention,
**M10+ is still recommended**.

Run the guided walkthrough:

```bash
uv run supply-chain-agent demo
```

Ask your own question:

```bash
uv run supply-chain-agent ask "Shipment SH-1043 for BRK-22 is 6 days late. What are my options?"
```

Run the Streamlit UI:

```bash
uv run python -m streamlit run src/supply_chain_mongodb_agent/streamlit_app.py
```

Open the URL printed by Streamlit, usually `http://localhost:8501`.

The UI has three tabs:

- **Ask Agent**: run guided disruption scenarios and approve or reject pending actions.
- **Workflow**: explain the Atlas-connected agent lifecycle and supporting frameworks.
- **Readiness**: show non-sensitive Atlas setup checks.

## What to look at first

If you are new to agentic development, start with these files:

1. `src/supply_chain_mongodb_agent/seed.py`: inspect the sample business data,
   knowledge, memories, and prior incidents.
2. `src/supply_chain_mongodb_agent/tools.py`: see what the agent can
   read or draft.
3. `src/supply_chain_mongodb_agent/agent.py`: see how LangGraph, MongoDBSaver,
   MongoDBStore, tools, and the LLM are wired.
4. `src/supply_chain_mongodb_agent/streamlit_app.py`: inspect the small UI wrapper.

## LLM provider configuration

The connected agent uses `langchain-openai`, so any OpenAI-compatible endpoint is
easy to swap in:

```bash
LLM_PROVIDER=openai_compatible
LLM_API_KEY=<your-llm-api-key>
LLM_BASE_URL=https://your-provider.example/v1
LLM_MODEL=<your-model-name>
```

For gateways that expect API keys in a custom header instead of the standard
Authorization header, also set:

```bash
LLM_API_KEY_HEADER=api-key
LLM_USE_RESPONSES_API=true
```

## Human-in-the-loop approval

Try this in either CLI or Streamlit:

```bash
uv run supply-chain-agent ask "Draft an approval request to expedite SH-1043 with premium freight because BRK-22 has under 3 days of cover."
```

In Streamlit, keep the same Thread ID and click either:

- **Approve pending action** to continue with the drafted action.
- **Reject pending action** to resume without executing the drafted action.

In the CLI walkthrough, resume the same thread with approval:

```bash
uv run supply-chain-agent approve --thread-id demo-thread
```

Approval and rejection resume the persisted LangGraph checkpoint for the same
thread.

## Suggested demo queries

### Operational data + recommendations

- `Shipment SH-1043 for BRK-22 is 6 days late. What are my options?`
- `What is the risk for shipment SH-2048 and should we use the battery cells?`
- `Shipment SH-3110 is delayed. Do we need premium freight?`

### Knowledge, memory, and prior incidents

- `Find the policy for Tier-1 shortages with less than three days of cover.`
- `Which contract terms apply when SUP-BAT has a quality hold?`
- `What approved alternate exists for BRK-22? Cite the source IDs.`
- `Do I have any planner preferences relevant to premium freight?`
- `Have we handled a BRK-22 port delay before? What worked last time?`
- `Compare this CELL-9 quality hold with prior incidents and recommend next steps.`

### Cross-capability story

- `For SH-1043, use live data, playbooks, planner memory, and prior incidents to recommend the lowest-risk action.`
- `For SH-2048, explain the operational state, relevant SOP, similar episode, and whether approval is required.`

## Best-practice notes

- Atlas is the platform showcase: it demonstrates real MongoDB-backed state,
  memory, vector search, automated embeddings, and reranking.
- Seeded memories, episodes, and action drafts include tenant, agent, and user
  scope to model actor-aware isolation.
- The approval tool drafts actions instead of pretending to execute them.
- `doctor` reports non-sensitive readiness and never prints secrets.

## Troubleshooting quick guide

Start with:

```bash
uv run supply-chain-agent doctor
```

Common fixes:

- Missing LLM key: set `LLM_API_KEY` in `.env`.
- LLM gateway auth fails: check `LLM_BASE_URL`, `LLM_API_KEY_HEADER`, and `LLM_USE_RESPONSES_API`.
- MongoDB connection fails: check `MONGODB_URI`, Atlas network access, and the IP access list.
- No scoped demo data: run `uv run supply-chain-agent seed`.
- Missing or stale indexes: run `uv run supply-chain-agent indexes`, wait, then rerun `doctor`.
- Approval or rejection does not resume: use the same Thread ID that created the pending request.

## Tests

```bash
uv run python -m pytest
uv run python -m ruff check
```

Offline tests mock external services and do not require Atlas, Voyage, or LLM credentials.
