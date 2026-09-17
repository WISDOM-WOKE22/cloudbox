import httpx


class TestRegister:
    async def test_register_success(self, client: httpx.AsyncClient):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "new@example.com",
                "username": "newuser",
                "password": "securepass123",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "new@example.com"
        assert data["username"] == "newuser"
        assert data["is_active"] is True
        assert "id" in data
        assert "hashed_password" not in data

    async def test_register_duplicate_email(
        self, client: httpx.AsyncClient, registered_user: dict
    ):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "testuser@example.com",
                "username": "different",
                "password": "securepass123",
            },
        )
        assert response.status_code == 409
        assert "Email already registered" in response.json()["detail"]

    async def test_register_duplicate_username(
        self, client: httpx.AsyncClient, registered_user: dict
    ):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "other@example.com",
                "username": "testuser",
                "password": "securepass123",
            },
        )
        assert response.status_code == 409
        assert "Username already taken" in response.json()["detail"]

    async def test_register_invalid_email(self, client: httpx.AsyncClient):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "username": "validuser",
                "password": "securepass123",
            },
        )
        assert response.status_code == 422

    async def test_register_short_password(self, client: httpx.AsyncClient):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "valid@example.com",
                "username": "validuser",
                "password": "short",
            },
        )
        assert response.status_code == 422

    async def test_register_invalid_username(self, client: httpx.AsyncClient):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "valid@example.com",
                "username": "ab",
                "password": "securepass123",
            },
        )
        assert response.status_code == 422


class TestLogin:
    async def test_login_success(
        self, client: httpx.AsyncClient, registered_user: dict
    ):
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "testuser@example.com", "password": "securepass123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(
        self, client: httpx.AsyncClient, registered_user: dict
    ):
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "testuser@example.com", "password": "wrongpassword"},
        )
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    async def test_login_nonexistent_email(self, client: httpx.AsyncClient):
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "nobody@example.com", "password": "securepass123"},
        )
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]


class TestRefresh:
    async def test_refresh_success(
        self, client: httpx.AsyncClient, auth_tokens: dict
    ):
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": auth_tokens["refresh_token"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["refresh_token"] != auth_tokens["refresh_token"]

    async def test_refresh_revoked_token(
        self, client: httpx.AsyncClient, auth_tokens: dict
    ):
        # Use the token once (rotates it)
        await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": auth_tokens["refresh_token"]},
        )
        # Try to use it again (should be revoked)
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": auth_tokens["refresh_token"]},
        )
        assert response.status_code == 401

    async def test_refresh_bogus_token(self, client: httpx.AsyncClient):
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "totally-fake-token"},
        )
        assert response.status_code == 401


class TestLogout:
    async def test_logout_success(
        self, client: httpx.AsyncClient, auth_tokens: dict
    ):
        response = await client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": auth_tokens["refresh_token"]},
        )
        assert response.status_code == 200
        assert "Successfully logged out" in response.json()["message"]

    async def test_refresh_after_logout(
        self, client: httpx.AsyncClient, auth_tokens: dict
    ):
        await client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": auth_tokens["refresh_token"]},
        )
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": auth_tokens["refresh_token"]},
        )
        assert response.status_code == 401
