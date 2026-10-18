"""Watchlist API tests: auth-required CRUD + user isolation."""


def _auth(client, email: str = "w@b.com") -> str:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "display_name": "W"},
    )
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})
    return login.json()["access_token"]


def test_requires_auth(client):
    assert client.get("/api/v1/watchlists").status_code == 401
    assert client.post("/api/v1/watchlists", json={"name": "x"}).status_code == 401


def test_create_and_list(client):
    token = _auth(client)
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.post(
        "/api/v1/watchlists",
        json={"name": "Top", "symbols": ["btc/usd", "ETH/USD"]},
        headers=headers,
    )
    assert resp.status_code == 201
    body = resp.json()["watchlist"]
    assert body["name"] == "Top"
    # symbols normalized to uppercase
    assert body["symbols"] == ["BTC/USD", "ETH/USD"]

    listing = client.get("/api/v1/watchlists", headers=headers)
    assert len(listing.json()["watchlists"]) == 1


def test_update_and_delete(client):
    token = _auth(client)
    headers = {"Authorization": f"Bearer {token}"}
    wl = client.post(
        "/api/v1/watchlists", json={"name": "A", "symbols": ["BTC/USD"]}, headers=headers
    ).json()["watchlist"]

    upd = client.put(
        f"/api/v1/watchlists/{wl['id']}",
        json={"symbols": ["ETH/USD", "SOL/USD"]},
        headers=headers,
    )
    assert upd.json()["watchlist"]["symbols"] == ["ETH/USD", "SOL/USD"]

    assert (
        client.delete(f"/api/v1/watchlists/{wl['id']}", headers=headers).status_code == 204
    )
    assert client.get("/api/v1/watchlists", headers=headers).json()["watchlists"] == []


def test_user_isolation(client):
    a_token = _auth(client, "u1@b.com")
    b_token = _auth(client, "u2@b.com")
    headers_a = {"Authorization": f"Bearer {a_token}"}
    headers_b = {"Authorization": f"Bearer {b_token}"}

    wl = client.post(
        "/api/v1/watchlists", json={"name": "Secret", "symbols": []}, headers=headers_a
    ).json()["watchlist"]

    # user B cannot see or mutate A's watchlist
    assert client.get("/api/v1/watchlists", headers=headers_b).json()["watchlists"] == []
    assert (
        client.get(f"/api/v1/watchlists/{wl['id']}", headers=headers_b).status_code == 404
    )
    assert (
        client.delete(f"/api/v1/watchlists/{wl['id']}", headers=headers_b).status_code == 404
    )
