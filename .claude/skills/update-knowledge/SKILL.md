---
name: update-knowledge
description: Review and update .claude/ configuration to reflect the current state of the project. Use after adding new domains, patterns, conventions, or when the user corrects an approach.
argument-hint: [topic]
---

# Update Project Knowledge

Review the `.claude/` configuration against the actual codebase and propose updates.

## Arguments

- `$0` (optional) -- Specific topic to update (e.g., "new payment domain", "error handling convention"). If omitted, do a full review.

## Step 1: Discover what exists now

Current entities:
!`find backend/domain/entities -name "*.py" -not -name "__init__.py" -not -path "*base*" -not -path "*__pycache__*" 2>/dev/null | sort`

Current handlers:
!`find backend/app/rest/v1/handlers -mindepth 2 -name "*.py" -not -name "__init__.py" -not -path "*base*" -not -path "*__pycache__*" 2>/dev/null | sort`

Current ports:
!`find backend/app/shared/ports -name "*.py" -not -name "__init__.py" -not -path "*__pycache__*" 2>/dev/null | sort`

Current events:
!`find backend/app/shared/events -name "*.py" -not -name "__init__.py" -not -name "base.py" -not -path "*__pycache__*" 2>/dev/null | sort`

Current controllers:
!`find backend/entry/rest/v1 -maxdepth 1 -name "*.py" -not -name "__init__.py" -not -path "*__pycache__*" 2>/dev/null | sort`

Recent git changes:
!`git log --oneline -15 2>/dev/null`

## Step 2: Compare against documented knowledge

Read each of these and check if they're still accurate:

1. `.claude/CLAUDE.md` — does the architecture section match reality? Any new patterns?
2. `.claude/rules/*.md` — do code examples still match current code? Any new conventions?
3. `.claude/skills/*/SKILL.md` — do the `!find` commands reflect current structure? Any new skill needed?
4. `.claude/agents/*.md` — do review checklists cover all current patterns?

## Step 3: Identify gaps

For each gap found, categorize it:

- **Stale**: documented but no longer true (renamed, removed, changed)
- **Missing**: exists in code but not documented
- **New pattern**: emerged from recent work, should be captured

## Step 4: Propose changes

For each update, present:

```markdown
### Update: {file path}

**Why**: {what changed and why the docs need updating}

**Current** (line N):
> {current text}

**Proposed**:
> {new text}
```

## Step 5: Apply approved changes

After the user approves, update the files. For each change:
1. Read the target file
2. Make the specific edit
3. Verify the file is consistent after the edit

## When to use this skill

- After implementing a new domain (entity + handlers + controller)
- After the user corrects your approach on something non-obvious
- After adding a new external integration
- After changing an established pattern
- Periodically (every few sessions) as a hygiene check
