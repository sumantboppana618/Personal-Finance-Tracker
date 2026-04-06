from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from db import (
    clear_transactions,
    create_transaction,
    delete_transaction,
    get_db_status,
    get_monthly_summary,
    get_summary,
    get_transactions,
    update_transaction,
)

load_dotenv()

app = Flask(__name__)


@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


# --- Home Page ---
@app.route("/")
def home():
    return render_template("index.html")


# --- Health Check ---
@app.route("/health")
def health():
    return jsonify({"status": "ok"})


# --- Database Health Check ---
@app.route("/db-health")
def db_health():
    status = get_db_status()
    return jsonify(status)


# --- Transaction CRUD Routes ---
@app.route("/transactions", methods=["GET"])
def list_transactions():
    filters = {
        "type": request.args.get("type"),
        "category": request.args.get("category"),
        "start_date": request.args.get("start_date"),
        "end_date": request.args.get("end_date"),
    }
    return jsonify(get_transactions(filters))


@app.route("/transactions", methods=["POST"])
def add_transaction():
    data = request.get_json()
    required_fields = ["title", "amount", "type", "category", "date"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400
    created = create_transaction(data)
    return jsonify(created), 201


@app.route("/transactions/<string:tx_id>", methods=["PUT"])
def update_transaction_route(tx_id):
    data = request.get_json()
    updated = update_transaction(tx_id, data)
    if not updated:
        return jsonify({"error": "Transaction not found"}), 404
    return jsonify(updated)


@app.route("/transactions/<string:tx_id>", methods=["DELETE"])
def delete_transaction_route(tx_id):
    removed = delete_transaction(tx_id)
    if not removed:
        return jsonify({"error": "Transaction not found"}), 404
    return jsonify(removed)


@app.route("/transactions/reset", methods=["POST"])
def reset_transactions():
    clear_transactions()
    return jsonify({"message": "All transactions cleared"})


# --- Summary and Reporting Routes ---
@app.route("/summary")
def summary():
    return jsonify(get_summary())


@app.route("/summary/monthly")
def monthly_summary():
    return jsonify(get_monthly_summary())


# --- AI Spending Insights ---
@app.route("/ai/spending-insights")
def spending_insights():
    from ai import analyze_spending
    rows = get_transactions({})
    if not rows:
        return jsonify({"insight": "No transactions yet. Add some to get insights."})
    result = analyze_spending(rows)
    return jsonify({"insight": result.get("summary", "No insight available.")})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)