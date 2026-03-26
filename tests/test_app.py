import os
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from app import app  # noqa: E402
from db import get_collection, reset_client  # noqa: E402


@pytest.fixture(autouse=True)
def setup_app_env():
    os.environ["TESTING"] = "1"
    os.environ["USE_MOCK_DB"] = "1"
    reset_client()
    with app.test_client() as client:
        # Clear data between tests
        collection = get_collection()
        collection.delete_many({})
        yield client
    reset_client()


def create_transaction(client, **overrides):
    payload = {
        "title": "Coffee",
        "amount": 5.0,
        "type": "expense",
        "category": "food",
        "date": "2026-03-01",
        "notes": "morning coffee",
    }
    payload.update(overrides)
    return client.post("/transactions", json=payload)


def test_health(setup_app_env):
    client = setup_app_env
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_db_health_with_mock(setup_app_env):
    client = setup_app_env
    resp = client.get("/db-health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_add_transaction(setup_app_env):
    client = setup_app_env
    resp = create_transaction(client, title="Salary", amount=1000, type="income", category="salary")
    body = resp.get_json()
    assert resp.status_code == 201
    assert body["title"] == "Salary"
    assert "id" in body


def test_add_transaction_missing_field(setup_app_env):
    client = setup_app_env
    resp = client.post("/transactions", json={"title": "Bad Data"})
    assert resp.status_code == 400


def test_get_transactions_filters(setup_app_env):
    client = setup_app_env
    create_transaction(client, category="food")
    create_transaction(client, category="transport", title="Bus", amount=2.5)
    resp = client.get("/transactions", query_string={"category": "transport"})
    data = resp.get_json()
    assert len(data) == 1
    assert data[0]["category"] == "transport"


def test_update_transaction(setup_app_env):
    client = setup_app_env
    resp = create_transaction(client, amount=10)
    txn_id = resp.get_json()["id"]
    update_resp = client.put(f"/transactions/{txn_id}", json={"amount": 12.5, "notes": "updated"})
    updated = update_resp.get_json()
    assert update_resp.status_code == 200
    assert updated["amount"] == 12.5
    assert updated["notes"] == "updated"


def test_delete_transaction(setup_app_env):
    client = setup_app_env
    resp = create_transaction(client)
    txn_id = resp.get_json()["id"]
    delete_resp = client.delete(f"/transactions/{txn_id}")
    assert delete_resp.status_code == 200
    list_resp = client.get("/transactions")
    assert list_resp.get_json() == []


def test_summary_totals(setup_app_env):
    client = setup_app_env
    create_transaction(client, title="Paycheck", amount=2000, type="income", category="salary")
    create_transaction(client, title="Rent", amount=800, type="expense", category="rent")
    resp = client.get("/summary")
    summary = resp.get_json()
    assert summary["total_income"] == 2000
    assert summary["total_expense"] == 800
    assert summary["balance"] == 1200


def test_monthly_summary(setup_app_env):
    client = setup_app_env
    create_transaction(client, date="2026-02-15", amount=100, category="food")
    create_transaction(client, date="2026-03-01", amount=50, category="food")
    resp = client.get("/summary/monthly")
    months = resp.get_json()
    months_sorted = sorted(months, key=lambda m: m["month"])
    assert len(months_sorted) == 2
    assert months_sorted[0]["month"] == "2026-02"
    assert months_sorted[0]["expense"] == 100


def test_ai_spending_insights(setup_app_env):
    client = setup_app_env
    create_transaction(client, category="rent", amount=500)
    create_transaction(client, category="food", amount=200)
    resp = client.get("/ai/spending-insights")
    text = resp.get_json()["insight"].lower()
    assert "rent" in text or "food" in text


def test_ai_spending_insights_no_data(setup_app_env):
    client = setup_app_env
    resp = client.get("/ai/spending-insights")
    assert resp.status_code == 200
    assert "No transactions yet" in resp.get_json()["insight"]


def test_invalid_transaction_id_update(setup_app_env):
    client = setup_app_env
    resp = client.put("/transactions/not-an-id", json={"title": "X"})
    assert resp.status_code == 400
