---
name: impl
description: Implement a change with a pipeline scaled to its complexity. Single entry point for all code changes — auto-detects effort or accepts small|mid|large override.
argument-hint: [small|mid|large] <description>
---

# Implement a Change

Single entry point for all code changes. Select effort explicitly or let Claude auto-detect from the request.

## Arguments

- `$0` -- (optional) Effort tier override: `small`, `mid`, or `large`. Omit to auto-detect.
- All remaining words form the change description.

## Effort Tiers

| Tier | Scope | Pipeline |
|------|-------|----------|
| `small` | 1–2 files, modifying existing logic, no new abstractions | Read → 1 question max → implement → `just check` |
| `mid` | Existing pattern, chain of `/add-*` skills, 3–8 files | Quick research → chain `/add-*` skills in order → `just check` |
| `large` | New domain, new abstractions, or no prior pattern to follow | Full pipeline: questions → research → plan → plan-review → user-approval → implement → verifier |

## Auto-Detection Rules

Choose **large** if any of:
- New entity or Alembic migration is required
- New port, adapter, repo, or event (new abstraction, not adding to an existing one)
- No existing `/add-*` skill covers the task
- Request says "new domain", "from scratch", "design", or "architect"

Choose **mid** if any of:
- Existing entity is being extended with new behavior (new handler, new endpoint, new event)
- One or more `/add-*` skills directly match the task
- 3–8 files touched, all following established patterns

Choose **small** if all of:
- Scoped to 1–2 existing files
- No new files, no new abstractions
- Modifying a value, condition, field, or small logic block

When ambiguous between mid and large, choose **mid**. When ambiguous between small and mid, choose **mid**.

## small pipeline

1. Read the file(s) involved.
2. If something is genuinely ambiguous, ask at most one clarifying question. Otherwise proceed immediately.
3. Make the change.
4. Run `just check`. Fix any issues before reporting done.

No planning. No agents. No approval step.

## mid pipeline

1. Identify which `/add-*` skills apply (e.g., `/add-handler` + `/add-endpoint` + `/add-test`).
2. Run `/research <domain>` to confirm existing patterns — never invent structure when an example already exists.
3. Execute the identified `/add-*` skills in dependency order: entity before repo, repo before handler, handler before controller, then tests.
4. Run `just check`. Fix all issues.
5. Delegate to **implementation-verifier** agent — fix any drift before reporting the task done.

No plan file. No approval step.

## large pipeline

Follow the full workflow — no steps may be skipped:

1. Ask clarifying questions: business rules, scope, data model, side effects, error cases, naming
2. Run `/research <topic>` — read all relevant existing code thoroughly
3. Run `/plan <feature>` — produce the structured plan with every file, field, method signature
4. Delegate to **plan-reviewer** agent — fix every gap it reports before proceeding
5. Present the reviewed plan to the user — wait for explicit approval; never infer it
6. Implement in dependency order — run `just check` after each major step; do not deviate from the plan without asking
7. Delegate to **implementation-verifier** agent — fix any drift before reporting the task done
8. Delegate to **architecture-reviewer** agent — fix any layer violations or pattern drift before reporting done
