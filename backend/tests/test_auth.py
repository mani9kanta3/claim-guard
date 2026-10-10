def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json()["database"] == "ok"


def test_login_success(client):
    response = client.post(
        "/api/auth/login",
        json={"email": "Customer@Demo.com", "password": "password123"},
    )
    data = response.get_json()

    assert response.status_code == 200
    assert "access_token" in data
    assert data["user"]["role"] == "CUSTOMER"
    assert "password_hash" not in data["user"]


def test_login_wrong_password(client):
    response = client.post(
        "/api/auth/login",
        json={"email": "customer@demo.com", "password": "wrong-password"},
    )
    assert response.status_code == 401
    assert response.get_json()["error"] == "INVALID_LOGIN"


def test_login_missing_fields(client):
    response = client.post("/api/auth/login", json={})
    assert response.status_code == 400
    assert response.get_json()["error"] == "VALIDATION_ERROR"


def test_register_short_password(client):
    response = client.post(
        "/api/auth/register",
        json={"full_name": "Test User", "email": "test@demo.com", "password": "123"},
    )
    assert response.status_code == 400


def test_register_duplicate_email(client):
    response = client.post(
        "/api/auth/register",
        json={"full_name": "Copy", "email": "customer@demo.com", "password": "password123"},
    )
    assert response.status_code == 409


def test_me_without_token(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    assert response.get_json()["error"] == "UNAUTHORIZED"


def test_me_with_token(client, officer_headers):
    response = client.get("/api/auth/me", headers=officer_headers)
    assert response.status_code == 200
    assert response.get_json()["role"] == "OFFICER"


def test_wrong_role_gets_403(client, customer_headers):
    response = client.get("/api/dashboard/summary", headers=customer_headers)
    assert response.status_code == 403


def test_unknown_url_returns_json_404(client):
    response = client.get("/api/does-not-exist")
    assert response.status_code == 404
    assert response.get_json()["error"] == "NOT_FOUND"
