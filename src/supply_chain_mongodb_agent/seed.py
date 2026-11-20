from datetime import UTC, datetime
from typing import Any

from pymongo.database import Database

from supply_chain_mongodb_agent.settings import Settings, get_settings


def demo_documents(settings: Settings | None = None) -> dict[str, list[dict[str, Any]]]:
    settings = settings or get_settings()
    scope = {"realm_id": settings.realm_id}
    return {
        "suppliers": [
            scope
            | {
                "supplier_id": "SUP-ONC",
                "name": "OncoPharm Manufacturing",
                "risk": "medium",
            },
            scope
            | {
                "supplier_id": "SUP-POOL",
                "name": "Regional Redistribution Pool",
                "risk": "low",
            },
            scope
            | {
                "supplier_id": "SUP-COLD",
                "name": "MedExpress Cold Chain",
                "risk": "high",
            },
            scope
            | {
                "supplier_id": "SUP-GEN",
                "name": "SterileSource Generics",
                "risk": "low",
            },
        ],
        "parts": [
            scope
            | {
                "part_id": "NDC-1043",
                "description": "Critical oncology injectable SKU",
                "tier": 1,
            },
            scope
            | {
                "part_id": "COLD-2048",
                "description": "Cold-chain biologic pack",
                "tier": 1,
            },
            scope
            | {
                "part_id": "MED-3110",
                "description": "Routine medical-surgical supply kit",
                "tier": 2,
            },
        ],
        "inventory": [
            scope
            | {
                "part_id": "NDC-1043",
                "site": "DC-ATL-01",
                "on_hand": 80,
                "daily_use": 48,
            },
            scope
            | {
                "part_id": "COLD-2048",
                "site": "DC-PHX-02",
                "on_hand": 260,
                "daily_use": 140,
            },
            scope
            | {
                "part_id": "MED-3110",
                "site": "DC-ATL-01",
                "on_hand": 9000,
                "daily_use": 800,
            },
        ],
        "purchase_orders": [
            scope
            | {
                "po_id": "PO-9001",
                "part_id": "NDC-1043",
                "supplier_id": "SUP-ONC",
                "qty": 500,
            },
            scope
            | {
                "po_id": "PO-9017",
                "part_id": "COLD-2048",
                "supplier_id": "SUP-COLD",
                "qty": 1200,
            },
            scope
            | {
                "po_id": "PO-9022",
                "part_id": "MED-3110",
                "supplier_id": "SUP-GEN",
                "qty": 15000,
            },
        ],
        "shipments": [
            scope
            | {
                "shipment_id": "SH-1043",
                "po_id": "PO-9001",
                "part_id": "NDC-1043",
                "supplier_id": "SUP-ONC",
                "status": "delayed",
                "delay_days": 6,
                "eta": "2026-09-08",
                "reason": "manufacturer allocation delay",
            },
            scope
            | {
                "shipment_id": "SH-2048",
                "po_id": "PO-9017",
                "part_id": "COLD-2048",
                "supplier_id": "SUP-COLD",
                "status": "temperature_excursion_hold",
                "delay_days": 4,
                "eta": "2026-09-06",
                "reason": "temperature monitor out of range during inbound transit",
            },
            scope
            | {
                "shipment_id": "SH-3110",
                "po_id": "PO-9022",
                "part_id": "MED-3110",
                "supplier_id": "SUP-GEN",
                "status": "delayed",
                "delay_days": 2,
                "eta": "2026-09-04",
                "reason": "regional courier missed pickup window",
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
        scope
        | {
            "doc_id": "sop-expedite-critical",
            "source": "SOP-EXP-01",
            "text": "For critical healthcare products under 48 hours of DC cover, evaluate expedited courier, inventory transfer, allocation request, and approved redistribution pool before customer service risk escalates.",
        },
        scope
        | {
            "doc_id": "contract-sup-onc",
            "source": "SUP-ONC-MSA",
            "text": "OncoPharm Manufacturing must notify delays over 48 hours and share expedite costs when a manufacturer-controlled allocation delay affects committed healthcare distribution orders.",
        },
        scope
        | {
            "doc_id": "alt-source-ndc1043",
            "source": "REDIST-NDC-1043",
            "text": "Regional Redistribution Pool is an approved alternate fulfillment path for NDC-1043 with two-day cold-chain courier lead time from a nearby distribution center.",
        },
        scope
        | {
            "doc_id": "sop-temperature-excursion",
            "source": "SOP-COLD-17",
            "text": "For cold-chain temperature excursion holds, quarantine suspect lots, preserve logger evidence, request manufacturer quality disposition within 24 hours, and do not release product without quality approval.",
        },
        scope
        | {
            "doc_id": "sop-routine-buffer",
            "source": "SOP-BUF-04",
            "text": "Routine medical-surgical supplies with over seven days of cover should avoid expedited courier unless a healthcare customer service risk appears within 72 hours.",
        },
        scope
        | {
            "doc_id": "contract-sup-cold",
            "source": "SUP-COLD-QA",
            "text": "MedExpress Cold Chain must provide replacement inventory or validated disposition for confirmed temperature excursions and cover containment freight for high-risk cold-chain holds.",
        },
    ]


def memory_documents(settings: Settings | None = None) -> list[dict[str, Any]]:
    settings = settings or get_settings()
    return [
        {
            "realm_id": settings.realm_id,
            "agent_id": settings.agent_id,
            "user_id": settings.user_id,
            "memory_id": "planner-air-freight-pref",
            "content": "Planner prefers cold-chain expedite for critical healthcare products when distribution-center days of supply is below two, after checking allocation transfers.",
            "created_at": datetime.now(UTC),
        }
    ]


def episode_documents(settings: Settings | None = None) -> list[dict[str, Any]]:
    settings = settings or get_settings()
    base = {
        "realm_id": settings.realm_id,
        "agent_id": settings.agent_id,
        "user_id": settings.user_id,
    }
    return [
        base
        | {
            "episode_id": "ep-ndc1043-allocation-delay",
            "incident_type": "logistics_delay",
            "related_parts": ["NDC-1043"],
            "outcome": "service_level_protected",
            "resolved_at": datetime(2026, 5, 18, tzinfo=UTC),
            "content": "NDC-1043 shipment delayed five days by manufacturer allocation. Team transferred available inventory from DC-ATL-01, requested allocation release, and used the redistribution pool for 200 emergency units. Lesson: check allocation transfer before approving full cold-chain expedite.",
        },
        base
        | {
            "episode_id": "ep-cold2048-temperature-hold",
            "incident_type": "temperature_excursion_hold",
            "related_parts": ["COLD-2048"],
            "outcome": "contained_with_quality_disposition",
            "resolved_at": datetime(2026, 7, 9, tzinfo=UTC),
            "content": "COLD-2048 logger excursion triggered a cold-chain hold. Best result came from quarantining the lot, preserving logger data, requesting manufacturer quality disposition, and pulling replacement inventory while quality rejected release without disposition.",
        },
        base
        | {
            "episode_id": "ep-med3110-low-risk-delay",
            "incident_type": "low_risk_delay",
            "related_parts": ["MED-3110"],
            "outcome": "expedite_avoided",
            "resolved_at": datetime(2026, 6, 2, tzinfo=UTC),
            "content": "MED-3110 courier delay looked urgent but inventory cover was above ten days. Planner avoided expedited courier, moved pickup to backup carrier, and maintained customer service. Lesson: calculate days of supply before escalating routine medical-surgical supplies.",
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
        return {
            "realm_id": doc["realm_id"],
            "part_id": doc["part_id"],
            "site": doc["site"],
        }
    if collection in {"agent_memories", "agent_episodes"}:
        return {
            "realm_id": doc["realm_id"],
            "agent_id": doc["agent_id"],
            "user_id": doc["user_id"],
            key_field: doc[key_field],
        }
    return {"realm_id": doc["realm_id"], key_field: doc[key_field]}
