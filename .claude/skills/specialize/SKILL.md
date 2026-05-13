---
name: specialize
description: One-shot guided session — prunes unused code, scaffolds new entities/endpoints, updates project identity config, and replaces the init migration for a specific project.
---

# Specialize This Template

Configure this generic SaaS backend for a specific project in a single guided session. You will ask questions, generate a complete removal + addition plan, get approval, then execute everything.

This skill orchestrates. It does not define patterns — those live in `.claude/rules/` and the add-* skills. For each new entity, repo, endpoint, or external integration, delegate to the appropriate skill.

---

## Phase 1 — Discovery

Run four rounds of `AskUserQuestion`. Batch questions to avoid overwhelming the user. Do not ask about implementation patterns or architecture — those are already covered.

### Round 1 — Project Identity

Three questions in one call:

1. **Project slug** — used for project identity: display name, docker container/volume prefix, pyproject metadata. Must be a valid Python identifier: lowercase letters, digits, underscores only, starts with a letter. Example: `shop_api`, `crm`, `my_app`. **The Python package folder stays `backend/` — do not rename it.**
2. **Display name** — human-readable title used in OpenAPI docs and README. Example: "Shop API".
3. **One-line description** — what this project does.

Validate the slug before proceeding: `re.match(r'^[a-z][a-z0-9_]*$', slug)`. If invalid, re-ask.

### Round 2 — Domain Model & Auth

Four questions in one call:

1. **MVP business entities** — open text, comma-separated. Example: "Product, Order, Review". These are the domain models that will be created. Template-provided entities (User, Role, Session, etc.) are separate.
2. **Auth flows to keep** — multi-select: `Email + password`, `Google OAuth`, `GitHub OAuth`, `Discord OAuth`. Select none to remove auth entirely (unusual — confirm if so).
3. **Multi-tenancy** — keep the `WithTenant` mixin on new entities and the existing Tenant entity, or remove it?
4. **RBAC** — keep full (Role + Permission M2M), simplify to Role only (remove Permission entity), or remove entirely?

### Round 3 — Infrastructure & Integrations

Four questions in one call:

1. **Built-in systems to keep** — multi-select: `S3 file storage (Asset entity + presigned URLs)`, `Background job queue (Worker + Job entities)`, `Audit logging (AuditLog entity)`, `Notifications (Notification entity)`, `Redis rate limiting`.
2. **Email** — keep Resend, use a different provider (ask which after), or no email at all?
3. **Analytics & maps** — multi-select: `Amplitude`, `Google Maps`, `Neither`.
4. **New external integrations** — open text. List services not in the template that the MVP needs. Example: "Stripe for payments, Twilio for SMS". Write "none" if none.

### Round 4 — MVP Endpoints & CORS

Two questions in one call:

1. **MVP endpoints** — open text. Describe the REST endpoints needed. Example: "Full CRUD for Product, list + get for Order, POST /checkout".
2. **Frontend origin** — the URL of the frontend that will call this API. Used for CORS. Example: `https://myapp.com`. Write `*` if unknown or open.

---

## Phase 2 — Research

After gathering answers, read the current state before producing the plan:

```
Current entities:
```
!`find backend/domain/entities -name "*.py" -not -name "__init__.py" -not -path "*__pycache__*" 2>/dev/null | sort`

```
Current handler directories:
```
!`find backend/app/rest/v1/handlers -mindepth 1 -maxdepth 1 -type d 2>/dev/null | sort`

```
Current controllers registered:
```
!`grep -n "Controller\|health" backend/entry/rest/v1/__init__.py 2>/dev/null`

```
Current ioc.py providers:
```
!`grep -n "^def create_" backend/entry/rest/main/ioc.py 2>/dev/null`

```
Current .env.example keys:
```
!`grep -E "^[A-Z]" .env.example 2>/dev/null | cut -d= -f1 | sort`

```
Existing migration files:
```
!`find backend/infra/database/alembic/migrations/versions -name "*.py" -not -name "__init__.py" 2>/dev/null`

Use this inventory to build the concrete file lists in the plan.

---

## Phase 3 — Plan Generation

Output the following plan. No files are touched in this phase.

