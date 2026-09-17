import httpx
from sqlalchemy.ext.asyncio import AsyncSession


class TestCreateFolder:
    async def test_create_root_folder(
        self, client: httpx.AsyncClient, auth_header: dict
    ):
        response = await client.post(
            "/api/v1/folders/",
            headers=auth_header,
            json={"name": "Documents"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Documents"
        assert data["parent_id"] is None
        assert "id" in data

    async def test_create_nested_folder(
        self, client: httpx.AsyncClient, auth_header: dict
    ):
        parent = await client.post(
            "/api/v1/folders/",
            headers=auth_header,
            json={"name": "Documents"},
        )
        parent_id = parent.json()["id"]

        response = await client.post(
            "/api/v1/folders/",
            headers=auth_header,
            json={"name": "Work", "parent_id": parent_id},
        )
        assert response.status_code == 201
        assert response.json()["parent_id"] == parent_id

    async def test_create_duplicate_name_same_parent(
        self, client: httpx.AsyncClient, auth_header: dict
    ):
        await client.post(
            "/api/v1/folders/",
            headers=auth_header,
            json={"name": "Documents"},
        )
        response = await client.post(
            "/api/v1/folders/",
            headers=auth_header,
            json={"name": "Documents"},
        )
        assert response.status_code == 409

    async def test_create_same_name_different_parent(
        self, client: httpx.AsyncClient, auth_header: dict
    ):
        parent = await client.post(
            "/api/v1/folders/",
            headers=auth_header,
            json={"name": "Parent"},
        )
        # Same name at root level and inside Parent — should both work
        await client.post(
            "/api/v1/folders/",
            headers=auth_header,
            json={"name": "Notes"},
        )
        response = await client.post(
            "/api/v1/folders/",
            headers=auth_header,
            json={"name": "Notes", "parent_id": parent.json()["id"]},
        )
        assert response.status_code == 201

    async def test_create_folder_nonexistent_parent(
        self, client: httpx.AsyncClient, auth_header: dict
    ):
        response = await client.post(
            "/api/v1/folders/",
            headers=auth_header,
            json={
                "name": "Orphan",
                "parent_id": "00000000-0000-0000-0000-000000000000",
            },
        )
        assert response.status_code == 404

    async def test_create_folder_unauthenticated(self, client: httpx.AsyncClient):
        response = await client.post(
            "/api/v1/folders/", json={"name": "Documents"}
        )
        assert response.status_code == 401


class TestListFolders:
    async def test_list_root_folders(
        self, client: httpx.AsyncClient, auth_header: dict
    ):
        await client.post(
            "/api/v1/folders/", headers=auth_header, json={"name": "A"}
        )
        await client.post(
            "/api/v1/folders/", headers=auth_header, json={"name": "B"}
        )
        response = await client.get("/api/v1/folders/", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        names = {f["name"] for f in data}
        assert names == {"A", "B"}

    async def test_list_child_folders(
        self, client: httpx.AsyncClient, auth_header: dict
    ):
        parent = await client.post(
            "/api/v1/folders/", headers=auth_header, json={"name": "Parent"}
        )
        parent_id = parent.json()["id"]
        await client.post(
            "/api/v1/folders/",
            headers=auth_header,
            json={"name": "Child", "parent_id": parent_id},
        )
        response = await client.get(
            f"/api/v1/folders/?parent_id={parent_id}", headers=auth_header
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Child"

    async def test_list_empty(
        self, client: httpx.AsyncClient, auth_header: dict
    ):
        response = await client.get("/api/v1/folders/", headers=auth_header)
        assert response.status_code == 200
        assert response.json() == []


class TestGetFolder:
    async def test_get_folder(
        self, client: httpx.AsyncClient, auth_header: dict
    ):
        created = await client.post(
            "/api/v1/folders/", headers=auth_header, json={"name": "Documents"}
        )
        folder_id = created.json()["id"]
        response = await client.get(
            f"/api/v1/folders/{folder_id}", headers=auth_header
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Documents"

    async def test_get_nonexistent_folder(
        self, client: httpx.AsyncClient, auth_header: dict
    ):
        response = await client.get(
            "/api/v1/folders/00000000-0000-0000-0000-000000000000",
            headers=auth_header,
        )
        assert response.status_code == 404


class TestUpdateFolder:
    async def test_rename_folder(
        self, client: httpx.AsyncClient, auth_header: dict
    ):
        created = await client.post(
            "/api/v1/folders/", headers=auth_header, json={"name": "Old Name"}
        )
        folder_id = created.json()["id"]
        response = await client.patch(
            f"/api/v1/folders/{folder_id}",
            headers=auth_header,
            json={"name": "New Name"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "New Name"

    async def test_rename_to_duplicate(
        self, client: httpx.AsyncClient, auth_header: dict
    ):
        await client.post(
            "/api/v1/folders/", headers=auth_header, json={"name": "Taken"}
        )
        created = await client.post(
            "/api/v1/folders/", headers=auth_header, json={"name": "Original"}
        )
        folder_id = created.json()["id"]
        response = await client.patch(
            f"/api/v1/folders/{folder_id}",
            headers=auth_header,
            json={"name": "Taken"},
        )
        assert response.status_code == 409

    async def test_rename_same_name(
        self, client: httpx.AsyncClient, auth_header: dict
    ):
        created = await client.post(
            "/api/v1/folders/", headers=auth_header, json={"name": "Same"}
        )
        folder_id = created.json()["id"]
        response = await client.patch(
            f"/api/v1/folders/{folder_id}",
            headers=auth_header,
            json={"name": "Same"},
        )
        assert response.status_code == 200


class TestDeleteFolder:
    async def test_delete_folder(
        self, client: httpx.AsyncClient, auth_header: dict
    ):
        created = await client.post(
            "/api/v1/folders/", headers=auth_header, json={"name": "Temp"}
        )
        folder_id = created.json()["id"]
        response = await client.delete(
            f"/api/v1/folders/{folder_id}", headers=auth_header
        )
        assert response.status_code == 204

        # Verify it's gone
        get_response = await client.get(
            f"/api/v1/folders/{folder_id}", headers=auth_header
        )
        assert get_response.status_code == 404

    async def test_delete_folder_cascades_children(
        self, client: httpx.AsyncClient, auth_header: dict, db: AsyncSession
    ):
        parent = await client.post(
            "/api/v1/folders/", headers=auth_header, json={"name": "Parent"}
        )
        parent_id = parent.json()["id"]
        child = await client.post(
            "/api/v1/folders/",
            headers=auth_header,
            json={"name": "Child", "parent_id": parent_id},
        )
        child_id = child.json()["id"]

        # Delete parent
        await client.delete(f"/api/v1/folders/{parent_id}", headers=auth_header)

        # Clear the session's identity map so it doesn't serve stale cached objects.
        # In production, each request has its own session, so this isn't needed.
        db.expunge_all()

        # Child should be gone too
        response = await client.get(
            f"/api/v1/folders/{child_id}", headers=auth_header
        )
        assert response.status_code == 404

    async def test_delete_nonexistent_folder(
        self, client: httpx.AsyncClient, auth_header: dict
    ):
        response = await client.delete(
            "/api/v1/folders/00000000-0000-0000-0000-000000000000",
            headers=auth_header,
        )
        assert response.status_code == 404


class TestFolderPath:
    async def _create_folder(self, client, auth_header, name, parent_id=None):
        body = {"name": name}
        if parent_id:
            body["parent_id"] = parent_id
        resp = await client.post(
            "/api/v1/folders/", headers=auth_header, json=body
        )
        return resp.json()

    async def test_root_folder_path(
        self, client: httpx.AsyncClient, auth_header: dict
    ):
        folder = await self._create_folder(client, auth_header, "Documents")
        response = await client.get(
            f"/api/v1/folders/{folder['id']}/path", headers=auth_header
        )
        assert response.status_code == 200
        path = response.json()
        assert len(path) == 1
        assert path[0]["name"] == "Documents"

    async def test_nested_path(
        self, client: httpx.AsyncClient, auth_header: dict
    ):
        root = await self._create_folder(client, auth_header, "Documents")
        mid = await self._create_folder(
            client, auth_header, "Work", root["id"]
        )
        leaf = await self._create_folder(
            client, auth_header, "Reports", mid["id"]
        )
        response = await client.get(
            f"/api/v1/folders/{leaf['id']}/path", headers=auth_header
        )
        assert response.status_code == 200
        path = response.json()
        assert len(path) == 3
        assert [p["name"] for p in path] == ["Documents", "Work", "Reports"]


class TestMoveFolder:
    async def _create_folder(self, client, auth_header, name, parent_id=None):
        body = {"name": name}
        if parent_id:
            body["parent_id"] = parent_id
        resp = await client.post(
            "/api/v1/folders/", headers=auth_header, json=body
        )
        return resp.json()

    async def test_move_to_another_folder(
        self, client: httpx.AsyncClient, auth_header: dict
    ):
        folder_a = await self._create_folder(client, auth_header, "A")
        folder_b = await self._create_folder(client, auth_header, "B")
        response = await client.post(
            f"/api/v1/folders/{folder_a['id']}/move",
            headers=auth_header,
            json={"parent_id": folder_b["id"]},
        )
        assert response.status_code == 200
        assert response.json()["parent_id"] == folder_b["id"]

    async def test_move_to_root(
        self, client: httpx.AsyncClient, auth_header: dict
    ):
        parent = await self._create_folder(client, auth_header, "Parent")
        child = await self._create_folder(
            client, auth_header, "Child", parent["id"]
        )
        response = await client.post(
            f"/api/v1/folders/{child['id']}/move",
            headers=auth_header,
            json={"parent_id": None},
        )
        assert response.status_code == 200
        assert response.json()["parent_id"] is None

    async def test_move_into_itself(
        self, client: httpx.AsyncClient, auth_header: dict
    ):
        folder = await self._create_folder(client, auth_header, "Folder")
        response = await client.post(
            f"/api/v1/folders/{folder['id']}/move",
            headers=auth_header,
            json={"parent_id": folder["id"]},
        )
        assert response.status_code == 400

    async def test_move_into_own_descendant(
        self, client: httpx.AsyncClient, auth_header: dict
    ):
        grandparent = await self._create_folder(client, auth_header, "GP")
        parent = await self._create_folder(
            client, auth_header, "P", grandparent["id"]
        )
        child = await self._create_folder(
            client, auth_header, "C", parent["id"]
        )
        # Move grandparent into child (circular)
        response = await client.post(
            f"/api/v1/folders/{grandparent['id']}/move",
            headers=auth_header,
            json={"parent_id": child["id"]},
        )
        assert response.status_code == 400

    async def test_move_name_conflict(
        self, client: httpx.AsyncClient, auth_header: dict
    ):
        target = await self._create_folder(client, auth_header, "Target")
        # Create a folder named "Same" inside Target
        await self._create_folder(client, auth_header, "Same", target["id"])
        # Create a root folder also named "Same"
        root_same = await self._create_folder(client, auth_header, "Same")
        # Move root "Same" into Target (conflicts with existing "Same")
        response = await client.post(
            f"/api/v1/folders/{root_same['id']}/move",
            headers=auth_header,
            json={"parent_id": target["id"]},
        )
        assert response.status_code == 409

    async def test_move_same_location_noop(
        self, client: httpx.AsyncClient, auth_header: dict
    ):
        parent = await self._create_folder(client, auth_header, "Parent")
        child = await self._create_folder(
            client, auth_header, "Child", parent["id"]
        )
        # Move to same parent — should succeed (no-op)
        response = await client.post(
            f"/api/v1/folders/{child['id']}/move",
            headers=auth_header,
            json={"parent_id": parent["id"]},
        )
        assert response.status_code == 200
        assert response.json()["parent_id"] == parent["id"]
