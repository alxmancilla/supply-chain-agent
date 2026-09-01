from datetime import UTC, datetime
from typing import Any

from pymongo.database import Database

from supply_chain_mongodb_agent.settings import Settings, get_settings


def demo_documents(settings: Settings | None = None) -> dict[str, list[dict[str, Any]]]:
    settings = settings or get_settings()
    scope = {"realm_id": settings.realm_id}
    return {
        "suppliers": [
            scope | {"supplier_id": "SUP-NEO", "name": "Neon Components", "risk": "medium"},
            scope | {"supplier_id": "SUP-ALT", "name": "AltSource Industrial", "risk": "low"},
            scope | {"supplier_id": "SUP-BAT", "name": "Apex Battery Systems", "risk": "high"},
            scope | {"supplier_id": "SUP-FAS", "name": "FastenerWorks", "risk": "low"},
        ],
        "parts": [
            scope | {"part_id": "BRK-22", "description": "Brake actuator", "tier": 1},
            scope | {"part_id": "CELL-9", "description": "High-density battery cell", "tier": 1},
            scope | {"part_id": "BOLT-7", "description": "Chassis fastener kit", "tier": 2},
        ],
        "inventory": [
            scope | {"part_id": "BRK-22", "site": "DET-01", "on_hand": 120, "daily_use": 55},
            scope | {"part_id": "CELL-9", "site": "FRE-02", "on_hand": 420, "daily_use": 220},
            scope | {"part_id": "BOLT-7", "site": "DET-01", "on_hand": 9000, "daily_use": 800},
        ],
        "purchase_orders": [
            scope | {"po_id": "PO-9001", "part_id": "BRK-22", "supplier_id": "SUP-NEO", "qty": 500},
            scope | {"po_id": "PO-9017", "part_id": "CELL-9", "supplier_id": "SUP-BAT", "qty": 1200},
            scope | {"po_id": "PO-9022", "part_id": "BOLT-7", "supplier_id": "SUP-FAS", "qty": 15000},
        ],
        "shipments": [
            scope | {
                "shipment_id": "SH-1043",
                "po_id": "PO-9001",
                "part_id": "BRK-22",
                "supplier_id": "SUP-NEO",
                "status": "delayed",
                "delay_days": 6,
                "eta": "2026-09-08",
                "reason": "port congestion",
            },
            scope | {
                "shipment_id": "SH-2048",
                "po_id": "PO-9017",
                "part_id": "CELL-9",
                "supplier_id": "SUP-BAT",
                "status": "quality_hold",
                "delay_days": 4,
                "eta": "2026-09-06",
                "reason": "incoming inspection failed electrolyte leakage sample",
            },
            scope | {
                "shipment_id": "SH-3110",
                "po_id": "PO-9022",
                "part_id": "BOLT-7",
                "supplier_id": "SUP-FAS",
                "status": "delayed",
                "delay_days": 2,
                "eta": "2026-09-04",
                "reason": "carrier missed pickup window",
            },
        ],
        "knowledge_corpus": knowledge_documents(settings),
        "agent_memories": memory_documents(settings),
        "agent_episodes": episode_documents(settings),
    }


