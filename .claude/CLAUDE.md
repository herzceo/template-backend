# Python Backend Template

## Workflow — assess effort first, then act

For any implementation request — whether a plain prompt or an explicit `/impl` call — classify the effort tier inline before acting. Do not invoke `/impl` as a skill; apply the pipeline directly. The user can type `/impl [small|mid|tuff]` to override the detected tier.

Classify the effort tier:

**small** — all of these are true:
- Scoped to 1–2 existing files
- No new files, no new abstractions
- Modifying a value, condition, field, or small logic block

**mid** — any of these is true (and not tuff):
- Existing entity extended with new behavior (handler, endpoint, event, service)
- New well described entity + CRUDs, following established patterns
- One or more `/add-*` skills directly match the task
- 3–8 files, all following established patterns

**tuff** — any of these is true:
- New port, adapter, repo, or event as a new abstraction
- No existing `/add-*` skill covers the task
- Request uses "new domain", "from scratch", "design", or "architect"
- Implementation is multi-layered and requires architectural decisions

When ambiguous between mid and tuff → mid. Between small and mid → mid.

### small pipeline
1. Read the affected file(s)
2. Ask at most one clarifying question if genuinely ambiguous — otherwise proceed immediately
3. Make the change
4. Run `just check` — fix all issues before reporting done

### mid pipeline
1. Identify which `/add-*` skills apply and their execution order
2. Run `/research <domain>` — confirm existing patterns, never invent when an example exists
3. Execute the `/add-*` skills in dependency order (entity → repo → handler → controller → test)
4. Run `just check` — fix all issues
5. Delegate to **implementation-verifier** agent — fix any drift before reporting done

No plan file. No approval step.

### tuff pipeline
1. **Understand**: ask clarifying questions — business rules, scope, data model, side effects, error cases, naming (at least 2–3 questions)
2. **Research**: use `/research <topic>` — read all existing code that touches the domain
3. **Plan**: use `/plan <feature>` — every file, field, method signature, error case; no hand-waving
4. **Review plan**: use the plan-reviewer agent — fix every gap before proceeding
5. **Confirm**: present the reviewed plan to the user — wait for explicit approval; never infer it
6. **Implement**: follow the plan exactly, in dependency order — run `just check` after each major step
7. **Verify**: use the implementation-verifier agent — every planned file must exist, `just check` must pass
8. **Audit**: use the architecture-reviewer agent — fix any layer violations or pattern drift before reporting done

The user can type `/impl [small|mid|tuff] <description>` to explicitly force a tier.

## Knowledge Maintenance — keep `.claude/` in sync with the project

The `.claude/` configuration is a living document. Knowledge updates can happen at any point in any pipeline tier — during research, mid-implementation, or after verification. As the project evolves, propose updates:

- **New pattern discovered** during implementation? Propose adding it to the relevant rule in `rules/` or to CLAUDE.md Key Patterns.
- **New convention agreed** with the user (naming, structure, approach)? Propose updating the relevant rule.
- **New domain added** (entity, handlers, controller)? Propose updating skill templates if the new domain introduced a variation.
- **User corrects your approach**? Propose capturing the correction as a rule so it's not repeated.
- **New external integration** pattern? Propose updating `rules/external-services.md`.
- **New error type or handling pattern**? Propose updating `rules/error-handling.md`.

When proposing updates, be specific: name the file, quote the section, show the change. Don't silently absorb lessons — surface them as `.claude/` updates so future sessions benefit too.

## Stack
Python 3.12-3.13 | Litestar 2.21+ | SQLAlchemy 2.0 (async) | Dishka DI | msgspec DTOs | PostgreSQL | Redis | S3 | Alembic | Granian ASGI

## Architecture

```
backend/
├── domain/    Entities (SQLAlchemy ORM), Repository Protocols, Enums
├── app/       Use cases: REST handlers, event handlers, services, shared ports (Protocols), DTOs, errors
├── entry/     Framework glue: Litestar controllers, middleware, DI wiring (ioc.py), app factory
├── infra/     Implementations: PostgreSQL repos, Redis adapters, HTTP clients, S3, security
├── internal/  Utilities: Result[T,E], Option[T], StructDTO, DI helpers, case conversion
└── main/      CLI entry point (api / queue / alembic)
```

## Import Direction (strictly enforced by hooks)
- `domain/` imports only from `domain/`, `internal/`
- `app/` imports only from `app/`, `domain/`, `internal/` -- NEVER from `infra/` or `entry/`
- `entry/` imports from anything in `backend.*`
- `infra/` imports from `infra/`, `domain/`, `backend.app.shared.*` (ports, db), `internal/`
- `internal/` imports only from `internal/`
- Dependency inversion: `app/` defines Protocols in `app/shared/ports/`, `infra/` implements them

