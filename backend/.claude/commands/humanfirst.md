# /humanfirst — HumanFirst MCP Workflow

Use this command to work with HumanFirst drafts via the MCP server tool surface.
All requests authenticate with a bearer token: `Authorization: Bearer hf_...`

## Prerequisites

Your MCP client must send `Authorization: Bearer hf_<your-token>` on every request.
The server validates the token against `users.mcp_token` and scopes all reads and
writes to the authenticated author — cross-user access is rejected.

## Available MCP Tools

| Tool | Purpose |
|---|---|
| `ping` | Health-check — returns `{"ok": true}` |
| `list_drafts` | List the authenticated author's drafts, newest first |
| `get_draft` | Fetch a single draft with its sections by draft ID |
| `save_section` | Add an AI-authored section to a locked draft |
| `delete_section` | Remove an AI-authored section from a locked draft |

## Workflow

### 1. List drafts

Call `list_drafts` to retrieve the author's drafts ordered by `updated_at` descending.
Each item includes `id`, `title`, `status`, `section_count`, and `ai_section_count`.

### 2. Choose a locked draft

**Selection rule:** only drafts with `status == "locked"` accept AI sections.
Drafts in any other status will be rejected by `save_section` with `draft_not_ready_for_ai`.
Pick the locked draft you intend to annotate.

### 3. Inspect the draft

Call `get_draft` with the chosen `draft_id` to retrieve the full body and the list of
existing sections (both human-materialized and AI-authored).

### 4. Add or remove sections

- **`save_section`** — create an AI section anchored after a specific paragraph.
  Supply `draft_id`, `type` (e.g. `example`, `rephrase`), `content`, and
  `position_after_paragraph` (must match a human section's position).
  Optional: `source_selection` and `author_prompt` for provenance.

- **`delete_section`** — remove a previously created AI section by `section_id`.
  Only AI-authored sections owned by the authenticated author can be deleted.

### 5. Verify

Call `get_draft` again to confirm the section list reflects your changes.

## Error Codes

| Code | Meaning |
|---|---|
| `auth_required` | No `Authorization` header present |
| `invalid_token` | Token does not match any user |
| `draft_not_found` | Draft ID unknown or belongs to another author |
| `draft_not_ready_for_ai` | Draft is not locked |
| `invalid_section_position` | `position_after_paragraph` has no matching human section |
| `section_not_found` | Section ID unknown or belongs to another author |
| `section_not_deletable` | Target section is human-authored and cannot be deleted |
