"""Super-admin plan CRUD tests: RBAC, lifecycle, version audit."""


def _register(client, email: str) -> dict:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "display_name": "X"},
    )
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _make_super(client):
    """Second registered user becomes super_admin in this fixture? First user is super_admin."""
    return _register(client, "boss@x.com")


class TestRBAC:
    def test_requires_auth(self, client):
        assert client.get("/api/v1/admin/plans").status_code == 401

    def test_regular_user_forbidden(self, client):
        # first registered user becomes super_admin; second stays regular
        _register(client, "first@x.com")
        _register(client, "user@x.com")
        login = client.post("/api/v1/auth/login", json={"email": "user@x.com", "password": "password123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        assert client.get("/api/v1/admin/plans", headers=headers).status_code == 403

    def test_non_super_cannot_create(self, client):
        # first user is super_admin; second is regular (unique ordering by id asc)
        _register(client, "first@x.com")
        second = _register(client, "second@x.com")
        resp = client.post(
            "/api/v1/admin/plans",
            json={"code": "rbac-pro", "name": "RBAC Pro"},
            headers=second,
        )
        assert resp.status_code == 403


class TestPlanCRUD:
    def test_super_creates_and_updates(self, client):
        headers = _make_super(client)
        created = client.post(
            "/api/v1/admin/plans",
            json={
                "code": "pro-custom",
                "name": "Pro Trader",
                "display_price": "$19",
                "billing_interval": "monthly",
                "features": ["Unlimited watchlists", "Charts"],
                "quotas": {"watchlists": 50, "alerts": 50},
            },
            headers=headers,
        )
        assert created.status_code == 201
        item = created.json()["item"]
        assert item["code"] == "pro-custom"
        assert item["quotas"]["watchlists"] == 50
        plan_id = item["id"]

        updated = client.put(
            f"/api/v1/admin/plans/{plan_id}",
            json={"display_price": "$29", "is_active": False},
            headers=headers,
        )
        assert updated.status_code == 200
        assert updated.json()["item"]["display_price"] == "$29"
        assert updated.json()["item"]["is_active"] is False
        # audit bump: create (1->2) then update (2->3)
        assert updated.json()["item"]["version"] == 3

    def test_duplicate_code_conflict(self, client):
        headers = _make_super(client)
        payload = {"code": "dup-code", "name": "Dup"}
        assert client.post("/api/v1/admin/plans", json=payload, headers=headers).status_code == 201
        assert client.post("/api/v1/admin/plans", json=payload, headers=headers).status_code == 409

    def test_archive_and_versions(self, client):
        headers = _make_super(client)
        plan_id = client.post(
            "/api/v1/admin/plans", json={"code": "demo", "name": "Demo"}, headers=headers
        ).json()["item"]["id"]
        assert client.delete(f"/api/v1/admin/plans/{plan_id}", headers=headers).status_code == 204

        versions = client.get(f"/api/v1/admin/plans/{plan_id}/versions", headers=headers)
        assert len(versions.json()["versions"]) == 2  # create + archive

        listing = client.get("/api/v1/admin/plans", headers=headers)
        archived = [p for p in listing.json()["items"] if p["id"] == plan_id][0]
        assert archived["is_archived"] is True

    def test_public_plans_hide_archived(self, client):
        headers = _make_super(client)
        active = client.post(
            "/api/v1/admin/plans", json={"code": "visible", "name": "Visible"}, headers=headers
        ).json()["item"]["id"]
        client.delete(f"/api/v1/admin/plans/{active}", headers=headers)

        public = client.get("/api/v1/plans").json()["items"]
        assert not any(p["code"] == "visible" for p in public)


class TestUserAdmin:
    def test_super_lists_users(self, client):
        headers = _make_super(client)
        resp = client.get("/api/v1/admin/users", headers=headers)
        assert resp.status_code == 200
        emails = {u["email"] for u in resp.json()["items"]}
        assert "boss@x.com" in emails

    def test_regular_cannot_list_users(self, client):
        _register(client, "first@x.com")
        _register(client, "peon@x.com")
        login = client.post(
            "/api/v1/auth/login", json={"email": "peon@x.com", "password": "password123"}
        )
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        assert client.get("/api/v1/admin/users", headers=headers).status_code == 403

    def test_suspend_and_activate(self, client):
        headers = _make_super(client)
        _register(client, "victim@x.com")
        uid = [
            u["id"]
            for u in client.get("/api/v1/admin/users", headers=headers).json()["items"]
            if u["email"] == "victim@x.com"
        ][0]
        sus = client.put(f"/api/v1/admin/users/{uid}", json={"is_suspended": True}, headers=headers)
        assert sus.status_code == 200
        assert sus.json()["item"]["is_suspended"] is True
        # suspended user cannot log in anymore
        login = client.post(
            "/api/v1/auth/login", json={"email": "victim@x.com", "password": "password123"}
        )
        assert login.status_code == 403
        react = client.put(f"/api/v1/admin/users/{uid}", json={"is_suspended": False}, headers=headers)
        assert react.json()["item"]["is_suspended"] is False

    def test_cannot_modify_self(self, client):
        headers = _make_super(client)
        uid = client.get("/api/v1/admin/users", headers=headers).json()["items"][0]["id"]
        resp = client.put(f"/api/v1/admin/users/{uid}", json={"is_suspended": True}, headers=headers)
        assert resp.status_code == 400

    def test_assign_roles(self, client):
        headers = _make_super(client)
        _register(client, "staff@x.com")
        uid = [
            u["id"]
            for u in client.get("/api/v1/admin/users", headers=headers).json()["items"]
            if u["email"] == "staff@x.com"
        ][0]
        resp = client.put(
            f"/api/v1/admin/users/{uid}", json={"roles": ["admin"]}, headers=headers
        )
        assert resp.status_code == 200
        assert "admin" in resp.json()["item"]["roles"]
        assert "super_admin" not in resp.json()["item"]["roles"]


class TestSystemOverview:
    def test_admin_can_view_system(self, client):
        headers = _make_super(client)
        resp = client.get("/api/v1/admin/system", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["counts"]["users"] >= 1
        assert body["counts"]["plans"] == 2
        assert any(b["provider"] == "demo" for b in body["billing"])
        assert isinstance(body["providers"], list)

    def test_regular_denied(self, client):
        _register(client, "norm1@x.com")
        _register(client, "norm2@x.com")
        login = client.post(
            "/api/v1/auth/login", json={"email": "norm2@x.com", "password": "password123"}
        )
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        assert client.get("/api/v1/admin/system", headers=headers).status_code == 403


class TestSymbolAdmin:
    def test_list_symbols_shows_active_state(self, client):
        headers = _make_super(client)
        resp = client.get("/api/v1/admin/symbols", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body["symbols"], list)
        assert any(s["symbol"] == "BTC/USD" for s in body["symbols"])
        btc = next(s for s in body["symbols"] if s["symbol"] == "BTC/USD")
        assert btc["is_active"] is True

    def test_super_can_disable_and_reenable(self, client):
        headers = _make_super(client)
        resp = client.put("/api/v1/admin/symbols/BTC/USD", json={"is_active": False}, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["item"]["is_active"] is False

        resp = client.put("/api/v1/admin/symbols/BTC/USD", json={"is_active": True}, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["item"]["is_active"] is True

    def test_regular_admin_cannot_toggle(self, client):
        _make_super(client)  # first user -> super_admin
        headers = _register(client, "admin2@x.com")  # second user -> regular
        # regular user cannot list admin symbols
        assert client.get("/api/v1/admin/symbols", headers=headers).status_code == 403
        # nor toggle them
        resp = client.put("/api/v1/admin/symbols/BTC/USD", json={"is_active": False}, headers=headers)
        assert resp.status_code == 403

    def test_unknown_symbol_404(self, client):
        headers = _make_super(client)
        resp = client.put("/api/v1/admin/symbols/NOPE/USD", json={"is_active": False}, headers=headers)
        assert resp.status_code == 404

    def test_sync_catalog_loads_all_50plus(self, client):
        headers = _make_super(client)
        resp = client.post("/api/v1/admin/symbols/sync-catalog", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["added"] >= 0
        # catalog should hold more than the previous 17-21 baseline
        assert body["catalog_size"] >= 50