```markdown
# Specialization Plan: {DisplayName}

## Files to DELETE

### Entities (and their repo protocols + implementations)
- backend/domain/entities/{name}.py — {reason}
  + backend/domain/repos/{name}.py
  + backend/infra/database/psql/repos/{name}.py
  (repeat per removed entity)

### Handler domains (entire directories)
- backend/app/rest/v1/handlers/{domain}/ — {reason}
  (repeat per removed domain)

### Controllers to remove from create_v1_router()
- {ControllerName} — {reason}

### External clients & adapters
- backend/infra/external/http/oauth/{provider}.py
- backend/infra/external/adapters/{provider}_oauth.py
  (repeat per removed OAuth provider)
- (any other removed external clients)

### ioc.py: providers / bindings to remove
- {function or binding} — {reason}

### Events & event handlers
- backend/app/shared/events/v1/{event}.py — {reason}
- backend/app/events/v1/handlers/{domain}/{event}.py

### Tests for removed domains
- tests/integration/api/v1/{domain}/ — NOTE: delete manually after reviewing for reusable patterns

## Files to CREATE

### Domain entities (new business objects)
- {slug}/domain/entities/{entity}.py
  Fields: {field}: {type}, ...  |  Mixins: {list}
  (repeat per entity)

### Handlers + endpoints
- {HTTP method} /{path} — {action} on {Entity}
  (repeat per MVP endpoint)

### New external integrations (from Round 3 open text)
- {ServiceName}: port + adapter + HTTP client
  (repeat per new integration)

## Config Updates

### pyproject.toml
- [project] name: "backend" → "{slug}" (metadata only — scripts entry and imports stay as `backend`)
- [project] description: → "{description}"

### .env.example
Remove: {list of env vars for removed integrations}
Add: {list of env vars for new integrations}
Update: NAME="{DisplayName}", DESCRIPTION="{description}", CORS_ALLOW_ORIGINS="{frontend_origin}"

### docker-compose.local.yaml
- Container name prefix: `template.local.` → `{slug}.local.`
- Volume names: `template.local.psql_data` → `{slug}.local.psql_data`, etc.
- Command arrays (`["backend", "api"]`, alembic) stay unchanged

### .claude/CLAUDE.md
- Update display name references if any

## Migration Replacement
- Delete: backend/infra/database/alembic/migrations/versions/2026_04_30_*.py
- Generate: `just migration "init"` (run after all entities are in place)

## Execution Order
1. Git checkpoint commit
2. Package rename (mv + sed)
3. Delete unused files; rebuild affected __init__.py exports
4. Scaffold new entities — /add-entity for each
5. Scaffold new repos — /add-repository for each
6. Scaffold new handlers + endpoints — /add-endpoint for each
7. New external integrations — /add-port for each
8. Update config files
9. Delete old migration → `just migration "init"`
10. `just check`

## Scope Summary
Deleting X files/directories, creating Y new components, updating Z config files.
```

---

## Phase 4 — Approval Gate

Present the plan in full. State the scope summary. **Do not touch any file until the user explicitly approves.**

---

## Phase 5 — Execution

Execute in the order listed in the plan. Steps unique to specialization are described below. Everything else delegates to the appropriate skill.

### 5.1 — Git Checkpoint

```bash
git add -A && git commit -m "chore: pre-specialization snapshot"
```

### 5.2 — Docker Container/Volume Prefix

The `backend/` package folder is never renamed. Only the docker-compose container/volume prefix changes:

```bash
sed -i '' 's/template\.local\./{slug}.local./g' docker-compose.local.yaml
```

### 5.3 — Delete Unused Files

Delete each file and directory in the DELETE list. After bulk deletes:
- Remove stale exports from `backend/domain/entities/__init__.py`
- Remove stale exports from `backend/domain/repos/__init__.py`
- Remove stale entries from `backend/infra/database/psql/repos/__init__.py`
- Remove stale gateway properties from `backend/domain/repos/gateway.py` and its impl
- Remove stale controller imports and route_handlers entries from `backend/entry/rest/v1/__init__.py`
- Remove stale provider bindings from `backend/entry/rest/main/ioc.py`

### 5.4 — Scaffold New Entities, Repos, Handlers, Endpoints

For each new entity: invoke `/add-entity`.
For each new repo: invoke `/add-repository`.
For each new endpoint: invoke `/add-endpoint`.

These skills carry all pattern knowledge. Do not re-implement what they already describe.

### 5.5 — New External Integrations

For each new external service from Round 3: invoke `/add-port`.
For HTTP-based services: invoke `/add-http-client` first, then wire via `/add-port`.

### 5.6 — Config Updates

Edit `pyproject.toml`, `.env.example`, `.claude/CLAUDE.md` with the Edit tool per the plan's Config Updates section.

For `.env.example`: add a comment block for secrets that need generation:
```
# Generate with: openssl rand -base64 32
OAUTH_STATE_SECRET=
```

### 5.7 — Migration Replacement

```bash
rm backend/infra/database/alembic/migrations/versions/2026_04_30_*.py
just migration "init"
```

### 5.8 — Verification

```bash
just check
```

Diagnose and fix any failures before reporting completion. Do not report the skill as done until `just check` passes clean.
