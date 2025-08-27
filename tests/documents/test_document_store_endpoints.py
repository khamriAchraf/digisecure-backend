from datetime import datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.test_data import BASE_URL, SUPER_ADMIN


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_document_folder_crud_and_tree_and_contents():
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        # Login as Super-Admin
        login_resp = await ac.post(
            "/auth/login",
            data={
                "username": SUPER_ADMIN["email"],
                "password": SUPER_ADMIN["password"],
            },
        )
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        unique_suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")

        # Create root-level folder
        root_folder_payload = {"name": f"Root-Folder-{unique_suffix}"}
        create_root_resp = await ac.post(
            "/documents/folders", json=root_folder_payload, headers=headers
        )
        assert (
            create_root_resp.status_code == 201
        ), f"Root folder creation failed: {create_root_resp.text}"
        root_folder = create_root_resp.json()
        root_folder_id = root_folder["id"]

        # Create subfolder under root
        child_folder_payload = {
            "name": f"Child-Folder-{unique_suffix}",
            "parent_id": root_folder_id,
        }
        create_child_resp = await ac.post(
            "/documents/folders", json=child_folder_payload, headers=headers
        )
        assert (
            create_child_resp.status_code == 201
        ), f"Child folder creation failed: {create_child_resp.text}"
        child_folder = create_child_resp.json()
        child_folder_id = child_folder["id"]

        # List folders under root
        list_sub_resp = await ac.get(
            "/documents/folders", params={"parent_id": root_folder_id}, headers=headers
        )
        assert list_sub_resp.status_code == 200
        subfolders = list_sub_resp.json()
        assert any(f["id"] == child_folder_id for f in subfolders)

        # Get folder tree and validate structure
        tree_resp = await ac.get("/documents/folders/tree", headers=headers)
        assert tree_resp.status_code == 200
        tree = tree_resp.json()
        assert tree["id"] == 0 and tree["name"] == "root"

        # Ensure root contains our root_folder
        def contains_folder(node, fid):
            if node["id"] == fid:
                return True
            for ch in node.get("children", []):
                if contains_folder(ch, fid):
                    return True
            return False

        assert contains_folder(tree, root_folder_id)

        # Create a document with initial version in the child folder
        file_bytes = b"hello world v1"
        multipart = {
            "name": (None, f"Doc-{unique_suffix}"),
            "description": (None, "Test document"),
            "folder_id": (None, str(child_folder_id)),
            "file": (
                f"doc-{unique_suffix}.txt",
                file_bytes,
                "application/octet-stream",
            ),
        }
        create_doc_resp = await ac.post("/documents/", files=multipart, headers=headers)
        assert (
            create_doc_resp.status_code == 201
        ), f"Document creation failed: {create_doc_resp.text}"
        doc = create_doc_resp.json()
        doc_id = doc["id"]
        assert doc["folder_id"] == child_folder_id
        assert len(doc.get("versions", [])) == 1

        # Verify folder contents returns both subfolders and documents
        contents_resp = await ac.get(
            f"/documents/folders/{root_folder_id}", headers=headers
        )
        assert contents_resp.status_code == 200
        contents = contents_resp.json()
        assert contents["folder"]["id"] == root_folder_id
        assert any(f["id"] == child_folder_id for f in contents["subfolders"])
        # Child folder should contain the created document
        child_contents_resp = await ac.get(
            f"/documents/folders/{child_folder_id}", headers=headers
        )
        assert child_contents_resp.status_code == 200
        child_contents = child_contents_resp.json()
        assert any(d["id"] == doc_id for d in child_contents["documents"])

        # Cleanup: delete document, then folders
        del_doc_resp = await ac.delete(f"/documents/{doc_id}", headers=headers)
        assert del_doc_resp.status_code == 204

        del_child_resp = await ac.delete(
            f"/documents/folders/{child_folder_id}", headers=headers
        )
        assert del_child_resp.status_code == 204
        del_root_resp = await ac.delete(
            f"/documents/folders/{root_folder_id}", headers=headers
        )
        assert del_root_resp.status_code == 204


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_document_version_upload_list_delete_and_download_and_move():
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        # Login
        login_resp = await ac.post(
            "/auth/login",
            data={
                "username": SUPER_ADMIN["email"],
                "password": SUPER_ADMIN["password"],
            },
        )
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        unique_suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")

        # Create a folder
        folder_resp = await ac.post(
            "/documents/folders",
            json={"name": f"Docs-{unique_suffix}"},
            headers=headers,
        )
        assert folder_resp.status_code == 201
        folder_id = folder_resp.json()["id"]

        # Create document with initial version
        file_v1 = b"content v1"
        create_doc_resp = await ac.post(
            "/documents/",
            files={
                "name": (None, f"My-Doc-{unique_suffix}"),
                "folder_id": (None, str(folder_id)),
                "file": (f"mydoc.txt", file_v1, "text/plain"),
            },
            headers=headers,
        )
        assert create_doc_resp.status_code == 201, create_doc_resp.text
        doc = create_doc_resp.json()
        doc_id = doc["id"]
        assert len(doc["versions"]) == 1

        # Upload a new version (v2)
        file_v2 = b"content v2"
        upload_v2_resp = await ac.post(
            f"/documents/{doc_id}/versions",
            files={"file": (f"mydoc.txt", file_v2, "text/plain")},
            headers=headers,
        )
        assert upload_v2_resp.status_code == 201, upload_v2_resp.text
        v2 = upload_v2_resp.json()
        assert v2["version_number"] == 2

        # List versions should include 2 entries
        versions_resp = await ac.get(f"/documents/{doc_id}/versions", headers=headers)
        assert versions_resp.status_code == 200
        versions = versions_resp.json()
        assert len(versions) == 2

        # Download latest version (v2)
        download_resp = await ac.get(
            f"/documents/versions/{v2['id']}/download", headers=headers
        )
        assert download_resp.status_code == 200
        assert download_resp.content == file_v2

        # Move document to a new folder
        new_folder_resp = await ac.post(
            "/documents/folders",
            json={"name": f"Target-{unique_suffix}"},
            headers=headers,
        )
        assert new_folder_resp.status_code == 201
        new_folder_id = new_folder_resp.json()["id"]

        patch_resp = await ac.patch(
            f"/documents/{doc_id}", json={"folder_id": new_folder_id}, headers=headers
        )
        assert patch_resp.status_code == 200, patch_resp.text
        moved_doc = patch_resp.json()
        assert moved_doc["folder_id"] == new_folder_id

        # Delete a version (v1)
        v1_id = next(v["id"] for v in versions if v["version_number"] == 1)
        del_v1_resp = await ac.delete(f"/documents/versions/{v1_id}", headers=headers)
        assert del_v1_resp.status_code == 204

        # Verify only one version remains
        versions_after_del = (
            await ac.get(f"/documents/{doc_id}/versions", headers=headers)
        ).json()
        assert len(versions_after_del) == 1

        # Cleanup
        assert (
            await ac.delete(f"/documents/{doc_id}", headers=headers)
        ).status_code == 204
        assert (
            await ac.delete(f"/documents/folders/{new_folder_id}", headers=headers)
        ).status_code == 204
        assert (
            await ac.delete(f"/documents/folders/{folder_id}", headers=headers)
        ).status_code == 204


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_documents_pagination_and_search_and_filters():
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        # Login
        login_resp = await ac.post(
            "/auth/login",
            data={
                "username": SUPER_ADMIN["email"],
                "password": SUPER_ADMIN["password"],
            },
        )
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        unique_suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")

        # Create folder and multiple documents
        folder_id = (
            await ac.post(
                "/documents/folders",
                json={"name": f"Docs-{unique_suffix}"},
                headers=headers,
            )
        ).json()["id"]

        names = [
            f"Alpha-{unique_suffix}",
            f"Beta-{unique_suffix}",
            f"Gamma-{unique_suffix}",
        ]
        for nm in names:
            await ac.post(
                "/documents/",
                files={
                    "name": (None, nm),
                    "folder_id": (None, str(folder_id)),
                    "file": (f"{nm}.txt", b"x" * 10, "text/plain"),
                },
                headers=headers,
            )

        # Paginate
        page1 = await ac.get(
            "/documents/",
            params={"page": 1, "per_page": 2, "sort_by": "name"},
            headers=headers,
        )
        assert page1.status_code == 200
        data1 = page1.json()
        assert data1["total"] >= 3
        assert len(data1["data"]) == 2

        # Cursor mode
        cursor_page = await ac.get(
            "/documents/",
            params={"cursor": data1["data"][0]["id"], "per_page": 2},
            headers=headers,
        )
        assert cursor_page.status_code == 200

        # Search by name
        search_resp = await ac.get(
            "/documents/", params={"search": "Alpha-"}, headers=headers
        )
        assert search_resp.status_code == 200
        search_items = search_resp.json()["data"]
        assert any("Alpha-" in doc["name"] for doc in search_items)

        # Filter by folder_id
        filter_resp = await ac.get(
            "/documents/", params={"folder_id": folder_id}, headers=headers
        )
        assert filter_resp.status_code == 200
        assert all(doc["folder_id"] == folder_id for doc in filter_resp.json()["data"])

        # Cleanup: delete documents and folder
        listing = await ac.get(
            "/documents/",
            params={"folder_id": folder_id, "per_page": 999},
            headers=headers,
        )
        for doc in listing.json()["data"]:
            await ac.delete(f"/documents/{doc['id']}", headers=headers)
        await ac.delete(f"/documents/folders/{folder_id}", headers=headers)
