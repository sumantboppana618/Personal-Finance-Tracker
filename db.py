import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from bson import ObjectId
from pymongo import MongoClient


def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    value = os.getenv(name, default)
    return value.strip() if isinstance(value, str) else value


MONGO_URI = _env("MONGO_URI")
MONGO_DB_NAME = _env("MONGO_DB_NAME", "finance_tracker")
USE_MOCK_DB = _env("USE_MOCK_DB") == "1"

_mock_transactions: List[Dict[str, Any]] = []


def _get_client():
    if not MONGO_URI:
        raise RuntimeError("MONGO_URI not set")
    return MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)


def get_db_status():
    if USE_MOCK_DB:
        return {"status": "ok", "message": "Mock DB active"}

    try:
        client = _get_client()
        client.admin.command("ping")
        return {"status": "ok", "message": "MongoDB connected"}
    except Exception as e:  # pragma: no cover - environment dependent
        return {"status": "error", "message": str(e)}


def _collection():
    client = _get_client()
    db = client[MONGO_DB_NAME]
    return db["transactions"]


def _serialize(doc: Dict[str, Any]) -> Dict[str, Any]:
    result = dict(doc)
    if "_id" in result:
        result["id"] = str(result.pop("_id"))
    return result


def _normalize_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(data)
    if "date" in normalized:
        try:
            normalized["date"] = datetime.fromisoformat(str(normalized["date"]))
        except ValueError:
            raise ValueError("Invalid date format; expected ISO date like 2024-03-01")
    if "amount" in normalized:
        normalized["amount"] = float(normalized["amount"])
    return normalized


# -------------------- CRUD -------------------- #

def create_transaction(data: Dict[str, Any]) -> Dict[str, Any]:
    doc = _normalize_payload(data)
    if USE_MOCK_DB:
        doc["id"] = str(len(_mock_transactions) + 1)
        _mock_transactions.append(doc)
        return doc

    result = _collection().insert_one(doc)
    doc["_id"] = result.inserted_id
    return _serialize(doc)


def get_transactions(filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    query: Dict[str, Any] = {}
    if filters.get("type"):
        query["type"] = filters["type"]
    if filters.get("category"):
        query["category"] = filters["category"]

    date_filter: Dict[str, Any] = {}
    if filters.get("start_date"):
        date_filter["$gte"] = datetime.fromisoformat(filters["start_date"])
    if filters.get("end_date"):
        end = datetime.fromisoformat(filters["end_date"]) + timedelta(days=1)
        date_filter["$lt"] = end
    if date_filter:
        query["date"] = date_filter

    if USE_MOCK_DB:
        def _in_range(doc):
            if "date" in query:
                d = doc.get("date")
                if not isinstance(d, datetime):
                    return False
                if "$gte" in query["date"] and d < query["date"]["$gte"]:
                    return False
                if "$lt" in query["date"] and d >= query["date"]["$lt"]:
                    return False
            if query.get("type") and doc.get("type") != query["type"]:
                return False
            if query.get("category") and doc.get("category") != query["category"]:
                return False
            return True

        results = [dict(x) for x in _mock_transactions if _in_range(x)]
        return [_serialize(x) for x in results]

    docs = list(_collection().find(query).sort("date", -1))
    return [_serialize(d) for d in docs]


def update_transaction(tx_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if USE_MOCK_DB:
        for i, doc in enumerate(_mock_transactions):
            if doc.get("id") == tx_id:
                updated = _normalize_payload(data)
                updated["id"] = tx_id
                _mock_transactions[i] = updated
                return updated
        return None

    oid = ObjectId(tx_id)
    doc = _normalize_payload(data)
    result = _collection().find_one_and_replace({"_id": oid}, doc, return_document=True)
    return _serialize(result) if result else None


def delete_transaction(tx_id: str) -> Optional[Dict[str, Any]]:
    if USE_MOCK_DB:
        for i, doc in enumerate(_mock_transactions):
            if doc.get("id") == tx_id:
                return _mock_transactions.pop(i)
        return None

    oid = ObjectId(tx_id)
    result = _collection().find_one_and_delete({"_id": oid})
    return _serialize(result) if result else None


def clear_transactions():
    if USE_MOCK_DB:
        _mock_transactions.clear()
        return
    _collection().delete_many({})


def get_summary() -> Dict[str, float]:
    if USE_MOCK_DB:
        income = sum(float(t.get("amount", 0)) for t in _mock_transactions if t.get("type") == "income")
        expense = sum(float(t.get("amount", 0)) for t in _mock_transactions if t.get("type") == "expense")
        return {"total_income": income, "total_expense": expense, "balance": income - expense}

    pipeline = [
        {"$group": {"_id": "$type", "total": {"$sum": "$amount"}}}
    ]
    totals = {"income": 0.0, "expense": 0.0}
    for row in _collection().aggregate(pipeline):
        if row["_id"] in totals:
            totals[row["_id"]] = float(row["total"])
    return {
        "total_income": totals["income"],
        "total_expense": totals["expense"],
        "balance": totals["income"] - totals["expense"],
    }


def get_monthly_summary() -> List[Dict[str, Any]]:
    if USE_MOCK_DB:
        months: Dict[str, Dict[str, Any]] = {}
        for t in _mock_transactions:
            d = t.get("date")
            if not isinstance(d, datetime):
                continue
            key = d.strftime("%Y-%m")
            months.setdefault(key, {"month": key, "income": 0.0, "expense": 0.0})
            if t.get("type") == "income":
                months[key]["income"] += float(t.get("amount", 0))
            else:
                months[key]["expense"] += float(t.get("amount", 0))
        return sorted(months.values(), key=lambda x: x["month"], reverse=True)

    pipeline = [
        {
            "$group": {
                "_id": {"$dateToString": {"format": "%Y-%m", "date": "$date"}},
                "income": {"$sum": {"$cond": [{"$eq": ["$type", "income"]}, "$amount", 0]}},
                "expense": {"$sum": {"$cond": [{"$eq": ["$type", "expense"]}, "$amount", 0]}},
            }
        },
        {"$sort": {"_id": -1}},
    ]
    rows = []
    for row in _collection().aggregate(pipeline):
        rows.append(
            {
                "month": row["_id"],
                "income": float(row["income"]),
                "expense": float(row["expense"]),
            }
        )
    return rows
