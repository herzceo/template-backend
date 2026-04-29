---
name: add-migration
description: Generate and apply an Alembic migration. Use after modifying entities or when schema changes are needed.
argument-hint: <description>
---

# Add a Migration

Generate an Alembic migration from entity changes and apply it.

## Arguments

- `$0` -- Migration description (e.g., `add invoices table`, `add status column to orders`)

## Implementation Steps

### 1. Verify entity exports

Ensure all entities are imported in `backend/domain/entities/__init__.py`. Alembic's `env.py` imports this module to discover models.

```bash
cat backend/domain/entities/__init__.py
```

### 2. Generate migration

```bash
just migration "$0"
```

This runs `alembic revision --autogenerate -m "$0"`.

### 3. Review generated migration

Read the new file in `backend/infra/database/alembic/migrations/versions/`.

Check for:
- Correct column types and constraints
- Proper index creation
- Foreign key references
- Nullable settings
- Enum type handling (PostgreSQL enums need special care)
- Default values

### 4. Apply migration

```bash
just migrate
```

This runs `alembic upgrade head`.

### 5. Verify

Check that the migration applied cleanly. Run `just check` to ensure no type errors.

## Common Issues

- **Missing entity import**: If autogenerate produces an empty migration, the entity is likely not imported in `__init__.py`
- **Enum columns**: PostgreSQL requires explicit `CREATE TYPE` for enums. Alembic usually handles this, but review carefully.
- **Dropping columns**: Alembic autogenerate may produce `drop_column` operations. Review these -- they are destructive and irreversible.
- **Renamed columns**: Alembic cannot detect renames -- it generates a drop + add instead. Handle renames manually if needed.
