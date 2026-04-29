---
name: research
description: Thoroughly investigate a part of the codebase before making changes. Use to understand existing patterns, trace data flows, and find reusable code.
argument-hint: <topic-or-area>
---

# Research the Codebase

Investigate a topic thoroughly. Read files, trace flows, find patterns. No code is written.

## Arguments

- `$0` -- Topic or area to research (e.g., "auth flow", "how events work", "user entity and its handlers")

## Investigation Checklist

### 1. Map the domain

Find all files related to the topic:

- Entities: `find backend/domain/entities -name "*.py"` — read relevant ones
- Repos: `find backend/domain/repos -name "*.py"` — read Protocol interfaces
- Handlers: `find backend/app/rest/v1/handlers -name "*.py"` — read use cases
- Controllers: `find backend/entry/rest/v1 -name "*.py"` — read HTTP routes
- Events: `find backend/app/shared/events -name "*.py"` — read event definitions
- Ports: `find backend/app/shared/ports -name "*.py"` — read abstractions
- DTOs: `find backend/app/rest/v1/dtos -name "*.py"` — read response shapes

### 2. Trace a full request flow

Pick a representative endpoint and trace it from HTTP to database:

1. **Controller** — which route, what decorators, how params are converted
2. **Handler** — what command fields, what dependencies, what logic
3. **Service** — if used, what it orchestrates
4. **Repository** — what queries, what Option wrapping
5. **Entity** — what columns, what relationships
6. **Events** — if published, what event handler does

### 3. Identify reusable patterns

- Existing DTOs that can be extended
- Existing services that already handle related logic
- Existing ports that cover the needed capability
- Existing base classes and mixins

### 4. Note gaps

- Missing repo methods that will be needed
- Missing DTOs for new response shapes
- Missing ports for new external capabilities
- Missing DI wiring

## Output Format

```markdown
# Research: {topic}

## Existing Components
- {component}: {file path} — {what it does}
- ...

## Data Flow
{controller} -> {handler} -> {service?} -> {repo} -> {entity}
                                         -> {event?} -> {event handler}

## Patterns to Reuse
- {pattern}: {file path} — {why it's relevant}
- ...

## Gaps
- {what's missing}: {where it should go}
- ...

## Recommendations
- {suggestion for implementation approach}
```
