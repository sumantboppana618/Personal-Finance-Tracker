import datetime as dt
import os
from bson import ObjectId
from flask import Flask, jsonify, render_template, request

from db import get_collection, get_db_status, reset_client

app = Flask(__name__)


def serialize_transaction(doc):
    return {
        "id": str(doc.get("_id")),
        "title": doc.get("title"),
        "amount": float(doc.get("amount", 0)),
        "type": doc.get("type"),
        "category": doc.get("category"),
        "date": doc.get("date"),
        "notes": doc.get("notes", ""),
    }


def parse_date(date_str):
    try:
        return dt.datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        return None


def build_filters(args):
    filters = {}
    if "type" in args:
        filters["type"] = args.get("type")
    if "category" in args:
        filters["category"] = args.get("category")
    start = args.get("start_date")
    end = args.get("end_date")
    if start or end:
        date_filter = {}
        if start:
            date_filter["$gte"] = start
        if end:
            date_filter["$lte"] = end
        filters["date"] = date_filter
    return filters


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/db-health")
def db_health():
    status = get_db_status()
    return jsonify(status)


@app.route("/transactions", methods=["GET"])
def get_transactions():
    collection = get_collection()
    filters = build_filters(request.args)
    docs = list(collection.find(filters))
    serialized = [serialize_transaction(doc) for doc in docs]
    return jsonify(serialized)


@app.route("/transactions", methods=["POST"])
def add_transaction():
    data = request.get_json(force=True, silent=True) or {}
    required_fields = ["title", "amount", "type", "category", "date"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    tx_type = data["type"].strip().lower()
    if tx_type not in {"income", "expense"}:
        return jsonify({"error": "type must be 'income' or 'expense'"}), 400

    parsed_date = parse_date(data["date"])
    if not parsed_date:
        return jsonify({"error": "date must be YYYY-MM-DD"}), 400

    try:
        amount = float(data["amount"])
    except Exception:
        return jsonify({"error": "amount must be a number"}), 400

    doc = {
        "title": data["title"],
        "amount": amount,
        "type": tx_type,
        "category": data["category"],
        "date": parsed_date.strftime("%Y-%m-%d"),
        "notes": data.get("notes", ""),
    }

    collection = get_collection()
    inserted = collection.insert_one(doc)
    created = collection.find_one({"_id": inserted.inserted_id})
    return jsonify(serialize_transaction(created)), 201


@app.route("/transactions/<transaction_id>", methods=["PUT"])
def update_transaction(transaction_id):
    data = request.get_json(force=True, silent=True) or {}
    collection = get_collection()
    try:
        _id = ObjectId(transaction_id)
    except Exception:
        return jsonify({"error": "Invalid transaction id"}), 400

    updates = {}
    for field in ["title", "category", "notes"]:
        if field in data:
            updates[field] = data[field]
    if "amount" in data:
        try:
            updates["amount"] = float(data["amount"])
        except Exception:
            return jsonify({"error": "amount must be a number"}), 400
    if "type" in data:
        if data["type"] not in {"income", "expense"}:
            return jsonify({"error": "type must be 'income' or 'expense'"}), 400
        updates["type"] = data["type"]
    if "date" in data:
        parsed_date = parse_date(data["date"])
        if not parsed_date:
            return jsonify({"error": "date must be YYYY-MM-DD"}), 400
        updates["date"] = parsed_date.strftime("%Y-%m-%d")

    if not updates:
        return jsonify({"error": "No valid fields to update"}), 400

    result = collection.update_one({"_id": _id}, {"$set": updates})
    if result.matched_count == 0:
        return jsonify({"error": "Transaction not found"}), 404

    updated = collection.find_one({"_id": _id})
    return jsonify(serialize_transaction(updated))


@app.route("/transactions/<transaction_id>", methods=["DELETE"])
def delete_transaction(transaction_id):
    collection = get_collection()
    try:
        _id = ObjectId(transaction_id)
    except Exception:
        return jsonify({"error": "Invalid transaction id"}), 400

    result = collection.delete_one({"_id": _id})
    if result.deleted_count == 0:
        return jsonify({"error": "Transaction not found"}), 404

    return jsonify({"status": "deleted"})


@app.route("/transactions/reset", methods=["POST"])
def reset_transactions():
    collection = get_collection()
    result = collection.delete_many({})
    return jsonify({"deleted": result.deleted_count})


@app.route("/summary", methods=["GET"])
def summary():
    collection = get_collection()
    docs = list(collection.find({}))
    total_income = sum(float(d.get("amount", 0)) for d in docs if d.get("type") == "income")
    total_expense = sum(float(d.get("amount", 0)) for d in docs if d.get("type") == "expense")
    balance = total_income - total_expense
    return jsonify(
        {
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": balance,
        }
    )


@app.route("/summary/monthly", methods=["GET"])
def monthly_summary():
    collection = get_collection()
    docs = list(collection.find({}))
    monthly = {}
    for d in docs:
        date_str = d.get("date")
        if not date_str:
            continue
        monthly_key = date_str[:7]  # YYYY-MM
        monthly.setdefault(monthly_key, {"income": 0, "expense": 0})
        if d.get("type") == "income":
            monthly[monthly_key]["income"] += float(d.get("amount", 0))
        else:
            monthly[monthly_key]["expense"] += float(d.get("amount", 0))
    result = []
    for month, values in sorted(monthly.items()):
        result.append({"month": month, "income": values["income"], "expense": values["expense"]})
    return jsonify(result)


def _generate_insight(transactions):
    if not transactions:
        return "No transactions yet. Add expenses to see spending insights."

    totals_by_category = {}
    for t in transactions:
        if t.get("type") != "expense":
            continue
        category = t.get("category", "uncategorized")
        totals_by_category[category] = totals_by_category.get(category, 0) + float(t.get("amount", 0))

    if not totals_by_category:
        return "Nice work—no expenses recorded yet."

    top_category = max(totals_by_category, key=totals_by_category.get)
    top_amount = totals_by_category[top_category]
    save_pct = 0.15 if top_amount >= 5000 else 0.1
    save_amount = top_amount * save_pct
    bullets = [
        f"• {top_category.title()} spending: QAR {top_amount:,.2f}",
        f"• Suggested cap: QAR {top_amount:,.2f}",
        f"• Recommended save: {int(save_pct*100)}% → QAR {save_amount:,.2f}",
        "• Allocate that amount into a rainy-day fund or interest-bearing account to grow."
    ]
    return "\n".join(bullets)


@app.route("/ai/spending-insights", methods=["GET"])
def ai_spending_insights():
    collection = get_collection()
    recent = list(collection.find({}).sort("date", -1).limit(20))
    insights = _generate_insight(recent)
    return jsonify({"insight": insights})


@app.before_request
def ensure_testing_reset():
    # In tests we may reset the client between runs.
    if os.getenv("RESET_DB_ON_REQUEST") == "1":
        reset_client()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
