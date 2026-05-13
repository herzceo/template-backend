---
name: task
description: Run a Linear task end-to-end — creates an isolated tmux session + worktree, starts a Claude agent to implement it, opens a PR, and watches for review feedback automatically.
argument-hint: <linear-task-id> [--interactive]
---

# Task — Linear Task Lifecycle

Orchestrates: Linear status → isolated worktree → tmux Claude agent → PR → automated review loop → cleanup.

## Arguments

- `$0` — Linear task ID (e.g., `MN-123`, `BE-456`)
- `$1` — (optional) `--interactive` — open the session so you can talk to the agent; omit for fully autonomous mode

## Modes

**Autonomous** (default): agent runs with `--dangerously-skip-permissions`, asks no questions, approves its own tool calls.

**Interactive** (`--interactive`): agent runs normally; you attach to the tmux session and can guide it. It still receives PR feedback notifications automatically.

---

## Step 1: Fetch the Linear issue

```
mcp__linear-server__get_issue(id: $0)
```

Extract: `title`, `team.id`, and label names. The description is not needed here — the agent will fetch it.

Determine branch type from labels (case-insensitive):
- "bug" or "fix" in any label → `fix`
- "chore" or "refactor" → `chore`
- default → `feature`

## Step 2: Fetch Linear status IDs

```
mcp__linear-server__list_issue_statuses(teamId: team.id)
```

Find IDs (case-insensitive name match):
- `todo_id` → "Todo" or "To Do"
- `in_progress_id` → "In Progress"
- `in_review_id` → "In Review" (fall back to `in_progress_id` if missing)
- `done_id` → "Done"
- `backlog_id` → "Backlog"

## Step 3: Build names

```bash
PROJECT_ROOT=$(git rev-parse --show-toplevel)

# slug: lowercase, spaces→hyphens, strip special chars, max 40 chars
SLUG=$(echo "{title}" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g; s/--*/-/g; s/^-//; s/-$//' | cut -c1-40)

REMOTE_BRANCH="{type}/{task-id}-$SLUG"          # e.g. feature/MN-123-add-role-permissions
LOCAL_BRANCH="worktree-$(echo $REMOTE_BRANCH | sed 's|/|+|g')"
WORKTREE_PATH="$PROJECT_ROOT/.claude/worktrees/$(echo $REMOTE_BRANCH | sed 's|/|+|g')"
TMUX_SESSION="claude-{task-id}"
STATE_FILE="$PROJECT_ROOT/.claude/tasks/{task-id}.json"
```

## Step 4: Set Linear → Todo

```
mcp__linear-server__save_issue(id: $0, stateId: todo_id)
```

## Step 5: Create worktree

```bash
mkdir -p "$PROJECT_ROOT/.claude/worktrees"
git worktree add "$WORKTREE_PATH" -b "$REMOTE_BRANCH"
```

## Step 6: Write initial state file

```bash
mkdir -p "$PROJECT_ROOT/.claude/tasks"
```

Write `$STATE_FILE`:
```json
{
  "task_id": "{task-id}",
  "tmux_session": "claude-{task-id}",
  "local_branch": "{LOCAL_BRANCH}",
  "remote_branch": "{REMOTE_BRANCH}",
  "worktree_path": "{WORKTREE_PATH}",
  "pr_number": null,
  "phase": "implementing",
  "status_ids": {
    "todo": "{todo_id}",
    "in_progress": "{in_progress_id}",
    "in_review": "{in_review_id}",
    "done": "{done_id}",
    "backlog": "{backlog_id}"
  },
  "last_comment_ids": [],
  "last_submitted_review_ids": [],
  "last_failed_check_ids": []
}
```

## Step 7: Create tmux session and start agent

```bash
tmux new-session -d -s "$TMUX_SESSION" -c "$WORKTREE_PATH"
```

Build the initial prompt (substitute all values before sending):

```
INITIAL_PROMPT="You are implementing Linear task {task-id}: \"{title}\".

Working directory: {WORKTREE_PATH}
Remote branch: {REMOTE_BRANCH}
State file (keep this updated): {STATE_FILE}

## Your implementation steps

1. Fetch the task description: mcp__linear-server__get_issue(id: {task-id})
2. Research the relevant domain — read existing handlers, repos, entities for this area of the codebase
3. Classify effort: mid (extending existing entity/handler) or tuff (new abstraction, new domain)
4. Implement in dependency order: entity → migration → repo → handler → controller → event → tests
5. Run \`just check\` after each major layer — fix all errors before continuing
6. Run \`just check\` until it passes completely clean

## After implementation

7. Commit: stage specific files only, message format \"{type}: {short summary}\"
8. Push: git push -u origin {LOCAL_BRANCH}:{REMOTE_BRANCH}
9. Create PR:
   gh pr create --title \"{type}: {title}\" --body \"## Linear task\\nhttps://linear.app/issue/{task-id}\\n\\n## Summary\\n...\\n\\n## Test plan\\n...\"
10. Update the state file at {STATE_FILE}: set pr_number to the PR number (integer), phase to \"review\"
11. Set Linear to In Review: mcp__linear-server__save_issue with stateId {in_review_id}
11. Wait — the PR watcher will notify you when there is review feedback

## When you receive a message about PR feedback

- Run: gh pr view {PR_NUMBER} --json reviews,comments
- Address all feedback
- Run \`just check\` until clean
- Commit and push
- Wait for further instructions

## When you receive a message that the PR was merged

1. Set Linear to Done: mcp__linear-server__save_issue with stateId {done_id}
2. Update {STATE_FILE}: set phase to \"done\"

## When you receive a message that the PR was closed without merging

1. Set Linear to Backlog: mcp__linear-server__save_issue with stateId {backlog_id}
2. Update {STATE_FILE}: set phase to \"done\"

Do not ask questions. Make reasonable decisions when things are ambiguous. Proceed."
```

**Autonomous mode** (no `--interactive`):
```bash
tmux send-keys -t "$TMUX_SESSION" "claude --dangerously-skip-permissions" Enter
sleep 5
tmux send-keys -t "$TMUX_SESSION" "$INITIAL_PROMPT"
sleep 1
tmux send-keys -t "$TMUX_SESSION" "" Enter
```

**Interactive mode** (`--interactive`):
```bash
tmux send-keys -t "$TMUX_SESSION" "claude" Enter
sleep 5
tmux send-keys -t "$TMUX_SESSION" "$INITIAL_PROMPT"
sleep 1
tmux send-keys -t "$TMUX_SESSION" "" Enter
```

## Step 8: Set Linear → In Progress

```
mcp__linear-server__save_issue(id: $0, stateId: in_progress_id)
```

## Step 9: Report to user

**Autonomous mode:**
> Task {task-id} is running autonomously in tmux session `claude-{task-id}`.
> Watch it: `tmux attach -t claude-{task-id}` (detach with Ctrl-b d)
> If the PR watcher isn't running yet, start it: `just pr-watcher`

**Interactive mode:**
> Task {task-id} is ready. Open a new terminal tab and run:
> `tmux attach -t claude-{task-id}`
> If the PR watcher isn't running yet, start it: `just pr-watcher`

---

## Error handling

- `git worktree add` fails (branch exists) → check if task already running; if so, report and stop
- Linear status name not found → ask user for the exact status name their team uses
- tmux not installed → report and stop; tmux is required for this skill
- Watcher fails to start → report the log path (`{task-id}-watcher.log`) for debugging
