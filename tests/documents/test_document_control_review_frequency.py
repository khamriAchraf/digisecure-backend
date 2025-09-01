from datetime import datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.test_data import BASE_URL, SUPER_ADMIN


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_document_review_frequency_updates_with_control_links():
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        # ---------- Login as Super-Admin ----------
        login_resp = await ac.post(
            "/auth/login",
            data={
                "username": SUPER_ADMIN["email"],
                "password": SUPER_ADMIN["password"],
            },
        )
        assert (
            login_resp.status_code == 200
        ), f"Super-Admin login failed: {login_resp.text}"
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # ---------- Upload a document (use docs/ROLES.md) ----------
        unique_suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
        file_bytes = b""
        try:
            with open("docs/ROLES.md", "rb") as f:
                file_bytes = f.read()
        except FileNotFoundError:
            file_bytes = b"Roles are a groupment of permissions"  # fallback content

        multipart = {
            "name": (None, f"ROLES-{unique_suffix}.md"),
            "description": (None, "Test roles document for control linking"),
            "file": (f"roles-{unique_suffix}.md", file_bytes, "text/markdown"),
        }
        create_doc_resp = await ac.post("/documents/", files=multipart, headers=headers)
        assert (
            create_doc_resp.status_code == 201
        ), f"Document creation failed: {create_doc_resp.text}"
        doc = create_doc_resp.json()
        document_id = doc["id"]

        try:
            # ---------- Find PCI-DSS scope ----------
            scopes_resp = await ac.get("/compliance/scopes", headers=headers)
            assert (
                scopes_resp.status_code == 200
            ), f"Failed to list scopes: {scopes_resp.text}"
            scopes = scopes_resp.json()
            pci_scope = next((s for s in scopes if s.get("name") == "PCI-DSS"), None)
            assert (
                pci_scope is not None
            ), "PCI-DSS scope not found (ensure seed created it)"
            scope_id = pci_scope["id"]

            # ---------- Find controls DOC-001 (12m) and DOC-042 (6m) ----------
            controls_resp = await ac.get(
                f"/compliance/scopes/{scope_id}/controls", headers=headers
            )
            assert (
                controls_resp.status_code == 200
            ), f"Failed to list controls: {controls_resp.text}"
            controls = controls_resp.json()

            def find_control(code: str):
                return next((c for c in controls if c.get("code") == code), None)

            ctrl_doc_001 = find_control("DOC-001")
            ctrl_doc_042 = find_control("DOC-042")
            assert ctrl_doc_001 is not None, "DOC-001 control not found"
            assert ctrl_doc_042 is not None, "DOC-042 control not found"
            ctrl_001_id = ctrl_doc_001["id"]
            ctrl_042_id = ctrl_doc_042["id"]

            # ---------- Link document to DOC-001 (expect 12 months) ----------
            link_payload = {"document_ids": [document_id]}
            link_001_resp = await ac.post(
                f"/compliance/scopes/{scope_id}/controls/{ctrl_001_id}/documents",
                json=link_payload,
                headers=headers,
            )
            assert (
                link_001_resp.status_code == 201
            ), f"Linking DOC-001 failed: {link_001_resp.text}"

            get_doc_resp = await ac.get(f"/documents/{document_id}", headers=headers)
            assert (
                get_doc_resp.status_code == 200
            ), f"Get document failed: {get_doc_resp.text}"
            current_doc = get_doc_resp.json()
            assert (
                current_doc.get("review_frequency_months") == 12
            ), f"Expected 12 months after linking DOC-001, got {current_doc.get('review_frequency_months')}"

            # ---------- Link document to DOC-042 (expect min -> 6 months) ----------
            link_042_resp = await ac.post(
                f"/compliance/scopes/{scope_id}/controls/{ctrl_042_id}/documents",
                json=link_payload,
                headers=headers,
            )
            assert (
                link_042_resp.status_code == 201
            ), f"Linking DOC-042 failed: {link_042_resp.text}"

            get_doc_resp = await ac.get(f"/documents/{document_id}", headers=headers)
            assert get_doc_resp.status_code == 200
            current_doc = get_doc_resp.json()
            print(current_doc)
            assert (
                current_doc.get("review_frequency_months") == 6
            ), f"Expected 6 months after linking DOC-042, got {current_doc.get('review_frequency_months')}"

            # ---------- Unlink document from DOC-042 (expect back to 12 months) ----------
            unlink_payload = {"document_ids": [document_id]}
            unlink_resp = await ac.request(
                "DELETE",
                f"/compliance/scopes/{scope_id}/controls/{ctrl_042_id}/documents",
                json=unlink_payload,
                headers=headers,
            )
            assert (
                unlink_resp.status_code == 204
            ), f"Unlinking DOC-042 failed: {unlink_resp.text}"

            get_doc_resp = await ac.get(f"/documents/{document_id}", headers=headers)
            assert get_doc_resp.status_code == 200
            current_doc = get_doc_resp.json()
            assert (
                current_doc.get("review_frequency_months") == 12
            ), f"Expected 12 months after unlinking DOC-042, got {current_doc.get('review_frequency_months')}"

        finally:
            # Cleanup the created document
            await ac.delete(f"/documents/{document_id}", headers=headers)
