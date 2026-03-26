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
    return jsonify(transactions)


@app.route("/transactions", methods=["POST"])
def add_transaction():
    data = request.get_json()

    required_fields = ["title", "amount", "type", "category", "date"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    transactions.append(data)
    return jsonify(data), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
