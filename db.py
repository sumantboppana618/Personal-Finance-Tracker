import os
from pymongo import MongoClient

_client = None


def reset_client():
    """Reset cached client (primarily used in tests)."""
    global _client
    _client = None


def _use_mock():
    return os.getenv("USE_MOCK_DB") == "1" or os.getenv("TESTING") == "1"


def get_client():
    """Return a Mongo client or a mongomock client when testing."""
    global _client
    if _client:
        return _client

    if _use_mock():
        import mongomock  # type: ignore

        _client = mongomock.MongoClient()
        return _client

    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        raise RuntimeError("MONGO_URI not set")

    _client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    return _client


def get_collection(name: str = "transactions"):
    db_name = os.getenv("MONGO_DB_NAME", "finance_tracker")
    client = get_client()
    return client[db_name][name]


def get_db_status():
    try:
        client = get_client()
        client.admin.command("ping")
        return {"status": "ok", "message": "MongoDB connected"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
