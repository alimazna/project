"""Auth flow tests: register, login, refresh, RBAC, user isolation."""



def test_register_first_user_is_super_admin(client):
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": "a@b.com", "password": "password123", "display_name": "A"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["access_token"]
    assert body["refresh_token"]

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.status_code == 200
    assert "super_admin" in me.json()["roles"]
    assert "user" in me.json()["roles"]


def test_register_duplicate_email(client):
    payload = {"email": "dup@b.com", "password": "password123"}
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    assert client.post("/api/v1/auth/register", json=payload).status_code == 409


def test_login_wrong_password(client):
    client.post("/api/v1/auth/register", json={"email": "w@b.com", "password": "password123"})
    resp = client.post("/api/v1/auth/login", json={"email": "w@b.com", "password": "wrongpass1"})
    assert resp.status_code == 401


def test_login_and_refresh(client):
    client.post("/api/v1/auth/register", json={"email": "r@b.com", "password": "password123"})
    login = client.post("/api/v1/auth/login", json={"email": "r@b.com", "password": "password123"})
    body = login.json()
    assert body["access_token"]

    refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": body["refresh_token"]})
    assert refresh.status_code == 200
    assert refresh.json()["access_token"]

    logout = client.post("/api/v1/auth/logout", json={"refresh_token": body["refresh_token"]})
    assert logout.status_code == 200

    # Refresh token rotated/revoked — reuse fails
    reuse = client.post("/api/v1/auth/refresh", json={"refresh_token": body["refresh_token"]})
    assert reuse.status_code == 401


def test_me_requires_auth(client):
    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.get("/api/v1/auth/me", headers={"Authorization": "Bearer garbage"}).status_code == 401


def test_second_user_is_not_admin(client):
    client.post("/api/v1/auth/register", json={"email": "first@b.com", "password": "password123"})
    resp = client.post("/api/v1/auth/register", json={"email": "second@b.com", "password": "password123"})
    me = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {resp.json()['access_token']}"}
    )
    assert "super_admin" not in me.json()["roles"]


def test_bootstrap_super_admin_endpoint(client, engine_factory):
    resp = client.post(
        "/api/v1/auth/bootstrap-super-admin",
        json={"email": "boot@b.com", "password": "password123"},
    )
    assert resp.status_code == 201
    # second call conflicts
    resp2 = client.post(
        "/api/v1/auth/bootstrap-super-admin",
        json={"email": "other@b.com", "password": "password123"},
    )
    assert resp2.status_code == 409
