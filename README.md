# Python Backend Template

Production-ready Python SaaS backend. Clone or fork, open in [Claude Code](https://claude.ai/code), and let it configure the project for your domain.

**Stack:** Python 3.12+ · Litestar · SQLAlchemy 2.0 async · Dishka DI · msgspec · PostgreSQL · Redis · S3 · Alembic · Granian

## Commands

```
/specialize          Configure this template for your project. Claude asks about your
                     domain, auth needs, and MVP scope, then renames the package,
                     removes unused code, scaffolds entities and endpoints, and
                     generates the initial migration. Run once after cloning.

/explain <question>  Ask a quick question about how the template works. Answers come
                     from .claude/ docs only — no codebase scan. Fast, but shallow.
                     For deeper analysis, use /research <topic> instead.
```
