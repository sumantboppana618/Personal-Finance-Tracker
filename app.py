from flask import Flask, jsonify, render_template, request
from db import get_db_status

app = Flask(__name__)
transactions = []


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
    result = []
    for i, t in enumerate(transactions):
        entry = dict(t)
        entry["id"] = i
        result.append(entry)
    return jsonify(result)


@app.route("/transactions", methods=["POST"])
def add_transaction():
    data = request.get_json()
    required_fields = ["title", "amount", "type", "category", "date"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400
    transactions.append(data)
    return jsonify(data), 201


@app.route("/transactions/<int:index>", methods=["PUT"])
def update_transaction(index):
    if 0 <= index < len(transactions):
        data = request.get_json()
        transactions[index] = data
        return jsonify(data)
    return jsonify({"error": "Transaction not found"}), 404


@app.route("/transactions/<int:index>", methods=["DELETE"])
def delete_transaction(index):
    if 0 <= index < len(transactions):
        removed = transactions.pop(index)
        return jsonify(removed)
    return jsonify({"error": "Transaction not found"}), 404


@app.route("/transactions/reset", methods=["POST"])
def reset_transactions():
    transactions.clear()
    return jsonify({"message": "All transactions cleared"})


@app.route("/summary")
def summary():
    total_income = sum(
        float(t["amount"]) for t in transactions if t.get("type") == "income"
    )
    total_expense = sum(
        float(t["amount"]) for t in transactions if t.get("type") == "expense"
    )
    return jsonify({
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": total_income - total_expense
    })


@app.route("/summary/monthly")
def monthly_summary():
    months = {}
    for t in transactions:
        month_key = t.get("date", "")[:7]
        if month_key not in months:
            months[month_key] = {"month": month_key, "income": 0, "expense": 0}
        if t.get("type") == "income":
            months[month_key]["income"] += float(t["amount"])
        else:
            months[month_key]["expense"] += float(t["amount"])
    return jsonify(sorted(months.values(), key=lambda x: x["month"], reverse=True))


@app.route("/ai/spending-insights")
def spending_insights():
    if not transactions:
        return jsonify({"insight": "No transactions yet. Add some to get insights."})
    from ai import analyze_spending
    result = analyze_spending(transactions)
    return jsonify({"insight": result.get("summary", "No insight available.")})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)