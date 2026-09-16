from supply_chain_mongodb_agent.settings import Settings
from supply_chain_mongodb_agent.validation import (
    _search_indexes_pending,
    validate_atlas_setup,
)


class FakeAdmin:
    def __init__(self) -> None:
        self.commands: list[str] = []

    def command(self, name: str) -> None:
        self.commands.append(name)


class FakeClient:
    def __init__(self) -> None:
        self.admin = FakeAdmin()
        self.closed = False

    def close(self) -> None:
        self.closed = True


def test_validate_atlas_setup_prepares_data_indexes_and_readiness(monkeypatch) -> None:
    client = FakeClient()
    db = object()
    checks = [{"name": "search_indexes", "ok": True, "detail": "ready"}]

    from supply_chain_mongodb_agent import validation

    monkeypatch.setattr(validation, "get_client", lambda settings: client)
    monkeypatch.setattr(validation, "get_database", lambda found_client, settings: db)
    monkeypatch.setattr(validation, "ensure_btree_indexes", lambda found_db, settings: ["shipments.realm_id_1"])
    monkeypatch.setattr(validation, "seed_demo_data", lambda found_db, settings: {"shipments": 3})
    monkeypatch.setattr(validation, "ensure_atlas_search_indexes", lambda found_db, settings: ["exists:index-1"])
    monkeypatch.setattr(validation, "doctor_report", lambda settings: checks)

    report = validate_atlas_setup(Settings(), wait_indexes_seconds=0)

    assert report["ok"]
    assert report["btree_indexes"] == ["shipments.realm_id_1"]
    assert report["seeded"] == {"shipments": 3}
    assert report["search_indexes"] == ["exists:index-1"]
    assert client.admin.commands == ["ping"]
    assert client.closed


def test_search_indexes_pending_handles_m0_build_states() -> None:
    assert _search_indexes_pending([{"name": "search_indexes", "ok": False, "detail": "missing indexes: a"}])
    assert _search_indexes_pending([{"name": "search_indexes", "ok": False, "detail": "indexes found but not ready yet"}])
    assert _search_indexes_pending([{"name": "search_indexes", "ok": False, "detail": "stale index definitions"}])
    assert not _search_indexes_pending([{"name": "search_indexes", "ok": True, "detail": "ready"}])