## Key Patterns

### Handler (app/rest/v1/handlers/)
`@dataclass` class inheriting `Handler[Command, ResponseDTO, Context]` with `type_=HandlerType.READ|WRITE`. Commands are `StructDTO` subclasses via `Command` base. Handlers are auto-registered via `__init_subclass__`. One handler per file.

### Repository (domain/repos/ + infra/database/psql/repos/)
Protocol interface in `domain/repos/` extending `CRUDSupported[Entity]`. Implementation in `infra/` via `ImplCRUDSupported[Entity]`. All lookups return `Option[T]` -- unwrap with `.some(ExceptionInstance)`. Central access via `RepoGateway` Protocol + `ImplRepoGateway` with `@cached_property`.

### Query Service (app/shared/db/query_services/ + infra/database/psql/queries/)
Read-only interfaces for complex queries that repositories can't serve efficiently (joins, aggregations, multi-table projections). Protocol in `app/shared/db/query_services/{domain}.py` — defines a `TypedDict` filter type and a `Protocol` returning shaped data. Implementation in `infra/database/psql/queries/{domain}.py` — `@final` class taking `async_sessionmaker[AsyncSession]`, opens a context-managed session per call. `ImplQueryServiceGateway` aggregates all services via `@cached_property`, mirrors `ImplRepoGateway`. Wired as `Scope.REQUEST` in `ioc.py` via `create_query_services_provider()`. Handlers that only read inject `QueryServiceGateway` instead of `Database`.

### Port / Adapter (app/shared/ports/ + infra/external/adapters/)
Port = `Protocol` in `app/shared/ports/{category}/`. Adapter = `@final` class in `infra/external/adapters/`. Naming: port = `PasswordHasher`, adapter = `ImplArgon2PasswordHasher`. Adapters never imported by `app/`.

### Dependency Injection (entry/rest/main/ioc.py)
Dishka `Provider(scope=Scope.APP|REQUEST)`. Bind impl to Protocol: `provider.provide(ImplClass, provides=ProtocolType)`. `Depends[Type]` for parameter injection. `DishkaRouter` in `create_v1_router()` auto-applies injection to all controllers — no per-route `@inject` needed.

### Error Handling (app/errors.py + internal/result.py + internal/option.py)
`DetailedError(message, code, details)` hierarchy. `Option[T].some(exc)` for repo lookups. `Result[T,E] = Ok[T] | Err[E]` with `.raise_()` for HTTP client responses.

### DTOs (internal/dto/ + app/rest/v1/dtos/ + entry/rest/v1/dtos.py)
All DTOs are `StructDTO` (msgspec.Struct). App DTOs = response shapes (`app/rest/v1/dtos/`). Entry DTOs = request bodies (`entry/rest/v1/dtos.py`). Conversion: `DTO.from_object(entity)`.

### Controllers (entry/rest/v1/)
Litestar `Controller` subclass. Route methods use only the HTTP method decorator (`@get|@post|@patch|@delete`) — no `@inject` (handled by `DishkaRouter`) and no `@result` (handled by the router-level `after_request=wrap_ok` hook in `create_v1_router()`). Handler injected via `Depends[HandlerType]`. Controllers convert `str` path params to `UUID`/`datetime`/enum before creating commands. Registered in `create_v1_router()`. Non-CRUD operations use Google-style `:camelCaseVerb` suffix (`@post("/{id:str}:assignRole")`). List endpoints use `offset: int = 0, limit: int = 50` query params. Controllers needing collection-level custom methods (e.g., `/auth:signIn`) set `path = ""` and use explicit full paths.

### Entities (domain/entities/)
SQLAlchemy `DeclarativeBase` with mixins: `WithUUIDID`, `WithActive`, `WithTime`, `WithTenant`. Mixin order: `WithUUIDID, WithActive, WithTime, WithTenant, Base`. Auto table naming. `Mapped[T]` with `mapped_column()`. Relationships use `lazy="raise"`. Companion entities (1:1 satellites of a primary entity) use only `WithUUIDID, WithTime, Base` and are always created in the same transaction as their primary — see `Profile` as the canonical example (`backend/domain/entities/profile.py`).

### Database / DBus (app/shared/db/)
`Database` Protocol (UoW + `RepoGateway` + `dbus` access) and `DBus` Protocol (transactional outbox publish) live in `app/shared/db/`. `DBus` is NOT injected — access it via `self.db.dbus`. `db.dbus` raises `RuntimeError` outside `async with self.db:` blocks, enforcing that events are always published within the same transaction as the business data.

