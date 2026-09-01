# Supply Chain Resolution Agent

Demo showing how MongoDB Atlas and LangChain/Deep Agents work together in a
stateful supply-chain agent.

## What it demonstrates

- **Operational data** in MongoDB: suppliers, parts, inventory, shipments, POs.
- **Agent state** in MongoDB via `MongoDBSaver` checkpoints.
- **Long-term memory** in MongoDB via Deep Agents `StoreBackend` and memory docs.
- **Vectors** with Atlas Vector Search **Automated Embedding** (`autoEmbed`).
- **Voyage AI through Atlas** using `voyage-4` embeddings and native `$rerank`.
- **Azure Grove API** as the OpenAI-compatible LLM gateway for `gpt-5.5`.
- **Human-in-the-loop** approval using Deep Agents `interrupt_on`.

## Setup

```bash
cp .env.example .env
uv sync
```

Fill in `.env` with your MongoDB Atlas URI and Grove API key.

## Bootstrap data and indexes

```bash
uv run supply-chain-agent seed
uv run supply-chain-agent indexes
```

`indexes` creates Atlas Search / Vector Search definitions for `autoEmbed`.
Native `$rerank` must also be enabled in Atlas Project Settings on MongoDB 8.3+.

## Run the CLI demo

```bash
uv run supply-chain-agent ask "Shipment SH-1043 for part BRK-22 is late. What are my options?"
```

## Run the Streamlit UI

```bash
uv run streamlit run src/supply_chain_mongodb_agent/streamlit_app.py
```

## Suggested demo queries

Use these in the CLI or Streamlit UI to show the full capability set.

### Operational data + recommendations

- `Shipment SH-1043 for BRK-22 is 6 days late. What are my options?`
- `What is the risk for shipment SH-2048 and should we use the battery cells?`
- `Shipment SH-3110 is delayed. Do we need premium freight?`

### Atlas Vector Search automated embedding + native rerank

- `Find the policy for Tier-1 shortages with less than three days of cover.`
- `Which contract terms apply when SUP-BAT has a quality hold?`
- `What approved alternate exists for BRK-22? Cite the source IDs.`

### Long-term memory and episodic memory

- `Do I have any planner preferences relevant to premium freight?`
- `Have we handled a BRK-22 port delay before? What worked last time?`
- `Compare this CELL-9 quality hold with prior incidents and recommend next steps.`

### Human-in-the-loop state and resume

- `Draft an approval request to expedite SH-1043 with premium freight because BRK-22 has under 3 days of cover.`
- Then resume the same thread with `uv run supply-chain-agent approve --thread-id <thread>`.

### Cross-capability story

- `For SH-1043, use live data, playbooks, planner memory, and prior incidents to recommend the lowest-risk action.`
- `For SH-2048, explain the operational state, relevant SOP, similar episode, and whether approval is required.`

## Tests

```bash
uv run pytest
uv run ruff check
```

Tests are offline and do not require Atlas, Voyage, or Grove credentials.