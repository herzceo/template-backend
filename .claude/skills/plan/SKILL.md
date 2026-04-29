---
name: plan
description: Produce a detailed implementation plan for a feature. MUST be used before implementing any non-trivial change. Outputs a structured plan — does NOT write code.
argument-hint: <feature-description>
---

# Plan a Feature

Produce a complete, reviewable implementation plan. No code is written.

## Arguments

- `$0` -- Feature description (e.g., "add invoice domain with PDF generation and email delivery")

## Step 1: Understand — ask questions FIRST

Before doing ANY research, identify what you don't know. Ask the user about:

- **Business rules**: what are the exact requirements? what happens on edge cases?
- **Scope**: which endpoints? what auth level? which users can access this?
- **Data model**: what fields? what relationships to existing entities? what constraints?
- **Side effects**: should events be published? emails sent? analytics tracked?
- **Error cases**: what should happen on invalid input? not found? conflict?
- **Naming**: what should entities/endpoints/events be called?

Ask at least 3 clarifying questions. Wait for answers before proceeding.

## Step 2: Research existing code

After questions are answered, explore the codebase:

```
What entities exist that relate to this feature?
```
!`find backend/domain/entities -name "*.py" -not -name "__init__.py" -not -path "*base*" -not -path "*__pycache__*" 2>/dev/null | sort`

```
What handlers exist in the target domain?
```
!`find backend/app/rest/v1/handlers -mindepth 1 -name "*.py" -not -name "__init__.py" -not -path "*base*" -not -path "*__pycache__*" 2>/dev/null | sort`

```
What ports exist?
```
!`find backend/app/shared/ports -name "*.py" -not -name "__init__.py" -not -path "*__pycache__*" 2>/dev/null | sort`

```
What events exist?
```
!`find backend/app/shared/events -name "*.py" -not -name "__init__.py" -not -name "base.py" -not -path "*__pycache__*" 2>/dev/null | sort`

Read the relevant existing files to understand current patterns and what can be reused.

## Step 3: Produce the plan

Output a structured plan in this exact format:

```markdown
# Plan: {Feature Name}

## Summary
{1-2 sentences describing the feature}

## Questions Resolved
- Q: {question} -> A: {answer from user}
- ...

## Components (in implementation order)

### 1. Entity: {EntityName}
- File: backend/domain/entities/{name}.py
- Mixins: WithUUIDID, WithTime, ...
- Columns:
  - {field}: Mapped[{type}] ({constraints})
  - ...
- Relationships: {description}
- Migration message: "{description}"

### 2. Repository: {Entity}Repo
- Protocol: backend/domain/repos/{name}.py
- Impl: backend/infra/database/psql/repos/{name}.py
- Base: CRUDSupported[{Entity}]
- Custom methods:
  - get_by_{field}({field}: {type}) -> Option[{Entity}]
  - ...
- Gateway property name: {name}

### 3. Port: {PortName} (if needed)
- Protocol: backend/app/shared/ports/{category}/{name}.py
- Methods:
  - {method}({params}) -> {return_type}
- Adapter: backend/infra/external/adapters/{name}.py
- Impl class: Impl{Detail}{PortName}

### 4. Event: {EventName} (if needed)
- Definition: backend/app/shared/events/v1/{name}.py
- name: "{snake_case_name}"
- Payload: {field}: {type}, ...
- Triggered by: {which handler}
- Event handler: backend/app/events/v1/handlers/{domain}/{name}.py
- Side effect: {what it does}

### 5. Service: {Name}Service (if needed)
- File: backend/app/rest/v1/services/{name}.py
- Methods:
  - {method}({params}) -> {return_type}
- Dependencies: {list}

### 6. Handler: {Action}{Entity}Handler
- File: backend/app/rest/v1/handlers/{domain}/{action}.py
- Command fields: {field}: {type}, ...
- Type: HandlerType.READ | WRITE
- Response DTO: dtos.{Entity} | None
- Dependencies: db, {service}, {port}, ...
- Logic:
  1. {step}
  2. {step}
  3. ...
- Error cases:
  - {condition} -> {ErrorType}(message="{message}")

### 7. DTO: {Entity} (if new)
- File: backend/app/rest/v1/dtos/{domain}.py
- Fields: {field}: {type}, ...

### 8. Controller method
- File: backend/entry/rest/v1/{domain}.py
- Method: {http_method} /{path}
- Auth: required | exclude_from_auth=True
- Path params: {param}: {type} (converted from str)
- Body: {CommandType} | {EntryDTO}

### 9. DI Wiring (if needed)
- File: backend/entry/rest/main/ioc.py
- New providers or bindings needed

## Files Created/Modified (checklist)
- [ ] backend/domain/entities/{name}.py (CREATE)
- [ ] backend/domain/entities/__init__.py (MODIFY — add export)
- [ ] backend/domain/repos/{name}.py (CREATE)
- [ ] backend/domain/repos/gateway.py (MODIFY — add property)
- [ ] ...

## Verification
- [ ] `just check` passes
- [ ] New endpoints appear in OpenAPI schema
- [ ] {specific test scenario}
```

## Step 4: Wait for approval

Present the plan and explicitly ask: "Does this plan look correct? Any changes before I implement?"

Do NOT proceed to implementation until the user approves.
