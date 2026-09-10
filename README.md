# Supply Chain Resolution Agent

Customer-shareable demo showing best practices for a stateful supply-chain agent
with MongoDB operational data, agent memory, retrieval, and human approval.

The project has two modes:

- **Local mode**: default, deterministic, and credential-free. This is the path
  to use with prospects and customers who want to clone and run immediately.
- **Atlas mode**: optional connected mode using MongoDB Atlas, Atlas Vector
  Search automated embeddings, native `$rerank`, MongoDB-backed LangGraph state,
  MongoDB-backed long-term memory, and a configurable OpenAI-compatible LLM.

## What it demonstrates

- Operational supply-chain data: suppliers, parts, inventory, shipments, POs.
- Agent tools that separate reads from state-changing actions.
- Tenant and actor scoping with `realm_id`, `agent_id`, and `user_id`.
- Human-in-the-loop approval for business-state changes.
- Local deterministic fallback so the demo works without credentials.
- Optional MongoDBSaver checkpoints for stateful LangGraph execution.
- Optional MongoDBStore memory for long-term agent memory.
- Optional Atlas Vector Search `autoEmbed` and native `$rerank`.

## Quickstart: no credentials required

```bash
uv sync
uv run supply-chain-agent doctor
uv run supply-chain-agent ask "Shipment SH-1043 for BRK-22 is 6 days late. What are my options?"
```

Run the Streamlit UI:

```bash
uv run python -m streamlit run src/supply_chain_mongodb_agent/streamlit_app.py
```

Open the URL printed by Streamlit, usually `http://localhost:8501`.

Local mode uses deterministic seeded sample documents in process. It does not
write to a database and does not call an LLM provider. Responses are intentionally
predictable so the repository is safe to share and easy to test.

## Optional: connected Atlas + LLM mode

Copy the example environment file and set `DEMO_MODE=atlas`:

```bash
cp .env.example .env
```

Fill in the required values:

- `DEMO_MODE=atlas`
- `MONGODB_URI`
- `MONGODB_DB`
- `LLM_API_KEY`
- `LLM_MODEL`
- `LLM_BASE_URL`, optional for providers that do not use the default OpenAI API

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

Then bootstrap data and indexes:

```bash
uv run supply-chain-agent doctor
uv run supply-chain-agent seed
uv run supply-chain-agent indexes
```

`indexes` creates Atlas Search / Vector Search definitions for `autoEmbed`.
Native `$rerank` must also be enabled in Atlas Project Settings on MongoDB 8.3+.

Ask the connected agent:

```bash
uv run supply-chain-agent ask "Shipment SH-1043 for part BRK-22 is late. What are my options?"
```

## Human-in-the-loop approval

Try this in either CLI or Streamlit:

```bash
uv run supply-chain-agent ask "Draft an approval request to expedite SH-1043 with premium freight because BRK-22 has under 3 days of cover."
```

Then resume the same thread:

```bash
uv run supply-chain-agent approve --thread-id demo-thread
```

In local mode this approval is simulated. In Atlas mode it resumes the persisted
LangGraph checkpoint.

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

- Local mode is the customer-safe path: no credentials, no network calls, no
  database writes, deterministic outputs.
- Atlas mode is the platform showcase: it demonstrates real MongoDB-backed state,
  memory, vector search, automated embeddings, and reranking.
- All seeded documents include tenant scope to model multi-tenant isolation.
- The approval tool drafts actions instead of pretending to execute them.
- `doctor` reports non-sensitive readiness and never prints secrets.

## Tests

```bash
uv run python -m pytest
uv run python -m ruff check
```

Offline tests do not require Atlas, Voyage, or LLM credentials.