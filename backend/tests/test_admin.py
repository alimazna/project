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
            json={"code": "pro", "name": "Pro"},
            headers=second,
        )
        assert resp.status_code == 403


class TestPlanCRUD:
    def test_super_creates_and_updates(self, client):
        headers = _make_super(client)
        created = client.post(
            "/api/v1/admin/plans",
            json={
                "code": "pro",
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
        assert item["code"] == "pro"
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
        payload = {"code": "free", "name": "Free"}
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
