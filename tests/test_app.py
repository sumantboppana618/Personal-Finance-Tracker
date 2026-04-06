import os

import pytest
import werkzeug

# Some newer Werkzeug builds remove __version__; Flask 2.2 expects it during testing.
if not hasattr(werkzeug, "__version__"):
    werkzeug.__version__ = "patched"

# Force the app to use the in-memory mock database for tests
os.environ["USE_MOCK_DB"] = "1"
os.environ["TESTING"] = "1"

from app import app  # noqa: E402
from db import clear_transactions  # noqa: E402


@pytest.fixture(autouse=True)
def _clean_db():
    clear_transactions()
    yield
    clear_transactions()


@pytest.fixture()
def client():
    return app.test_client()


def _sample_tx(**overrides):
    base = {
        "title": "Salary",
        "amount": 1000,
        "type": "income",
        "category": "income",
        "date": "2024-03-01",
    }
    base.update(overrides)
    return base


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json()["status"] == "ok"


def test_db_health_mock(client):
    res = client.get("/db-health")
    assert res.status_code == 200
    assert res.get_json()["status"] == "ok"


def test_create_and_list_transactions(client):
    res = client.post("/transactions", json=_sample_tx())
    assert res.status_code == 201
    tx_id = res.get_json()["id"]

    res = client.get("/transactions")
    data = res.get_json()
    assert len(data) == 1
    assert data[0]["id"] == tx_id
    assert data[0]["title"] == "Salary"


def test_filters_by_type_and_category(client):
    client.post("/transactions", json=_sample_tx(title="Salary"))
    client.post("/transactions", json=_sample_tx(title="Groceries", type="expense", category="food"))

    res = client.get("/transactions?type=expense&category=food")
    data = res.get_json()
    assert len(data) == 1
    assert data[0]["title"] == "Groceries"


def test_filters_by_date_range(client):
    client.post("/transactions", json=_sample_tx(title="Old", date="2024-01-01"))
    client.post("/transactions", json=_sample_tx(title="New", date="2024-03-15"))

    res = client.get("/transactions?start_date=2024-03-01&end_date=2024-03-31")
    titles = {row["title"] for row in res.get_json()}
    assert "New" in titles
    assert "Old" not in titles


def test_update_transaction(client):
    res = client.post("/transactions", json=_sample_tx(title="Initial"))
    tx_id = res.get_json()["id"]

    res = client.put(f"/transactions/{tx_id}", json=_sample_tx(title="Updated"))
    assert res.status_code == 200
    assert res.get_json()["title"] == "Updated"


def test_delete_transaction(client):
    res = client.post("/transactions", json=_sample_tx(title="ToDelete"))
    tx_id = res.get_json()["id"]

    res = client.delete(f"/transactions/{tx_id}")
    assert res.status_code == 200

    res = client.get("/transactions")
    assert res.get_json() == []


def test_summary_and_monthly(client):
    client.post("/transactions", json=_sample_tx(amount=1000, date="2024-03-01"))
    client.post("/transactions", json=_sample_tx(amount=200, type="expense", category="food", date="2024-03-02"))
    client.post("/transactions", json=_sample_tx(amount=100, type="expense", category="transport", date="2024-02-10"))

    res = client.get("/summary")
    summary = res.get_json()
    assert summary["total_income"] == 1000
    assert summary["total_expense"] == 300
    assert summary["balance"] == 700

    res = client.get("/summary/monthly")
    months = res.get_json()
    assert any(m["month"] == "2024-03" and m["expense"] == 200 for m in months)


def test_ai_insight_returns_message(client):
    client.post("/transactions", json=_sample_tx(amount=50, type="expense", category="food"))
    res = client.get("/ai/spending-insights")
    assert res.status_code == 200
    assert "insight" in res.get_json()


def test_reset_transactions(client):
    client.post("/transactions", json=_sample_tx())
    res = client.post("/transactions/reset")
    assert res.status_code == 200
    res = client.get("/transactions")
    assert res.get_json() == []


def test_validation_missing_field(client):
    res = client.post("/transactions", json={"title": "oops"})
    assert res.status_code == 400
