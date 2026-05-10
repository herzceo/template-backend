# Python Backend Template

Production-ready Python SaaS backend. Clone or fork, open in [Claude Code](https://claude.ai/code), and let it configure the project for your domain.

**Stack:** Python 3.12+ · Litestar · SQLAlchemy 2.0 async · Dishka DI · msgspec · PostgreSQL · Redis · S3 · Alembic · Granian

## Commands

```
/help                Show all available commands and how to get started.

/specialize          Configure this template for your project. Claude asks about your
                     domain, auth needs, and MVP scope, then renames the package,
                     removes unused code, scaffolds entities and endpoints, and
                     generates the initial migration. Run once after cloning.

/explain <question>  Ask a quick question about how the template works. Answers come
                     from .claude/ docs only — no codebase scan. Fast, but shallow.
                     For deeper analysis, use /research <topic> instead.

/impl [small|mid|   Implement a change. Auto-detects the appropriate pipeline based on
large] <description> complexity: small (1–2 files, in-place edit), mid (chain of /add-*
                     skills), or large (full planning cycle with review and approval).
                     Pass a tier explicitly to force it.

/chat <problem>      Design consultation before committing to an approach. Claude asks
                     about your priorities, researches the codebase and established
                     patterns (DDD, Clean Architecture, CQRS, etc.), and presents 2–3
                     options with trade-offs and a recommendation. No code is written.
```
