---
name: front
description: Summarize the API interface changes from this session for the frontend, then optionally spawn an agent to implement them in the frontend repo. Use after changing endpoints, request/response DTOs, or auth.
argument-hint: "[--implement | --summary-only]"
---

# Frontend Handoff

Summarize the API interface changes made in this session into a frontend-facing
contract, then optionally drive a frontend agent to implement them. The backend
repo is read-only for this skill — nothing here edits backend code.

## Arguments

- `$0` (optional) — flow control:
  - `--implement` — skip the confirmation and spawn the frontend agent immediately
  - `--summary-only` — emit the summary and stop; never offer to spawn
  - omitted (default) — summarize, then ask whether to spawn

## Step 1: Locate the frontend repo

Current config:
!`cat .claude/frontend.json 2>/dev/null || echo "MISSING"`

- If the output is `MISSING` or the configured `path` does not exist on disk, ask
  the user for the frontend repo's **absolute path** (and an optional one-line
  stack note, e.g. framework + where the API client lives). Write their answer to
  `.claude/frontend.json` using the schema in `.claude/frontend.example.json`,
  then continue.
- A valid `path` is required only to spawn the agent in Step 4. The summary in
  Steps 2–3 works without it — if the user only wants the summary, don't block on
  the config.

## Step 2: Determine change scope (auto)

Uncommitted interface changes:
!`git diff --stat HEAD -- backend/entry/rest/v1 backend/app/rest/v1/dtos 2>/dev/null`

Branch interface changes vs main:
!`git diff --stat main...HEAD -- backend/entry/rest/v1 backend/app/rest/v1/dtos 2>/dev/null`

Recent commits:
!`git log --oneline -10 2>/dev/null`

Pick the scope from the stats above:

- If the **uncommitted** stat is non-empty → scope = **working tree**. Get full
  detail with `git diff HEAD -- backend/entry/rest/v1 backend/app/rest/v1/dtos`.
- Else if the **branch** stat is non-empty → scope = **branch vs main**. Get full
  detail with `git diff main...HEAD -- backend/entry/rest/v1 backend/app/rest/v1/dtos`.
- If both are empty → report "No interface changes detected" and stop.

State the chosen scope explicitly before building the summary.

## Step 3: Build the interface summary

Read the changed controller and DTO files and resolve each change into the
frontend-facing contract. Sources of truth:

- HTTP method + path — controller decorators in `backend/entry/rest/v1/*.py` and
  the mounted route list in `backend/entry/rest/v1/__init__.py` (`create_v1_router`)
- Auth requirement — guards/dependencies on the controller method
- Request body shape — the `*Body` `StructDTO` in `backend/entry/rest/v1/dtos.py`
- Response shape — the response DTO in `backend/app/rest/v1/dtos/`
- Error/status codes — raised errors and their `code`

Classify every endpoint and DTO change as **Added**, **Changed**, or **Removed**.
Every line in the output must trace to a real route or DTO field — never infer.

## Output Format

```markdown
# Frontend interface changes — {scope}

## Summary
{1–2 sentence what-changed-and-why}

## Endpoints
### {ADDED|CHANGED|REMOVED} `{METHOD} {path}`
- **Auth**: required | public
- **Request**: `{BodyName}` { field: type, ... } | none
- **Response**: `{DtoName}` { field: type, ... }
- **Errors**: {status + code, e.g. 409 conflict} | none
- **Notes**: {pagination, enum values, breaking-change callout}

## DTO shape changes
- `{DtoName}.{field}`: {added | removed | type X→Y}

## Frontend action items
- {concrete change the FE must make, e.g. "update api client signIn() return type"}
```

## Step 4: Offer to implement

Skip this step entirely if `$0` is `--summary-only`.

Otherwise, unless `$0` is `--implement` (which skips the prompt), ask the user
whether to spawn a frontend agent to implement the changes. On confirmation —
and only if `.claude/frontend.json` has a valid `path` — delegate to a
general-purpose agent via the Agent tool. The agent prompt must:

- State the frontend repo **absolute path** and the stack note from `frontend.json`.
- Embed the full Step-3 summary verbatim.
- Instruct the agent to:
  - Operate **only inside the frontend repo**, using absolute paths; `cd` into it
    for any frontend tooling (install / lint / test).
  - Discover the frontend's API-client layer and conventions before editing.
  - Implement the **Frontend action items**.
  - Run the frontend's own checks if present.
  - Return a short report of the files it changed.
- Be explicit that the **backend repo is read-only context** — the agent must not
  edit backend files.

Relay the agent's report back to the user.

## What NOT to do

- Do not edit backend files — this skill is read-only on the backend.
- Do not spawn the agent without a valid configured frontend `path`.
- Do not invent endpoints or fields — every line traces to a controller or DTO.
- Do not summarize non-interface changes (internal services, repos, infra).
