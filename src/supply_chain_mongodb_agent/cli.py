import typer
from langgraph.types import Command
from rich.console import Console

from supply_chain_mongodb_agent.agent import (
    build_agent,
    extract_latest_text,
    format_pending_approval,
)
from supply_chain_mongodb_agent.db import get_client, get_database
from supply_chain_mongodb_agent.indexes import (
    ensure_atlas_search_indexes,
    ensure_btree_indexes,
)
from supply_chain_mongodb_agent.seed import seed_demo_data
from supply_chain_mongodb_agent.settings import get_settings

app = typer.Typer(help="Supply-chain MongoDB + LangChain agent demo")
console = Console()


@app.command()
def seed() -> None:
    """Seed demo operational, corpus, and memory documents."""
    settings = get_settings()
    client = get_client(settings)
    db = get_database(client, settings)
    ensure_btree_indexes(db, settings)
    counts = seed_demo_data(db, settings)
    console.print({"seeded": counts})
    client.close()


@app.command()
def indexes() -> None:
    """Create Atlas Search/Vector Search auto-embedding indexes."""
    settings = get_settings()
    client = get_client(settings)
    db = get_database(client, settings)
    ensure_btree_indexes(db, settings)
    results = ensure_atlas_search_indexes(db, settings)
    console.print({"indexes": results})
    client.close()


@app.command()
def ask(question: str, thread_id: str = "demo-thread") -> None:
    """Ask the agent a supply-chain question."""
    settings = get_settings()
    client = get_client(settings)
    agent = build_agent(client, settings)
    result = agent.invoke(
        {"messages": [{"role": "user", "content": question}]},
        config={"configurable": {"thread_id": thread_id}},
    )
    console.print(extract_latest_text(result) or format_pending_approval(result))
    client.close()


@app.command()
def approve(thread_id: str = "demo-thread") -> None:
    """Approve pending human-in-the-loop tool calls for a thread."""
    settings = get_settings()
    client = get_client(settings)
    agent = build_agent(client, settings)
    result = agent.invoke(
        Command(resume={"decisions": [{"type": "approve"}]}),
        config={"configurable": {"thread_id": thread_id}},
    )
    console.print(extract_latest_text(result) or format_pending_approval(result))
    client.close()


@app.command()
def smoke() -> None:
    """Show non-sensitive effective configuration."""
    settings = get_settings()
    console.print({
        "db": settings.mongodb_db,
        "realm_id": settings.realm_id,
        "agent_id": settings.agent_id,
        "grove_model": settings.grove_model,
        "embedding_model": settings.atlas_embedding_model,
        "rerank_model": settings.atlas_rerank_model,
    })