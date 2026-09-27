# Project Registration (Phase 3)

Authenticated, ownership-aware registration for LaunchPad projects.

## Scope

This is registration only: name, description, website, an on/off lifecycle
flag. It deliberately does **not** include token symbol/supply/decimals,
presale configuration, vesting configuration, or liquidity configuration —
those require decisions Phase 3 has no mandate to make and belong to Phase 4
(Ecosystem Token Creation) and later.

## Ownership model

- `Project.owner_id` is set exactly once, at creation, from the
  authenticated user resolved by the existing Phase 2 JWT dependency
  (`get_current_user`) — never from request-body content. A test
  (`test_client_supplied_owner_field_is_ignored`) proves a forged
  `owner_id`/`user_id` field in the request body has no effect.
- Every route that touches a specific project depends on
  `app/features/projects/dependencies.py::get_owned_project`, which is the
  single place cross-user access is denied.
- Cross-user access — reads and writes both — returns **404, not 403**.
  This matches the reasoning already applied to SIWE nonces in Phase 2: a
  403 would let a caller distinguish "this project doesn't exist" from
  "this project exists but isn't yours," which leaks information about
  which project IDs are valid. A caller who isn't the owner gets the same
  response either way.

## API

| Method | Path | Auth | Behavior |
|---|---|---|---|
| POST | `/api/v1/projects` | required | Register a project; owner = caller |
| GET | `/api/v1/projects/me` | required | List the caller's own projects |
| GET | `/api/v1/projects/{id}` | required | Fetch one owned project (404 if not owner) |
| PATCH | `/api/v1/projects/{id}` | required | Partial update of an owned project |

No delete endpoint — "register and manage" was read as create/read/update;
delete wasn't clearly required and was left out rather than guessed at. Can
be added later behind the same `get_owned_project` dependency if needed.

## Slug

`slug` is derived server-side from `name` at creation time (see
`service.py::_slugify`) and is **immutable** after creation — renaming a
project via `PATCH` does not change its slug. A name that collides with an
existing slug is rejected with `409 CONFLICT`, not silently deduplicated,
so the caller knows to pick a different name rather than getting a
surprise auto-suffixed identifier.

## Testing

`app/features/projects/test_projects.py` — 11 tests, all against a real
Postgres instance with real SIWE-authenticated sessions (reusing the same
login helper pattern as `auth/test_auth.py`), covering: unauthenticated
rejection, owner assignment, spoofed-owner-field rejection, owned
retrieval/update, list-my-projects scoping, cross-user read/update
rejection, nonexistent-project 404, invalid payload (422), duplicate-slug
conflict (409), and inactive-user rejection.
