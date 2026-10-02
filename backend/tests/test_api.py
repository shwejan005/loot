import os
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Override developer machine settings before importing the application. The
# tests stay offline and never connect to the developer's configured database.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["CREATE_TABLES_ON_STARTUP"] = "false"
os.environ["JWT_SECRET"] = "test-secret-only"
os.environ["OPENAI_API_KEY"] = ""
os.environ["CORS_ORIGINS"] = "http://localhost:3000,http://127.0.0.1:3000,capacitor://localhost"

from app.config import settings
from app.db import Base, get_db
from app.main import app
from app.seed.load import seed_cards


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(settings, "jwt_secret", "test-secret-only")
    monkeypatch.setattr(settings, "openai_api_key", "")
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    test_session = sessionmaker(autoflush=False, autocommit=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        with test_session() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    with test_session() as db:
        seed_cards(db)

    # Avoid the app lifespan, which connects to the configured development DB.
    test_client = TestClient(app)
    try:
        yield test_client
    finally:
        test_client.close()
        app.dependency_overrides.pop(get_db, None)
        engine.dispose()


def assert_status(response, expected_status):
    assert response.status_code == expected_status, response.text
    return response.json() if response.content else None


def register_user(client):
    suffix = uuid4().hex[:12]
    identity = {
        "username": f"test_{suffix}",
        "email": f"test_{suffix}@example.com",
        "password": "test-password-123",
    }
    result = assert_status(client.post("/auth/register", json=identity), 201)
    headers = {"Authorization": f"Bearer {result['access_token']}"}
    return identity, headers


def test_wallet_purchase_and_analytics_flow(client):
    assert_status(client.get("/health"), 200)
    issuers = assert_status(client.get("/catalog/issuers"), 200)
    products = assert_status(client.get("/catalog/cards"), 200)
    assert issuers and products

    assert_status(client.get("/cards/"), 401)
    identity, headers = register_user(client)
    assert assert_status(client.get("/auth/me", headers=headers), 200)["username"] == identity["username"]
    assert_status(
        client.post(
            "/auth/login",
            json={"username": identity["email"], "password": identity["password"]},
        ),
        200,
    )
    assert_status(client.post("/auth/register", json=identity), 400)

    card = assert_status(
        client.post(
            "/cards/",
            headers=headers,
            json={"card_product_id": products[0]["id"], "last_four": "4242", "is_default": True},
        ),
        201,
    )
    assert assert_status(client.get("/cards/", headers=headers), 200)[0]["id"] == card["id"]

    recommendation = assert_status(
        client.post("/route/", headers=headers, json={"merchant_name": "Swiggy", "amount": 1200}),
        200,
    )
    assert recommendation["category_detected"] == "dining"
    assert recommendation["recommended"]["card"]["id"] == card["id"]

    purchase = assert_status(
        client.post(
            "/transactions/",
            headers=headers,
            json={"card_id": card["id"], "merchant_raw": "Swiggy", "amount": 1200},
        ),
        201,
    )
    assert purchase["category"] == "dining"

    sms = assert_status(
        client.post(
            "/transactions/sms",
            headers=headers,
            json={
                "sms_body": (
                    f"Your card XX4242 debited for Rs.500 at Zomato on "
                    f"{datetime.now(timezone.utc):%d-%m-%Y}"
                )
            },
        ),
        201,
    )
    assert sms["source"] == "sms"
    assert sms["card_id"] == card["id"]
    assert float(sms["amount"]) == 500

    transactions = assert_status(client.get("/transactions/", headers=headers), 200)
    assert transactions["total"] == 2
    assert {item["id"] for item in transactions["items"]} == {purchase["id"], sms["id"]}
    assert_status(client.get(f"/transactions/{purchase['id']}", headers=headers), 200)

    month = datetime.now(timezone.utc).strftime("%Y-%m")
    report = assert_status(
        client.get(f"/analytics/monthly-report?month={month}", headers=headers),
        200,
    )
    assert float(report["total_spent"]) == 1700
    assert report["top_category"] == "dining"

    summary = assert_status(client.get("/analytics/summary", headers=headers), 200)
    assert summary["total_transactions"] == 2
    assert summary["card_count"] == 1
    categories = assert_status(client.get("/analytics/spending-by-category", headers=headers), 200)
    assert categories[0]["category"] == "dining"
    assert categories[0]["transaction_count"] == 2
    assert_status(client.get("/analytics/card-utilization", headers=headers), 200)


def test_web_and_capacitor_cors_origins(client):
    for origin in ("http://localhost:3000", "capacitor://localhost"):
        response = client.options(
            "/auth/login",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "authorization,content-type",
            },
        )
        assert response.status_code == 200, response.text
        assert response.headers["access-control-allow-origin"] == origin
        assert response.headers["access-control-allow-credentials"] == "true"
        assert "authorization" in response.headers["access-control-allow-headers"].lower()


def test_sms_import_rejects_non_purchase_and_refund_alerts(client):
    _, headers = register_user(client)

    non_transaction = assert_status(
        client.post(
            "/transactions/sms",
            headers=headers,
            json={"sms_body": "Your account balance is Rs.5000"},
        ),
        422,
    )
    assert "Could not parse" in non_transaction["detail"]

    refund = assert_status(
        client.post(
            "/transactions/sms",
            headers=headers,
            json={"sms_body": "Refund credited Rs.500 at Zomato"},
        ),
        422,
    )
    assert "cannot be imported" in refund["detail"]
