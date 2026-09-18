from unittest.mock import AsyncMock, patch

import httpx


class TestActivities:
    async def test_list_activities_empty(
        self, client: httpx.AsyncClient, auth_header: dict
    ):
        response = await client.get("/api/v1/activities/", headers=auth_header)
        assert response.status_code == 200
        assert response.json() == []

    @patch("cloudbox_api.services.activity.publish_event")
    async def test_file_create_publishes_event(
        self, mock_publish, client: httpx.AsyncClient, auth_header: dict
    ):
        response = await client.post(
            "/api/v1/files/",
            headers=auth_header,
            json={"name": "test.pdf", "mime_type": "application/pdf", "size": 0},
        )
        assert response.status_code == 201
        mock_publish.assert_called_once()

        call_args = mock_publish.call_args
        routing_key = call_args[0][0]
        event = call_args[0][1]
        assert routing_key == "activity.file.created"
        assert event["action"] == "file.created"
        assert event["resource_name"] == "test.pdf"

    @patch("cloudbox_api.services.activity.publish_event")
    async def test_folder_create_publishes_event(
        self, mock_publish, client: httpx.AsyncClient, auth_header: dict
    ):
        response = await client.post(
            "/api/v1/folders/",
            headers=auth_header,
            json={"name": "Documents"},
        )
        assert response.status_code == 201
        mock_publish.assert_called_once()

        event = mock_publish.call_args[0][1]
        assert event["action"] == "folder.created"
        assert event["resource_name"] == "Documents"

    @patch("cloudbox_api.services.activity.publish_event")
    async def test_file_rename_publishes_event(
        self, mock_publish, client: httpx.AsyncClient, auth_header: dict
    ):
        # Create file (first publish call)
        file_resp = await client.post(
            "/api/v1/files/",
            headers=auth_header,
            json={"name": "old.txt", "mime_type": "text/plain", "size": 0},
        )
        file_id = file_resp.json()["id"]
        mock_publish.reset_mock()

        # Rename
        await client.patch(
            f"/api/v1/files/{file_id}",
            headers=auth_header,
            json={"name": "new.txt"},
        )
        mock_publish.assert_called_once()
        event = mock_publish.call_args[0][1]
        assert event["action"] == "file.renamed"

    @patch("cloudbox_api.services.activity.publish_event")
    async def test_file_delete_publishes_event(
        self, mock_publish, client: httpx.AsyncClient, auth_header: dict
    ):
        file_resp = await client.post(
            "/api/v1/files/",
            headers=auth_header,
            json={"name": "temp.txt", "mime_type": "text/plain", "size": 0},
        )
        file_id = file_resp.json()["id"]
        mock_publish.reset_mock()

        await client.delete(f"/api/v1/files/{file_id}", headers=auth_header)
        mock_publish.assert_called_once()
        event = mock_publish.call_args[0][1]
        assert event["action"] == "file.deleted"

    @patch("cloudbox_api.services.activity.publish_event")
    async def test_no_event_on_same_name_rename(
        self, mock_publish, client: httpx.AsyncClient, auth_header: dict
    ):
        file_resp = await client.post(
            "/api/v1/files/",
            headers=auth_header,
            json={"name": "same.txt", "mime_type": "text/plain", "size": 0},
        )
        file_id = file_resp.json()["id"]
        mock_publish.reset_mock()

        await client.patch(
            f"/api/v1/files/{file_id}",
            headers=auth_header,
            json={"name": "same.txt"},
        )
        mock_publish.assert_not_called()
