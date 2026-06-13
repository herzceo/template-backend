---
name: front
description: Summarize the API interface changes made during THIS session for the frontend, then optionally spawn an agent to implement them in the frontend repo. Use after changing endpoints, request/response DTOs, or auth.
argument-hint: "[--implement | --summary-only]"
---

# Frontend Handoff

Summarize the API interface changes **you made during this session** into a
frontend-facing contract, then optionally drive a frontend agent to implement
them. The backend repo is read-only for this skill — nothing here edits backend
code.

## Arguments

- `$0` (optional) — flow control:
  - `--implement` — skip the confirmation and spawn the frontend agent immediately
  - `--summary-only` — emit the summary and stop; never offer to spawn
  - omitted (default) — summarize, then ask whether to spawn

## Step 1: Recall this session's interface changes

The source of truth is **your own memory of what you changed in this session** —
the endpoints, request/response DTOs, auth requirements, and error codes you
added, changed, or removed while working. Do **not** scan git history, branch
diffs, or the worktree to discover scope; only summarize work done in the
current session.

If you made no interface changes this session, say "No interface changes were
made this session" and stop. Do not fall back to diffing git.

You may re-open the specific files you edited this session to get exact field
names and types right — but only files you actually touched, to confirm detail,
not to discover new scope. Sources of truth for detail:

- HTTP method + path — controller decorators in `backend/entry/rest/v1/*.py` and
  the mounted route list in `backend/entry/rest/v1/__init__.py` (`create_v1_router`)
- Auth requirement — guards/dependencies on the controller method
- Request body shape — the `*Body` `StructDTO` in `backend/entry/rest/v1/dtos.py`
- Response shape — the response DTO in `backend/app/rest/v1/dtos/`
- Error/status codes — raised errors and their `code`

## Step 2: Build the interface summary

Classify every endpoint and DTO change as **Added**, **Changed**, or **Removed**.
Every line in the output must trace to a real route or DTO field you touched this
session — never infer.

## Output Format

```markdown
# Frontend interface changes — this session

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

## Step 3: Offer to implement

Skip this step entirely if `$0` is `--summary-only`.

Otherwise, unless `$0` is `--implement` (which skips the prompt), ask the user
whether to spawn a frontend agent to implement the changes.

Only when the user opts to implement (via `--implement` or by confirming), locate
the frontend repo:

!`cat .claude/frontend.json 2>/dev/null`

- If that config is absent or its `path` does not exist on disk, ask the user for
  the frontend repo's **absolute path** (and an optional one-line stack note, e.g.
  framework + where the API client lives). Write their answer to
  `.claude/frontend.json` using the schema in `.claude/frontend.example.json`,
  then continue.
- Do not raise the missing config before this point — the default summary never
  needs it, so never announce that the config is empty or missing while
  summarizing.

With a valid `path`, delegate to a general-purpose agent via the Agent tool. The
agent prompt must:

- State the frontend repo **absolute path** and the stack note from `frontend.json`.
- Embed the full Step-2 summary verbatim.
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
- Do not scan git diffs, branch history, or the worktree to determine scope — the
  scope is what you changed in this session.
- Do not announce that `.claude/frontend.json` is missing or empty while
  summarizing; the config is only needed to spawn the implement agent.
- Do not spawn the agent without a valid configured frontend `path`.
- Do not invent endpoints or fields — every line traces to a controller or DTO you
  touched this session.
- Do not summarize non-interface changes (internal services, repos, infra).
