def test_register_and_login(client):
    register_payload = {
        "full_name": "Test User", "email": "test@example.com", "phone": "+919876543210",
        "password": "StrongPass123", "role": "customer",
    }
    resp = client.post("/api/v1/auth/register", json=register_payload)
    assert resp.status_code == 201
    body = resp.json()
    assert body["success"] is True
    assert "access_token" in body["data"]

    resp = client.post("/api/v1/auth/login", json={"phone": "+919876543210", "password": "StrongPass123"})
    assert resp.status_code == 200
    assert resp.json()["data"]["access_token"]


def test_login_wrong_password_fails(client):
    client.post("/api/v1/auth/register", json={
        "full_name": "Test User 2", "phone": "+919876500000", "password": "StrongPass123",
    })
    resp = client.post("/api/v1/auth/login", json={"phone": "+919876500000", "password": "WrongPass"})
    assert resp.status_code == 401


def test_get_profile_requires_auth(client):
    resp = client.get("/api/v1/users/me")
    assert resp.status_code in (401, 403)