def knowledge_documents(settings: Settings | None = None) -> list[dict[str, Any]]:
    settings = settings or get_settings()
    scope = {"realm_id": settings.realm_id}
    return [
        scope | {"doc_id": "sop-expedite-tier1", "source": "SOP-EXP-01", "text": "For Tier-1 part shortages under three days of cover, evaluate premium freight, split shipment, and approved alternate suppliers before line stoppage."},
        scope | {"doc_id": "contract-sup-neo", "source": "SUP-NEO-MSA", "text": "Neon Components must notify delays over 48 hours and share cost on premium freight when delay is supplier-controlled."},
        scope | {"doc_id": "alt-source-brk22", "source": "AVL-BRK-22", "text": "AltSource Industrial is an approved alternate supplier for BRK-22 with two-day expedited lead time from Ohio."},
        scope | {"doc_id": "sop-quality-hold", "source": "SOP-QA-17", "text": "For battery cell quality holds, quarantine suspect lots, request supplier 8D within 24 hours, and evaluate deviation only with quality engineering approval."},
        scope | {"doc_id": "sop-tier2-buffer", "source": "SOP-BUF-04", "text": "Tier-2 consumables with over seven days of cover should avoid premium freight unless line stoppage risk appears within 72 hours."},
        scope | {"doc_id": "contract-sup-bat", "source": "SUP-BAT-QA", "text": "Apex Battery Systems must provide replacement lots for confirmed leakage defects and cover containment freight for high-risk battery cell holds."},
    ]


def memory_documents(settings: Settings | None = None) -> list[dict[str, Any]]:
    settings = settings or get_settings()
    return [
        {
            "realm_id": settings.realm_id,
            "user_id": settings.user_id,
            "memory_id": "planner-air-freight-pref",
            "content": "Planner prefers premium freight for Tier-1 parts when days of cover is below three.",
            "created_at": datetime.now(UTC),
        }
    ]


def episode_documents(settings: Settings | None = None) -> list[dict[str, Any]]:
    settings = settings or get_settings()
    base = {"realm_id": settings.realm_id, "user_id": settings.user_id}
    return [
        base | {
            "episode_id": "ep-brk22-port-delay",
            "incident_type": "logistics_delay",
            "related_parts": ["BRK-22"],
            "outcome": "no_line_stop",
            "resolved_at": datetime(2026, 5, 18, tzinfo=UTC),
            "content": "BRK-22 shipment delayed five days by port congestion. Team split available inventory between DET-01 lines, obtained partial container release, and used AltSource for 200 emergency units. Lesson: ask carrier for partial release before approving full premium freight.",
        },
        base | {
            "episode_id": "ep-cell9-quality-hold",
            "incident_type": "quality_hold",
            "related_parts": ["CELL-9"],
            "outcome": "contained_with_replacement_lot",
            "resolved_at": datetime(2026, 7, 9, tzinfo=UTC),
            "content": "CELL-9 leakage sample triggered quality hold. Best result came from quarantining lot, requesting supplier 8D, and pulling replacement lot from Apex Battery Systems while quality engineering rejected deviation use.",
        },
        base | {
            "episode_id": "ep-bolt7-low-risk-delay",
            "incident_type": "low_risk_delay",
            "related_parts": ["BOLT-7"],
            "outcome": "premium_freight_avoided",
            "resolved_at": datetime(2026, 6, 2, tzinfo=UTC),
            "content": "BOLT-7 carrier delay looked urgent but inventory cover was above ten days. Planner avoided premium freight, moved pickup to backup carrier, and kept production on plan. Lesson: calculate days of cover before escalating Tier-2 consumables.",
        },
    ]


def seed_demo_data(db: Database, settings: Settings | None = None) -> dict[str, int]:
    counts: dict[str, int] = {}
    for coll_name, docs in demo_documents(settings).items():
        for doc in docs:
            key = _identity_key(coll_name, doc)
            db[coll_name].replace_one(key, doc, upsert=True)
        counts[coll_name] = len(docs)
    return counts


def _identity_key(collection: str, doc: dict[str, Any]) -> dict[str, Any]:
    key_field = {
        "suppliers": "supplier_id",
        "parts": "part_id",
        "inventory": "part_id",
        "purchase_orders": "po_id",
        "shipments": "shipment_id",
        "knowledge_corpus": "doc_id",
        "agent_memories": "memory_id",
        "agent_episodes": "episode_id",
    }[collection]
    if collection == "inventory":
        return {"realm_id": doc["realm_id"], "part_id": doc["part_id"], "site": doc["site"]}
    return {"realm_id": doc["realm_id"], key_field: doc[key_field]}