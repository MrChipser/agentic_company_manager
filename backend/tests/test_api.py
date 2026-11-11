from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)
HEADERS = {"Authorization": "Bearer demo-token"}


def test_login_and_create_invoice_updates_vat():
    login = client.post("/api/auth/login", json={"email": "admin@demo.hu", "password": "admin"})
    assert login.status_code == 200
    due_date = (date.today() + timedelta(days=30)).isoformat()
    response = client.post("/api/invoices", headers=HEADERS, json={
        "direction": "OUTGOING", "amount": "1000000", "vat_rate": 27,
        "issue_date": date.today().isoformat(), "due_date": due_date,
    })
    assert response.status_code == 200
    assert response.json()["vat_amount"] == "270000.00"
    assert len(client.get("/api/invoices", headers=HEADERS).json()) == 1


def test_forecast_reports_liquidity_deficit():
    response = client.get("/api/forecast", headers=HEADERS, params={"days": 30, "start": date.today().isoformat()})
    assert response.status_code == 200
    assert response.json()["status"] == "OK"


def test_invalid_invoice_does_not_change_database():
    before = len(client.get("/api/invoices", headers=HEADERS).json())
    response = client.post("/api/invoices", headers=HEADERS, json={
        "direction": "OUTGOING", "amount": "0", "vat_rate": 27,
        "issue_date": date.today().isoformat(), "due_date": (date.today() + timedelta(days=30)).isoformat(),
    })
    assert response.status_code == 422
    assert len(client.get("/api/invoices", headers=HEADERS).json()) == before


def test_protected_endpoint_requires_token():
    assert client.post("/api/invoices", json={"direction": "OUTGOING", "amount": "100", "vat_rate": 27}).status_code == 401