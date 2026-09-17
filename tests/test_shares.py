import httpx


async def _register_and_login(client, email, username):
    """Register a user and return (user_data, auth_header)."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "username": username, "password": "securepass123"},
    )
    user_data = reg.json()
    login = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "securepass123"},
    )
    token = login.json()["access_token"]
    return user_data, {"Authorization": f"Bearer {token}"}


async def _create_file(client, auth_header, name="test.pdf"):
    resp = await client.post(
        "/api/v1/files/",
        headers=auth_header,
        json={"name": name, "mime_type": "application/pdf", "size": 1024},
    )
    return resp.json()


async def _create_folder(client, auth_header, name="Shared"):
    resp = await client.post(
        "/api/v1/folders/",
        headers=auth_header,
        json={"name": name},
    )
    return resp.json()


class TestFileShares:
    async def test_share_file(self, client: httpx.AsyncClient):
        alice, alice_h = await _register_and_login(client, "alice@test.com", "alice")
        bob, _ = await _register_and_login(client, "bob@test.com", "bob")
        file = await _create_file(client, alice_h)

        response = await client.post(
            f"/api/v1/files/{file['id']}/shares",
            headers=alice_h,
            json={"shared_with_id": bob["id"], "permission": "viewer"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["shared_with_id"] == bob["id"]
        assert data["permission"] == "viewer"
        assert data["resource_type"] == "file"
        assert data["resource_id"] == file["id"]

    async def test_share_file_duplicate(self, client: httpx.AsyncClient):
        alice, alice_h = await _register_and_login(client, "alice@test.com", "alice")
        bob, _ = await _register_and_login(client, "bob@test.com", "bob")
        file = await _create_file(client, alice_h)

        await client.post(
            f"/api/v1/files/{file['id']}/shares",
            headers=alice_h,
            json={"shared_with_id": bob["id"], "permission": "viewer"},
        )
        response = await client.post(
            f"/api/v1/files/{file['id']}/shares",
            headers=alice_h,
            json={"shared_with_id": bob["id"], "permission": "editor"},
        )
        assert response.status_code == 409

    async def test_share_file_with_self(self, client: httpx.AsyncClient):
        alice, alice_h = await _register_and_login(client, "alice@test.com", "alice")
        file = await _create_file(client, alice_h)

        response = await client.post(
            f"/api/v1/files/{file['id']}/shares",
            headers=alice_h,
            json={"shared_with_id": alice["id"], "permission": "viewer"},
        )
        assert response.status_code == 400

    async def test_share_file_nonexistent_user(self, client: httpx.AsyncClient):
        alice, alice_h = await _register_and_login(client, "alice@test.com", "alice")
        file = await _create_file(client, alice_h)

        response = await client.post(
            f"/api/v1/files/{file['id']}/shares",
            headers=alice_h,
            json={
                "shared_with_id": "00000000-0000-0000-0000-000000000000",
                "permission": "viewer",
            },
        )
        assert response.status_code == 404

    async def test_list_file_shares(self, client: httpx.AsyncClient):
        alice, alice_h = await _register_and_login(client, "alice@test.com", "alice")
        bob, _ = await _register_and_login(client, "bob@test.com", "bob")
        file = await _create_file(client, alice_h)

        await client.post(
            f"/api/v1/files/{file['id']}/shares",
            headers=alice_h,
            json={"shared_with_id": bob["id"], "permission": "viewer"},
        )
        response = await client.get(
            f"/api/v1/files/{file['id']}/shares", headers=alice_h
        )
        assert response.status_code == 200
        assert len(response.json()) == 1

    async def test_list_file_shares_non_owner(self, client: httpx.AsyncClient):
        alice, alice_h = await _register_and_login(client, "alice@test.com", "alice")
        bob, bob_h = await _register_and_login(client, "bob@test.com", "bob")
        file = await _create_file(client, alice_h)

        response = await client.get(
            f"/api/v1/files/{file['id']}/shares", headers=bob_h
        )
        assert response.status_code == 404

    async def test_update_file_share(self, client: httpx.AsyncClient):
        alice, alice_h = await _register_and_login(client, "alice@test.com", "alice")
        bob, _ = await _register_and_login(client, "bob@test.com", "bob")
        file = await _create_file(client, alice_h)

        share_resp = await client.post(
            f"/api/v1/files/{file['id']}/shares",
            headers=alice_h,
            json={"shared_with_id": bob["id"], "permission": "viewer"},
        )
        share_id = share_resp.json()["id"]

        response = await client.patch(
            f"/api/v1/files/{file['id']}/shares/{share_id}",
            headers=alice_h,
            json={"permission": "editor"},
        )
        assert response.status_code == 200
        assert response.json()["permission"] == "editor"

    async def test_delete_file_share(self, client: httpx.AsyncClient):
        alice, alice_h = await _register_and_login(client, "alice@test.com", "alice")
        bob, _ = await _register_and_login(client, "bob@test.com", "bob")
        file = await _create_file(client, alice_h)

        share_resp = await client.post(
            f"/api/v1/files/{file['id']}/shares",
            headers=alice_h,
            json={"shared_with_id": bob["id"], "permission": "viewer"},
        )
        share_id = share_resp.json()["id"]

        response = await client.delete(
            f"/api/v1/files/{file['id']}/shares/{share_id}",
            headers=alice_h,
        )
        assert response.status_code == 204

        # Verify it's gone
        list_resp = await client.get(
            f"/api/v1/files/{file['id']}/shares", headers=alice_h
        )
        assert len(list_resp.json()) == 0

    async def test_delete_file_cleans_up_shares(self, client: httpx.AsyncClient):
        alice, alice_h = await _register_and_login(client, "alice@test.com", "alice")
        bob, _ = await _register_and_login(client, "bob@test.com", "bob")
        file = await _create_file(client, alice_h)

        await client.post(
            f"/api/v1/files/{file['id']}/shares",
            headers=alice_h,
            json={"shared_with_id": bob["id"], "permission": "viewer"},
        )

        # Delete the file
        await client.delete(f"/api/v1/files/{file['id']}", headers=alice_h)

        # Shares should be gone (file no longer exists, so 404)
        response = await client.get(
            f"/api/v1/files/{file['id']}/shares", headers=alice_h
        )
        assert response.status_code == 404


class TestFolderShares:
    async def test_share_folder(self, client: httpx.AsyncClient):
        alice, alice_h = await _register_and_login(client, "alice@test.com", "alice")
        bob, _ = await _register_and_login(client, "bob@test.com", "bob")
        folder = await _create_folder(client, alice_h)

        response = await client.post(
            f"/api/v1/folders/{folder['id']}/shares",
            headers=alice_h,
            json={"shared_with_id": bob["id"], "permission": "editor"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["permission"] == "editor"
        assert data["resource_type"] == "folder"

    async def test_list_folder_shares(self, client: httpx.AsyncClient):
        alice, alice_h = await _register_and_login(client, "alice@test.com", "alice")
        bob, _ = await _register_and_login(client, "bob@test.com", "bob")
        folder = await _create_folder(client, alice_h)

        await client.post(
            f"/api/v1/folders/{folder['id']}/shares",
            headers=alice_h,
            json={"shared_with_id": bob["id"], "permission": "viewer"},
        )
        response = await client.get(
            f"/api/v1/folders/{folder['id']}/shares", headers=alice_h
        )
        assert response.status_code == 200
        assert len(response.json()) == 1

    async def test_update_folder_share(self, client: httpx.AsyncClient):
        alice, alice_h = await _register_and_login(client, "alice@test.com", "alice")
        bob, _ = await _register_and_login(client, "bob@test.com", "bob")
        folder = await _create_folder(client, alice_h)

        share_resp = await client.post(
            f"/api/v1/folders/{folder['id']}/shares",
            headers=alice_h,
            json={"shared_with_id": bob["id"], "permission": "viewer"},
        )
        share_id = share_resp.json()["id"]

        response = await client.patch(
            f"/api/v1/folders/{folder['id']}/shares/{share_id}",
            headers=alice_h,
            json={"permission": "editor"},
        )
        assert response.status_code == 200
        assert response.json()["permission"] == "editor"

    async def test_delete_folder_share(self, client: httpx.AsyncClient):
        alice, alice_h = await _register_and_login(client, "alice@test.com", "alice")
        bob, _ = await _register_and_login(client, "bob@test.com", "bob")
        folder = await _create_folder(client, alice_h)

        share_resp = await client.post(
            f"/api/v1/folders/{folder['id']}/shares",
            headers=alice_h,
            json={"shared_with_id": bob["id"], "permission": "viewer"},
        )
        share_id = share_resp.json()["id"]

        response = await client.delete(
            f"/api/v1/folders/{folder['id']}/shares/{share_id}",
            headers=alice_h,
        )
        assert response.status_code == 204
