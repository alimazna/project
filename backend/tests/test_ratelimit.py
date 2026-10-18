"""Rate limiting on auth endpoints (register/login/refresh)."""


class TestRegisterRateLimit:
    def test_register_burst_is_limited(self, client):
        # 10 allowed per minute, then 429
        for i in range(10):
            resp = client.post(
                "/api/v1/auth/register",
                json={"email": f"u{i}@x.com", "password": "password123"},
            )
            assert resp.status_code == 201
        blocked = client.post(
            "/api/v1/auth/register",
            json={"email": "over@x.com", "password": "password123"},
        )
        assert blocked.status_code == 429


class TestLoginRateLimit:
    def test_login_burst_is_limited(self, client):
        client.post(
            "/api/v1/auth/register",
            json={"email": "l@x.com", "password": "password123"},
        )
        for _ in range(20):
            client.post("/api/v1/auth/login", json={"email": "l@x.com", "password": "bad"})
        blocked = client.post("/api/v1/auth/login", json={"email": "l@x.com", "password": "bad"})
        assert blocked.status_code == 429
