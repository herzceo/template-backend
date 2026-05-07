# Python Backend Template

> **New project?** Open in [Claude Code](https://claude.ai/code) and run `/specialize` — guided setup in ~5 minutes.

A production-ready Python SaaS backend. Clone or fork, then let Claude configure it for your domain.

## Quick Start

1. Clone or fork this repository
2. Open the project in [Claude Code](https://claude.ai/code)
3. Type `/specialize` and press Enter
4. Answer questions about your project (~5 min)
5. Review the specialization plan, then approve
6. Claude executes all changes: renames the package, removes unused code, scaffolds your entities and endpoints, generates your first migration

## Stack

Python 3.12+ · Litestar 2.21+ · SQLAlchemy 2.0 async · Dishka DI · msgspec · PostgreSQL · Redis · S3 · Alembic · Granian

## What the Template Includes

- **Auth** — email/password signup, email verification, OAuth (Google / GitHub / Discord), session management
- **RBAC** — roles, permissions, multi-tenancy via per-entity tenant scoping
- **Storage** — S3 / S3-compatible presigned URL uploads with blurhash
- **Background jobs** — PostgreSQL-backed job queue with worker entry point
- **Async event bus** — side-effect events via database-backed DBus
- **Audit logging, notifications, assets** — ready-made entities and handlers
- **Integration test suite** — testcontainers (real Postgres + Redis), factory helpers, mock ports
- **OpenAPI / Scalar docs** — at `/docs`

## Architecture

```
{pkg}/
├── domain/    Entities, repository protocols, enums
├── app/       Handlers, services, DTOs, shared ports (Protocols)
├── entry/     Litestar controllers, middleware, DI wiring
├── infra/     PostgreSQL/Redis/S3 implementations, HTTP clients, adapters
├── internal/  Result[T,E], Option[T], StructDTO, DI helpers
└── main/      CLI entry point (api / queue / alembic)
```

Import direction is strictly enforced: `domain → internal`, `app → domain + internal`, `infra → domain + app.shared.ports`, `entry → anything`.

## Development Commands

| Command | What it does |
|---|---|
| `just init` | Install dependencies (`uv sync`) |
| `just check` | Format + lint + type check + layer guard |
| `just run` | Start API server |
| `just test` | Integration tests (requires Docker) |
| `just test-unit` | Unit tests |
| `just migrate` | Apply pending migrations |
| `just migration "msg"` | Generate new Alembic migration |
| `just start` | Start Docker services (Postgres, Redis) |
| `just stop` | Stop Docker services |

## Claude Code Workflow

This template ships with a full `.claude/` configuration: rules loaded by file path, skills for every development task, and quality-gate agents.

See `.claude/CLAUDE.md` for the complete workflow, skill list, and agent references.
