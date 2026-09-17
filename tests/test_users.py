import httpx


class TestGetMe:
    async def test_get_me_authenticated(
        self, client: httpx.AsyncClient, auth_header: dict, registered_user: dict
    ):
        response = await client.get("/api/v1/users/me", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "testuser@example.com"
        assert data["username"] == "testuser"
        assert data["is_active"] is True
        assert "hashed_password" not in data

    async def test_get_me_unauthenticated(self, client: httpx.AsyncClient):
        response = await client.get("/api/v1/users/me")
        assert response.status_code == 401


class TestUpdateMe:
    async def test_update_username(
        self, client: httpx.AsyncClient, auth_header: dict, registered_user: dict
    ):
        response = await client.patch(
            "/api/v1/users/me",
            headers=auth_header,
            json={"username": "updated_name"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "updated_name"
        assert data["email"] == "testuser@example.com"

    async def test_update_email(
        self, client: httpx.AsyncClient, auth_header: dict, registered_user: dict
    ):
        response = await client.patch(
            "/api/v1/users/me",
            headers=auth_header,
            json={"email": "newemail@example.com"},
        )
        assert response.status_code == 200
        assert response.json()["email"] == "newemail@example.com"

    async def test_update_empty_body(
        self, client: httpx.AsyncClient, auth_header: dict, registered_user: dict
    ):
        response = await client.patch(
            "/api/v1/users/me", headers=auth_header, json={}
        )
        assert response.status_code == 200
        assert response.json()["username"] == "testuser"

    async def test_update_duplicate_username(
        self, client: httpx.AsyncClient, auth_header: dict, registered_user: dict
    ):
        # Register a second user
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "other@example.com",
                "username": "taken_name",
                "password": "securepass123",
            },
        )
        response = await client.patch(
            "/api/v1/users/me",
            headers=auth_header,
            json={"username": "taken_name"},
        )
        assert response.status_code == 409

    async def test_update_unauthenticated(self, client: httpx.AsyncClient):
        response = await client.patch(
            "/api/v1/users/me", json={"username": "hacker"}
        )
        assert response.status_code == 401
