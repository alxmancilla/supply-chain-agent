import typer
from langgraph.types import Command
from rich.console import Console

from supply_chain_mongodb_agent.agent import (
    build_agent,
    extract_latest_text,
    format_pending_approval,
)
from supply_chain_mongodb_agent.db import get_client, get_database
from supply_chain_mongodb_agent.doctor import doctor_ok, doctor_report
from supply_chain_mongodb_agent.indexes import (
    ensure_atlas_search_indexes,
    ensure_btree_indexes,
)
from supply_chain_mongodb_agent.local_agent import approve_local_demo
from supply_chain_mongodb_agent.seed import demo_documents, seed_demo_data
from supply_chain_mongodb_agent.settings import get_settings

app = typer.Typer(help="Supply-chain MongoDB + LangChain agent demo")
console = Console()


@app.command()
def seed() -> None:
    """Seed demo operational, corpus, and memory documents."""
    settings = get_settings()
    if settings.demo_mode == "local":
        counts = {name: len(docs) for name, docs in demo_documents(settings).items()}
        console.print({"mode": "local", "seeded": counts, "note": "Local mode uses in-process sample data; no database writes."})
        return
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
    if settings.demo_mode == "local":
        console.print({"mode": "local", "indexes": "not required", "note": "Set DEMO_MODE=atlas to create Atlas indexes."})
        return
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
    client = None if settings.demo_mode == "local" else get_client(settings)
    agent = build_agent(client, settings)
    result = agent.invoke(
        {"messages": [{"role": "user", "content": question}]},
        config={"configurable": {"thread_id": thread_id}},
    )
    console.print(extract_latest_text(result) or format_pending_approval(result))
    if client is not None:
        client.close()


@app.command()
def approve(thread_id: str = "demo-thread") -> None:
    """Approve pending human-in-the-loop tool calls for a thread."""
    settings = get_settings()
    if settings.demo_mode == "local":
        result = approve_local_demo(thread_id)
        console.print(extract_latest_text(result))
        return
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
    llm_status = (
        {"provider": "not used in local mode", "model": "not used in local mode", "api_key_configured": "not required"}
        if settings.demo_mode == "local"
        else {
            "provider": settings.effective_llm_provider,
            "model": settings.effective_llm_model,
            "base_url_configured": settings.effective_llm_base_url_configured,
            "custom_api_key_header": bool(settings.effective_llm_api_key_header),
            "responses_api": settings.effective_llm_use_responses_api,
            "api_key_configured": settings.llm_api_key_configured,
        }
    )
    console.print({
        "demo_mode": settings.demo_mode,
        "db": settings.mongodb_db,
        "realm_id": settings.realm_id,
        "agent_id": settings.agent_id,
        "llm": llm_status,
        "embedding_model": settings.atlas_embedding_model,
        "rerank_model": settings.atlas_rerank_model,
    })


@app.command()
def doctor() -> None:
    """Run non-sensitive readiness checks for the selected demo mode."""
    checks = doctor_report(get_settings())
    for check in checks:
        icon = "✅" if check["ok"] else "❌"
        console.print(f"{icon} {check['name']}: {check['detail']}")
    if not doctor_ok(checks):
        raise typer.Exit(code=1)