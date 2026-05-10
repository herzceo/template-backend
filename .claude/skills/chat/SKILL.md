---
name: chat
description: Design consultation — explore approaches, trade-offs, and patterns before committing to an implementation. No code written. Outputs a structured comparison and a recommended next step.
argument-hint: <topic-or-problem>
---

# Design Consultation

Think through a design problem before picking an approach. No code is written. Output is a structured comparison of options and a concrete recommendation tied to the user's priorities.

## Arguments

- `$0` -- Topic or problem (e.g., "how to model multi-tenancy in billing", "whether to use events or direct service calls for profile sync")

## Step 1: Clarify context

Before researching anything, ask:

1. **Priority axis**: speed to ship vs. long-term maintainability — where does this sit?
2. **Scale and lifespan**: expected load, team size, how long this code will be owned and evolved?
3. **Integration constraints**: what must not break? Which existing decisions are fixed?

Wait for answers. Do not proceed to Step 2 on assumption.

## Step 2: Research the codebase

Run `/research <topic>` to establish:
- What patterns already handle similar problems in this codebase
- What the layer boundaries and DI approach imply about the decision
- What downstream code would be affected by each option

## Step 3: Survey established approaches

Draw from design literature based on what the problem class is:

- **Domain-Driven Design (Evans)**: bounded contexts, aggregates, domain events, repositories — relevant for modeling problems and aggregate boundaries
- **Clean Architecture (Martin)**: dependency rule, use-case layer, port/adapter isolation — relevant for coupling and layering decisions
- **CQRS**: separate read and write models — relevant when read and write patterns diverge; note this project already uses query services for reads
- **Event-driven design**: async side effects via published events — relevant for cross-domain decoupling; note this project has a PostgreSQL-backed job queue
- **Simple CRUD**: sometimes the boring answer is correct — relevant when the domain is stable and the scope is small

For each candidate approach, evaluate:
- What it optimizes for
- What it costs (complexity, new abstractions, migration effort)
- Whether an existing file in the codebase already demonstrates this pattern

## Step 4: Present options

Output this structure — no freeform prose:

```markdown
# Design: {topic}

## Context
{User's stated priorities and constraints}

## Codebase baseline
{Relevant existing pattern + file path, or "no prior art"}

## Option A: {Name}
**Approach**: {1–2 sentences}
**Fits existing patterns**: yes | partial | no — {reason}
**Trade-offs**:
- Pro: {benefit}
- Con: {cost}

## Option B: {Name}
**Approach**: {1–2 sentences}
**Fits existing patterns**: yes | partial | no — {reason}
**Trade-offs**:
- Pro: {benefit}
- Con: {cost}

## Recommendation
**Option {X}** — {1–2 sentences tied directly to the user's stated priority axis}

## Next step
{One of: `/impl large <feature>`, `/impl mid <feature>`, `/plan <feature>`, or "discuss more before deciding"}
```

## What NOT to do

- Do not write code or implementation plans — this is exploration only
- Do not recommend an option without tying it to the user's priorities from Step 1
- Do not present more than 3 options — pick the realistic ones
- Do not skip Step 1 — recommendations without stated priorities are noise
