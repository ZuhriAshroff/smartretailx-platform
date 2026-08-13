def test_register_creates_a_customer_account(client):
    response = client.post(
        "/v1/auth/register",
        json={"email": "gina@smartretailx.com", "password": "password123", "full_name": "Gina Customer"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["role"] == "customer"
    assert body["email"] == "gina@smartretailx.com"


def test_register_rejects_a_duplicate_email(client):
    payload = {"email": "harry@smartretailx.com", "password": "password123", "full_name": "Harry Customer"}
    client.post("/v1/auth/register", json=payload)
    response = client.post("/v1/auth/register", json=payload)
    assert response.status_code == 409


def test_login_returns_a_bearer_token_for_valid_credentials(client):
    client.post(
        "/v1/auth/register",
        json={"email": "ivy@smartretailx.com", "password": "password123", "full_name": "Ivy Customer"},
    )
    response = client.post("/v1/auth/login", json={"email": "ivy@smartretailx.com", "password": "password123"})
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_rejects_an_invalid_password(client):
    client.post(
        "/v1/auth/register",
        json={"email": "jack@smartretailx.com", "password": "password123", "full_name": "Jack Customer"},
    )
    response = client.post("/v1/auth/login", json={"email": "jack@smartretailx.com", "password": "wrong"})
    assert response.status_code == 401
