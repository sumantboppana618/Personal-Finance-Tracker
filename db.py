import os
from pymongo import MongoClient


def get_db_status():
    mongo_uri = os.getenv("MONGO_URI")

    if not mongo_uri:
        return {"status": "error", "message": "MONGO_URI not set"}

    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        return {"status": "ok", "message": "MongoDB connected"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
