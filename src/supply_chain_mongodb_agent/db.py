from pymongo import MongoClient
from pymongo.database import Database

from supply_chain_mongodb_agent.settings import Settings, get_settings


def get_client(settings: Settings | None = None) -> MongoClient:
    """Create a reusable PyMongo client.

    This demo intentionally avoids arbitrary pool/timeout tuning. PyMongo's
    defaults are appropriate for a local CLI/Streamlit demo; tune from Atlas
    connection metrics before changing pool parameters for production.
    """
    settings = settings or get_settings()
    return MongoClient(settings.mongodb_uri, appname="supply-chain-agent-demo")


def get_database(client: MongoClient, settings: Settings | None = None) -> Database:
    settings = settings or get_settings()
    return client[settings.mongodb_db]