### Events (app/shared/events/ + app/events/ + infra/database/psql/dbus/)
`BaseEvent(StructDTO, kw_only=True)` with `name: ClassVar[str]`. Publish via `self.db.dbus.publish(event)` inside `async with self.db:`. `EventHandler[E]` with auto-registration keyed by event name. Background execution via PostgreSQL job queue (`infra/database/psql/dbus/`).

## Code Style
- ruff `select = ["ALL"]`, line-length 100. Strict mypy.
- No useless comments, no section dividers
- No function-level imports -- all top-level or `if TYPE_CHECKING:`
- `@final` on every concrete implementation class
- `ImplXxx` naming for implementations
- One primary class per file, explicit `__all__` exports in `__init__.py`
- Python 3.12+ generics: `class X[T]:` not `Generic[T]`
- All commands run through `uv run` -- never bare `python3` or `python`

## Commands
- `just check` -- ruff format + ruff check + mypy + layer guard (full project)
- `just run api` / `just run queue` -- start services
- `just migrate` -- alembic upgrade head
- `just migration "description"` -- autogenerate migration
- `just start` / `just stop` / `just delete` -- Docker Compose
- `just test` -- integration tests (testcontainers, requires Docker)
- `just test-unit` -- unit tests (no Docker needed)
- `just test-all` -- all test sessions

## Git — worktree workflow
All commits made during a worktree session (code, fixes, docs, knowledge updates) go on the **feature branch**. All git operations stay inside the worktree — never use `git -C` to operate on the parent repo.

End-of-session: push the feature branch with the translated name, then ask the user to merge it into `main`:
```bash
LOCAL=$(git branch --show-current)
REMOTE=$(echo "$LOCAL" | sed 's/^worktree-//; s/+/\//g')
git push -u origin "$LOCAL:$REMOTE"
```

Hard rules — no exceptions:
- Never force-push `main`
- Never cherry-pick commits between branches
- Never push the raw `worktree-*` branch name to origin

## Rules (`.claude/rules/`) -- loaded contextually by file path
architecture, entities, handlers, repositories, dtos, controllers, ports-adapters, dependency-injection, error-handling, typing, database, events, external-services, code-style, testing, git

## Skills (`.claude/skills/`)

User-invoked overrides:
- `/impl [small|mid|tuff] <change>` -- forces a specific effort tier; omit the tier to confirm auto-detection
- `/chat <problem>` -- design consultation before committing to an approach; outputs options + trade-offs + recommendation; no code written

Project setup (use when forking this template):
- `/specialize` -- interactive session: asks about your domain, auth, infra, and MVP scope, then renames the package, prunes unused code, scaffolds your entities/endpoints, and replaces the init migration

Template orientation:
- `/help` -- overview of the template, all commands, and how to start
- `/explain <question>` -- quick answer from `.claude/` docs only; no codebase scan; for simple conceptual questions

Planning (use BEFORE writing code):
- `/plan <feature>` -- structured planning with questions, research, detailed component spec
- `/research <topic>` -- investigate codebase before making changes

Knowledge (keep `.claude/` in sync):
- `/update-knowledge [topic]` -- review and update rules, skills, agents after changes

Implementation (use DURING coding):
- `/add-endpoint <domain> <action> <method>` -- full endpoint pipeline
- `/add-entity <name> <fields>` -- domain entity + migration
- `/add-repository <entity>` -- protocol + impl + gateway wire
- `/add-handler <domain> <action>` -- command + handler
- `/add-port <category> <name>` -- protocol + adapter + DI wire
- `/add-event <name>` -- event + publisher + handler
- `/add-http-client <service>` -- HTTP client + adapter
- `/add-migration <description>` -- Alembic autogenerate
- `/add-service <domain> <name>` -- application service
- `/add-test <domain> <action>` -- integration test for an endpoint or event handler

Test feedback loop (use AFTER coding):
- `/run-tests <domain | path | category> [pattern]` -- scoped pytest run, faster than `just test`
- `/debug-failing-test <test-path>` -- decision-tree diagnosis using project test recipes

## Agents (`.claude/agents/`)

Quality gates (enforce the workflow):
- **plan-reviewer** -- validates plan completeness before implementation. MUST pass.
- **implementation-verifier** -- validates code matches plan after implementation. MUST pass.

Review (catch issues):
- **architecture-reviewer** -- audits layer violations, import direction, pattern adherence
- **code-reviewer** -- quality, security, typing, pattern compliance review
- **migration-reviewer** -- audits Alembic migrations for data loss, NOT NULL footguns, missing FK indexes, locking, entity drift

Design (research and design):
- **domain-designer** -- designs entities, repos, events, ports (read-only)
- **feature-implementer** -- orchestrates full feature implementation end-to-end

Knowledge (keep docs accurate):
- **knowledge-maintainer** -- audits `.claude/` against codebase, finds stale/missing docs
