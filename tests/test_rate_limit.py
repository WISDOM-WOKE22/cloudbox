from unittest.mock import AsyncMock, patch

import httpx


class TestLoginRateLimit:
    @patch("cloudbox_api.core.rate_limit.get_redis")
    async def test_rate_limit_blocks_after_max_attempts(
        self, mock_get_redis, client: httpx.AsyncClient, registered_user: dict
    ):
        mock_redis = AsyncMock()
        mock_get_redis.return_value = mock_redis

        # Simulate being over the limit
        mock_redis.incr.return_value = 11
        mock_redis.ttl.return_value = 45

        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "testuser@example.com", "password": "securepass123"},
        )
        assert response.status_code == 429
        assert "Too many login attempts" in response.json()["detail"]
        assert response.headers.get("retry-after") == "45"

    @patch("cloudbox_api.core.rate_limit.get_redis")
    async def test_rate_limit_allows_under_limit(
        self, mock_get_redis, client: httpx.AsyncClient, registered_user: dict
    ):
        mock_redis = AsyncMock()
        mock_get_redis.return_value = mock_redis
        mock_redis.incr.return_value = 1

        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "testuser@example.com", "password": "securepass123"},
        )
        assert response.status_code == 200

    @patch("cloudbox_api.core.rate_limit.get_redis")
    async def test_rate_limit_sets_expiry_on_first_attempt(
        self, mock_get_redis, client: httpx.AsyncClient, registered_user: dict
    ):
        mock_redis = AsyncMock()
        mock_get_redis.return_value = mock_redis
        mock_redis.incr.return_value = 1

        await client.post(
            "/api/v1/auth/login",
            data={"username": "testuser@example.com", "password": "securepass123"},
        )

        mock_redis.expire.assert_called_once()

    async def test_login_works_without_redis(
        self, client: httpx.AsyncClient, registered_user: dict
    ):
        # No mocking — Redis is None in tests, should pass through
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "testuser@example.com", "password": "securepass123"},
        )
        assert response.status_code == 200


class TestUserCache:
    @patch("cloudbox_api.dependencies.auth.get_cached_user")
    @patch("cloudbox_api.dependencies.auth.cache_user")
    async def test_cache_populated_on_miss(
        self,
        mock_cache_user,
        mock_get_cached,
        client: httpx.AsyncClient,
        auth_header: dict,
    ):
        mock_get_cached.return_value = None  # cache miss

        response = await client.get("/api/v1/users/me", headers=auth_header)
        assert response.status_code == 200

        mock_cache_user.assert_called_once()

    @patch("cloudbox_api.dependencies.auth.get_cached_user")
    async def test_cache_hit_skips_db(
        self,
        mock_get_cached,
        client: httpx.AsyncClient,
        auth_header: dict,
        registered_user: dict,
    ):
        mock_get_cached.return_value = {
            "id": registered_user["id"],
            "email": registered_user["email"],
            "username": registered_user["username"],
            "is_active": True,
            "created_at": registered_user["created_at"],
            "updated_at": registered_user["updated_at"],
        }

        response = await client.get("/api/v1/users/me", headers=auth_header)
        assert response.status_code == 200
        assert response.json()["username"] == registered_user["username"]

    @patch("cloudbox_api.services.user.invalidate_user_cache")
    async def test_cache_invalidated_on_update(
        self,
        mock_invalidate,
        client: httpx.AsyncClient,
        auth_header: dict,
        registered_user: dict,
    ):
        response = await client.patch(
            "/api/v1/users/me",
            headers=auth_header,
            json={"username": "cache_test_user"},
        )
        assert response.status_code == 200
        mock_invalidate.assert_called_once()
