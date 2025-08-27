## Compliance Controls API

This document describes the endpoints for listing compliance controls for a scope and managing document links for a specific control.

All routes are prefixed with `/compliance`.

### Authentication and permissions

- Requires an authenticated user (standard auth headers for your API).
- Permissions:
  - Read endpoints: permission `read` on resource `compliance_scope`.
  - Mutating endpoints: permission `update` on resource `compliance_scope`.

---

### GET /scopes/{scope_id}/controls

List all controls for the given scope. Includes the documents linked to each control.

- Path params:
  - `scope_id` (integer): ID of the `ComplianceScope`.

- Response: `200 OK`
  - Body: `ComplianceControl[]`
    - Fields:
      - `id` (int)
      - `scope_id` (int)
      - `code` (string)
      - `title` (string)
      - `description` (string | null)
      - `required_document_name` (string | null)
      - `required_document_description` (string | null)
      - `required_document_type` (string | null)
      - `last_audit_date` (ISO datetime | null)
      - `last_audit_result` (string | null)
      - `documents` (Document[]): linked documents (read‑only list)

- Example

```bash
curl -X GET \
  -H "Authorization: Bearer <TOKEN>" \
  http://localhost:8000/compliance/scopes/1/controls
```

- Sample response (truncated)

```json
[
  {
    "id": 10,
    "scope_id": 1,
    "code": "1",
    "title": "Install and Maintain Network Security Controls",
    "description": "...",
    "required_document_name": null,
    "required_document_description": null,
    "required_document_type": null,
    "last_audit_date": null,
    "last_audit_result": null,
    "documents": [
      { "id": 5, "name": "Policy Firewall", "description": "..." }
    ]
  }
]
```

---

### POST /scopes/{scope_id}/controls/{control_id}/documents

Create one or many links between a control and documents (association object with metadata). Ignores duplicates.

- Path params:
  - `scope_id` (integer): ID of the `ComplianceScope` that owns the control.
  - `control_id` (integer): ID of the `ComplianceControl`.

- Request body: `ControlDocumentLinkCreate`
  - `document_ids` (int[]): one or many document IDs to link
  - `last_review_date` (ISO date | null)
  - `next_review_date` (ISO date | null)
  - `expiration_date` (ISO date | null)
  - `status` (string | null) e.g., `Compliant`, `Non-Compliant`, `Pending`
  - `compliance_notes` (string | null)

- Response: `201 Created`
  - Body: `ControlDocumentLink[]` (created links)
    - `id`, `control_id`, `document_id`, `linked_at`, `last_review_date`, `next_review_date`, `expiration_date`, `status`, `compliance_notes`

- Example

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{
        "document_ids": [5, 7, 9],
        "last_review_date": "2025-06-01",
        "next_review_date": "2026-06-01",
        "status": "Pending",
        "compliance_notes": "Awaiting risk committee sign-off"
      }' \
  http://localhost:8000/compliance/scopes/1/controls/10/documents
```

Sample response (truncated):

```json
[
  {
    "id": 42,
    "control_id": 10,
    "document_id": 5,
    "linked_at": "2025-08-14T10:25:00.000Z",
    "last_review_date": "2025-06-01",
    "next_review_date": "2026-06-01",
    "expiration_date": null,
    "status": "Pending",
    "compliance_notes": "Awaiting risk committee sign-off"
  }
]
```

---

### DELETE /scopes/{scope_id}/controls/{control_id}/documents

Remove links between a control and one or many documents.

- Path params:
  - `scope_id` (integer): ID of the `ComplianceScope` that owns the control.
  - `control_id` (integer): ID of the `ComplianceControl`.

- Request body: `ControlDocumentLinkDelete`
  - `document_ids` (int[]): one or many document IDs to unlink

- Response: `204 No Content`

- Example

```bash
curl -X DELETE \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{ "document_ids": [5, 7] }' \
  http://localhost:8000/compliance/scopes/1/controls/10/documents
```

---

### Notes

- The list endpoint for controls uses eager loading to include `documents` without N+1 queries.
- The `ControlDocumentLink` association provides metadata (timestamps, review/expiry dates, status, notes). Use the POST endpoint to populate these when linking.
- Deleting links does not delete the underlying `Document` or `ComplianceControl` records.


