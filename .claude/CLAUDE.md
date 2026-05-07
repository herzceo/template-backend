# Python Backend Template

## Workflow — ALWAYS follow this before writing code

1. **Understand**: read the request carefully. Identify ambiguities, edge cases, missing details.
2. **Ask questions**: do NOT assume. Ask about business rules, expected behavior, error cases, naming, scope boundaries. Ask at least 2-3 clarifying questions before any non-trivial feature.
3. **Research**: use `/research <topic>` or the domain-designer agent. Read existing code that touches the same domain. Find patterns to reuse.
4. **Plan**: use `/plan <feature>` to produce a structured plan. Every file, every field, every method signature, every error case. No hand-waving.
5. **Review plan**: use the plan-reviewer agent to verify the plan is complete. Fix any gaps it finds. The plan MUST pass review before coding.
6. **Confirm**: present the reviewed plan to the user. Wait for explicit approval. Never start coding on assumption.
7. **Implement**: follow the plan exactly, in dependency order (inner layers first). Run `just check` after each major step. Do not deviate from the plan without asking.
8. **Verify**: use the implementation-verifier agent to check the result matches the plan. Every planned file must exist, every pattern must be followed, `just check` must pass.

For trivial changes (typo fix, single-line edit), skip to step 7. For everything else, steps 1-6 are mandatory. Skipping planning is not allowed.

## Knowledge Maintenance — keep `.claude/` in sync with the project

The `.claude/` configuration is a living document. As the project evolves, propose updates:

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
- `infra/` imports from `infra/`, `domain/`, `backend.app.shared.*` (ports only), `internal/`
- `internal/` imports only from `internal/`
- Dependency inversion: `app/` defines Protocols in `app/shared/ports/`, `infra/` implements them

## Key Patterns

### Handler (app/rest/v1/handlers/)
`@dataclass` class inheriting `Handler[Command, ResponseDTO, Context]` with `type_=HandlerType.READ|WRITE`. Commands are `StructDTO` subclasses via `Command` base. Handlers are auto-registered via `__init_subclass__`. One handler per file.

### Repository (domain/repos/ + infra/database/psql/repos/)
Protocol interface in `domain/repos/` extending `CRUDSupported[Entity]`. Implementation in `infra/` via `ImplCRUDSupported[Entity]`. All lookups return `Option[T]` -- unwrap with `.some(ExceptionInstance)`. Central access via `RepoGateway` Protocol + `ImplRepoGateway` with `@cached_property`.

### Port / Adapter (app/shared/ports/ + infra/external/adapters/)
Port = `Protocol` in `app/shared/ports/{category}/`. Adapter = `@final` class in `infra/external/adapters/`. Naming: port = `PasswordHasher`, adapter = `ImplArgon2PasswordHasher`. Adapters never imported by `app/`.

### Dependency Injection (entry/rest/main/ioc.py)
Dishka `Provider(scope=Scope.APP|REQUEST)`. Bind impl to Protocol: `provider.provide(ImplClass, provides=ProtocolType)`. `@inject` decorator on controller methods. `Depends[Type]` for parameter injection.

### Error Handling (app/errors.py + internal/result.py + internal/option.py)
`DetailedError(message, code, details)` hierarchy. `Option[T].some(exc)` for repo lookups. `Result[T,E] = Ok[T] | Err[E]` with `.raise_()` for HTTP client responses.

### DTOs (internal/dto/ + app/rest/v1/dtos/ + entry/rest/v1/dtos.py)
All DTOs are `StructDTO` (msgspec.Struct). App DTOs = response shapes (`app/rest/v1/dtos/`). Entry DTOs = request bodies (`entry/rest/v1/dtos.py`). Conversion: `DTO.from_object(entity)`.

### Controllers (entry/rest/v1/)
Litestar `Controller` subclass. Decorator order: `@get|@post` -> `@inject` -> `@result`. Handler injected via `Depends[HandlerType]`. Controllers convert `str` path params to `UUID`/`datetime`/enum before creating commands. Registered in `create_v1_router()`.

### Entities (domain/entities/)
SQLAlchemy `DeclarativeBase` with mixins: `WithUUIDID`, `WithActive`, `WithTime`, `WithTenant`. Mixin order: `WithUUIDID, WithActive, WithTime, WithTenant, Base`. Auto table naming. `Mapped[T]` with `mapped_column()`. Relationships use `lazy="raise"`.

### Events (app/shared/events/ + app/events/ + infra/dbus/)
`BaseEvent(StructDTO, kw_only=True)` with `name: ClassVar[str]`. Publish via `DBus.publish(event)`. `EventHandler[E]` with auto-registration keyed by event name. Background execution via PostgreSQL job queue.

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

## Rules (`.claude/rules/`) -- loaded contextually by file path
architecture, entities, handlers, repositories, dtos, controllers, ports-adapters, dependency-injection, error-handling, typing, database, events, external-services, code-style, testing

## Skills (`.claude/skills/`)

Project setup (use when forking this template):
- `/specialize` -- interactive session: asks about your domain, auth, infra, and MVP scope, then renames the package, prunes unused code, scaffolds your entities/endpoints, and replaces the init migration

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
