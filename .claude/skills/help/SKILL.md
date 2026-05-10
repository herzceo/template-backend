---
name: help
description: Show an overview of this template — what it is, available commands, and how to start.
---

# Help

Output the following text verbatim:

---

## Python Backend Template

Production-ready Python SaaS backend. Stack: Python 3.12+ · Litestar · SQLAlchemy 2.0 async · Dishka DI · msgspec · PostgreSQL · Redis · S3 · Alembic · Granian.

---

### Getting started

1. Clone or fork this repo
2. Open in Claude Code
3. Run `/specialize` — Claude will ask about your domain, auth needs, and MVP scope, then configure the project for you

---

### Commands

**Setup**
- `/specialize` — one-time project configuration: renames the package, prunes unused code, scaffolds your entities and endpoints, generates the initial migration

**Implementation**
- `/impl [small|mid|large] <change>` — implement anything; Claude auto-detects the right pipeline (small = in-place edit, mid = chain of /add-* skills, large = full planning cycle); pass a tier to override
- `/chat <problem>` — design consultation before committing to an approach; Claude researches patterns and presents options with trade-offs; no code written

**Planning**
- `/plan <feature>` — produce a detailed implementation plan; used inside the large pipeline
- `/research <topic>` — investigate the codebase before making changes

**Building blocks** (used inside `/impl mid`, or directly)
- `/add-endpoint <domain> <action> <method>` — full endpoint pipeline
- `/add-entity <name> <fields>` — domain entity + migration
- `/add-repository <entity>` — protocol + impl + gateway wire
- `/add-handler <domain> <action>` — command + handler
- `/add-port <category> <name>` — protocol + adapter + DI wire
- `/add-event <name>` — event + publisher + handler
- `/add-http-client <service>` — HTTP client + adapter
- `/add-migration <description>` — Alembic autogenerate
- `/add-service <domain> <name>` — application service
- `/add-test <domain> <action>` — integration test

**Testing**
- `/run-tests <domain | path | category>` — scoped test run, faster than `just test`
- `/debug-failing-test <test-path>` — diagnose a failing test with project-specific recipes

**Knowledge**
- `/update-knowledge [topic]` — update `.claude/` docs to reflect current codebase state
- `/explain <question>` — quick answer from `.claude/` docs; no codebase scan

---

### Shell commands

```
just check          ruff format + ruff check + mypy + layer guard
just run api        start the API server
just run queue      start the job queue worker
just test           integration tests (requires Docker)
just test-unit      unit tests (no Docker)
just migrate        apply pending migrations
just migration "x"  autogenerate a new migration
just start          start Docker Compose stack
just stop           stop Docker Compose stack
```
