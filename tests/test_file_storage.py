from unittest.mock import patch

import httpx


async def _create_file(client, auth_header, name="test.pdf"):
    resp = await client.post(
        "/api/v1/files/",
        headers=auth_header,
        json={"name": name, "mime_type": "application/pdf", "size": 0},
    )
    return resp.json()


class TestUploadUrl:
    @patch("cloudbox_api.services.file.generate_upload_url")
    async def test_get_upload_url(
        self, mock_upload_url, client: httpx.AsyncClient, auth_header: dict
    ):
        mock_upload_url.return_value = "http://minio:9000/cloudbox/key?signature=abc"
        file = await _create_file(client, auth_header)

        response = await client.post(
            f"/api/v1/files/{file['id']}/upload-url", headers=auth_header
        )
        assert response.status_code == 200
        data = response.json()
        assert "upload_url" in data
        assert data["expires_in"] == 900
        mock_upload_url.assert_called_once()

    @patch("cloudbox_api.services.file.generate_upload_url")
    async def test_upload_url_sets_storage_key(
        self, mock_upload_url, client: httpx.AsyncClient, auth_header: dict
    ):
        mock_upload_url.return_value = "http://minio:9000/cloudbox/key?sig=abc"
        file = await _create_file(client, auth_header)
        assert file["storage_key"] is None

        await client.post(
            f"/api/v1/files/{file['id']}/upload-url", headers=auth_header
        )

        # File now has a storage_key
        get_resp = await client.get(
            f"/api/v1/files/{file['id']}", headers=auth_header
        )
        assert get_resp.json()["storage_key"] is not None
        assert "users/" in get_resp.json()["storage_key"]

    async def test_upload_url_nonexistent_file(
        self, client: httpx.AsyncClient, auth_header: dict
    ):
        response = await client.post(
            "/api/v1/files/00000000-0000-0000-0000-000000000000/upload-url",
            headers=auth_header,
        )
        assert response.status_code == 404

    async def test_upload_url_unauthenticated(self, client: httpx.AsyncClient):
        response = await client.post(
            "/api/v1/files/00000000-0000-0000-0000-000000000000/upload-url"
        )
        assert response.status_code == 401


class TestConfirmUpload:
    @patch("cloudbox_api.services.file.get_object_size")
    @patch("cloudbox_api.services.file.object_exists")
    @patch("cloudbox_api.services.file.generate_upload_url")
    async def test_confirm_upload_success(
        self,
        mock_upload_url,
        mock_exists,
        mock_size,
        client: httpx.AsyncClient,
        auth_header: dict,
    ):
        mock_upload_url.return_value = "http://minio:9000/bucket/key?sig=abc"
        mock_exists.return_value = True
        mock_size.return_value = 204800

        file = await _create_file(client, auth_header)

        # Get upload URL (sets storage_key)
        await client.post(
            f"/api/v1/files/{file['id']}/upload-url", headers=auth_header
        )

        # Confirm upload
        response = await client.post(
            f"/api/v1/files/{file['id']}/confirm-upload", headers=auth_header
        )
        assert response.status_code == 200
        assert response.json()["size"] == 204800

    async def test_confirm_upload_no_storage_key(
        self, client: httpx.AsyncClient, auth_header: dict
    ):
        file = await _create_file(client, auth_header)
        response = await client.post(
            f"/api/v1/files/{file['id']}/confirm-upload", headers=auth_header
        )
        assert response.status_code == 400
        assert "No upload URL" in response.json()["detail"]

    @patch("cloudbox_api.services.file.object_exists")
    @patch("cloudbox_api.services.file.generate_upload_url")
    async def test_confirm_upload_not_uploaded(
        self,
        mock_upload_url,
        mock_exists,
        client: httpx.AsyncClient,
        auth_header: dict,
    ):
        mock_upload_url.return_value = "http://minio:9000/bucket/key?sig=abc"
        mock_exists.return_value = False

        file = await _create_file(client, auth_header)
        await client.post(
            f"/api/v1/files/{file['id']}/upload-url", headers=auth_header
        )

        response = await client.post(
            f"/api/v1/files/{file['id']}/confirm-upload", headers=auth_header
        )
        assert response.status_code == 400
        assert "not been uploaded" in response.json()["detail"]


class TestDownloadUrl:
    @patch("cloudbox_api.services.file.generate_download_url")
    @patch("cloudbox_api.services.file.object_exists")
    @patch("cloudbox_api.services.file.generate_upload_url")
    async def test_download_url_success(
        self,
        mock_upload_url,
        mock_exists,
        mock_download_url,
        client: httpx.AsyncClient,
        auth_header: dict,
    ):
        mock_upload_url.return_value = "http://minio:9000/bucket/key?sig=abc"
        mock_exists.return_value = True
        mock_download_url.return_value = (
            "http://minio:9000/cloudbox/key?download-sig=xyz"
        )

        file = await _create_file(client, auth_header)

        # Get upload URL to set storage_key
        await client.post(
            f"/api/v1/files/{file['id']}/upload-url", headers=auth_header
        )

        response = await client.get(
            f"/api/v1/files/{file['id']}/download-url", headers=auth_header
        )
        assert response.status_code == 200
        data = response.json()
        assert "download_url" in data
        assert data["expires_in"] == 3600

    async def test_download_url_not_uploaded(
        self, client: httpx.AsyncClient, auth_header: dict
    ):
        file = await _create_file(client, auth_header)
        response = await client.get(
            f"/api/v1/files/{file['id']}/download-url", headers=auth_header
        )
        assert response.status_code == 404
        assert "not been uploaded" in response.json()["detail"]


class TestDeleteFileWithStorage:
    @patch("cloudbox_api.services.file.delete_object")
    @patch("cloudbox_api.services.file.generate_upload_url")
    async def test_delete_file_removes_object(
        self,
        mock_upload_url,
        mock_delete,
        client: httpx.AsyncClient,
        auth_header: dict,
    ):
        mock_upload_url.return_value = "http://minio:9000/bucket/key?sig=abc"

        file = await _create_file(client, auth_header)

        # Get upload URL to set storage_key
        await client.post(
            f"/api/v1/files/{file['id']}/upload-url", headers=auth_header
        )

        # Delete the file
        await client.delete(
            f"/api/v1/files/{file['id']}", headers=auth_header
        )

        mock_delete.assert_called_once()
