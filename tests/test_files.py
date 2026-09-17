import httpx
from sqlalchemy.ext.asyncio import AsyncSession


async def _create_folder(client, auth_header, name):
    resp = await client.post(
        "/api/v1/folders/", headers=auth_header, json={"name": name}
    )
    return resp.json()


async def _create_file(client, auth_header, name="report.pdf", folder_id=None):
    body = {"name": name, "mime_type": "application/pdf", "size": 1024}
    if folder_id:
        body["folder_id"] = folder_id
    resp = await client.post(
        "/api/v1/files/", headers=auth_header, json=body
    )
    return resp.json()


class TestCreateFile:
    async def test_create_file_at_root(
        self, client: httpx.AsyncClient, auth_header: dict
    ):
        response = await client.post(
            "/api/v1/files/",
            headers=auth_header,
            json={"name": "notes.txt", "mime_type": "text/plain", "size": 256},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "notes.txt"
        assert data["mime_type"] == "text/plain"
        assert data["size"] == 256
        assert data["folder_id"] is None
        assert data["storage_key"] is None
        assert "id" in data

    async def test_create_file_in_folder(
        self, client: httpx.AsyncClient, auth_header: dict
    ):
        folder = await _create_folder(client, auth_header, "Documents")
        response = await client.post(
            "/api/v1/files/",
            headers=auth_header,
            json={
                "name": "report.pdf",
                "mime_type": "application/pdf",
                "size": 2048,
                "folder_id": folder["id"],
            },
        )
        assert response.status_code == 201
        assert response.json()["folder_id"] == folder["id"]

    async def test_create_file_nonexistent_folder(
        self, client: httpx.AsyncClient, auth_header: dict
    ):
        response = await client.post(
            "/api/v1/files/",
            headers=auth_header,
            json={
                "name": "file.txt",
                "mime_type": "text/plain",
                "size": 100,
                "folder_id": "00000000-0000-0000-0000-000000000000",
            },
        )
        assert response.status_code == 404

    async def test_create_file_duplicate_name_allowed(
        self, client: httpx.AsyncClient, auth_header: dict
    ):
        await _create_file(client, auth_header, "same.txt")
        response = await client.post(
            "/api/v1/files/",
            headers=auth_header,
            json={"name": "same.txt", "mime_type": "text/plain", "size": 0},
        )
        assert response.status_code == 201

    async def test_create_file_unauthenticated(self, client: httpx.AsyncClient):
        response = await client.post(
            "/api/v1/files/",
            json={"name": "file.txt", "mime_type": "text/plain", "size": 0},
        )
        assert response.status_code == 401

    async def test_create_file_invalid_data(
        self, client: httpx.AsyncClient, auth_header: dict
    ):
        response = await client.post(
            "/api/v1/files/",
            headers=auth_header,
            json={"name": "", "mime_type": "text/plain", "size": -1},
        )
        assert response.status_code == 422


class TestListFiles:
    async def test_list_root_files(
        self, client: httpx.AsyncClient, auth_header: dict
    ):
        await _create_file(client, auth_header, "a.txt")
        await _create_file(client, auth_header, "b.txt")
        response = await client.get("/api/v1/files/", headers=auth_header)
        assert response.status_code == 200
        assert len(response.json()) == 2

    async def test_list_files_in_folder(
        self, client: httpx.AsyncClient, auth_header: dict
    ):
        folder = await _create_folder(client, auth_header, "Docs")
        await _create_file(client, auth_header, "in_folder.txt", folder["id"])
        await _create_file(client, auth_header, "at_root.txt")

        response = await client.get(
            f"/api/v1/files/?folder_id={folder['id']}", headers=auth_header
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "in_folder.txt"

    async def test_list_empty(
        self, client: httpx.AsyncClient, auth_header: dict
    ):
        response = await client.get("/api/v1/files/", headers=auth_header)
        assert response.status_code == 200
        assert response.json() == []


class TestGetFile:
    async def test_get_file(
        self, client: httpx.AsyncClient, auth_header: dict
    ):
        file = await _create_file(client, auth_header)
        response = await client.get(
            f"/api/v1/files/{file['id']}", headers=auth_header
        )
        assert response.status_code == 200
        assert response.json()["name"] == "report.pdf"

    async def test_get_nonexistent_file(
        self, client: httpx.AsyncClient, auth_header: dict
    ):
        response = await client.get(
            "/api/v1/files/00000000-0000-0000-0000-000000000000",
            headers=auth_header,
        )
        assert response.status_code == 404


class TestUpdateFile:
    async def test_rename_file(
        self, client: httpx.AsyncClient, auth_header: dict
    ):
        file = await _create_file(client, auth_header, "old.txt")
        response = await client.patch(
            f"/api/v1/files/{file['id']}",
            headers=auth_header,
            json={"name": "new.txt"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "new.txt"

    async def test_rename_same_name(
        self, client: httpx.AsyncClient, auth_header: dict
    ):
        file = await _create_file(client, auth_header, "same.txt")
        response = await client.patch(
            f"/api/v1/files/{file['id']}",
            headers=auth_header,
            json={"name": "same.txt"},
        )
        assert response.status_code == 200


class TestDeleteFile:
    async def test_delete_file(
        self, client: httpx.AsyncClient, auth_header: dict
    ):
        file = await _create_file(client, auth_header)
        response = await client.delete(
            f"/api/v1/files/{file['id']}", headers=auth_header
        )
        assert response.status_code == 204

        get_resp = await client.get(
            f"/api/v1/files/{file['id']}", headers=auth_header
        )
        assert get_resp.status_code == 404

    async def test_delete_nonexistent_file(
        self, client: httpx.AsyncClient, auth_header: dict
    ):
        response = await client.delete(
            "/api/v1/files/00000000-0000-0000-0000-000000000000",
            headers=auth_header,
        )
        assert response.status_code == 404

    async def test_folder_delete_cascades_files(
        self, client: httpx.AsyncClient, auth_header: dict, db: AsyncSession
    ):
        folder = await _create_folder(client, auth_header, "Temp")
        file = await _create_file(client, auth_header, "inside.txt", folder["id"])

        await client.delete(f"/api/v1/folders/{folder['id']}", headers=auth_header)
        db.expunge_all()

        response = await client.get(
            f"/api/v1/files/{file['id']}", headers=auth_header
        )
        assert response.status_code == 404


class TestMoveFile:
    async def test_move_file_to_folder(
        self, client: httpx.AsyncClient, auth_header: dict
    ):
        file = await _create_file(client, auth_header, "doc.txt")
        folder = await _create_folder(client, auth_header, "Target")
        response = await client.post(
            f"/api/v1/files/{file['id']}/move",
            headers=auth_header,
            json={"folder_id": folder["id"]},
        )
        assert response.status_code == 200
        assert response.json()["folder_id"] == folder["id"]

    async def test_move_file_to_root(
        self, client: httpx.AsyncClient, auth_header: dict
    ):
        folder = await _create_folder(client, auth_header, "Source")
        file = await _create_file(client, auth_header, "doc.txt", folder["id"])
        response = await client.post(
            f"/api/v1/files/{file['id']}/move",
            headers=auth_header,
            json={"folder_id": None},
        )
        assert response.status_code == 200
        assert response.json()["folder_id"] is None

    async def test_move_file_between_folders(
        self, client: httpx.AsyncClient, auth_header: dict
    ):
        folder_a = await _create_folder(client, auth_header, "A")
        folder_b = await _create_folder(client, auth_header, "B")
        file = await _create_file(client, auth_header, "doc.txt", folder_a["id"])
        response = await client.post(
            f"/api/v1/files/{file['id']}/move",
            headers=auth_header,
            json={"folder_id": folder_b["id"]},
        )
        assert response.status_code == 200
        assert response.json()["folder_id"] == folder_b["id"]

    async def test_move_file_nonexistent_folder(
        self, client: httpx.AsyncClient, auth_header: dict
    ):
        file = await _create_file(client, auth_header, "doc.txt")
        response = await client.post(
            f"/api/v1/files/{file['id']}/move",
            headers=auth_header,
            json={"folder_id": "00000000-0000-0000-0000-000000000000"},
        )
        assert response.status_code == 404

    async def test_move_file_same_location_noop(
        self, client: httpx.AsyncClient, auth_header: dict
    ):
        folder = await _create_folder(client, auth_header, "Same")
        file = await _create_file(client, auth_header, "doc.txt", folder["id"])
        response = await client.post(
            f"/api/v1/files/{file['id']}/move",
            headers=auth_header,
            json={"folder_id": folder["id"]},
        )
        assert response.status_code == 200
        assert response.json()["folder_id"] == folder["id"]
