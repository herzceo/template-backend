"""Background PR watcher for /task lifecycle.

Polls GitHub every 60 s for all active tasks. Notifies each Claude agent in its
tmux session when new review activity is detected. Handles merged/closed cleanup.

Usage: python pr-watcher.py
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any


POLL_INTERVAL = 60
CLEANUP_GRACE = 120  # seconds for agent to finish Linear update before force-cleanup


def project_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, check=True,
    )
    return Path(result.stdout.strip())


def active_tasks(tasks_dir: Path) -> list[dict[str, Any]]:
    tasks = []
    for path in sorted(tasks_dir.glob("*.json")):
        try:
            state = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        if state.get("phase") in ("implementing", "review") and state.get("pr_number"):
            tasks.append(state)
    return tasks


def send_to_session(session: str, message: str) -> None:
    subprocess.run(["tmux", "send-keys", "-t", session, message], check=False)
    subprocess.run(["tmux", "send-keys", "-t", session, "", "Enter"], check=False)
    print(f"[watcher] → {session}: {message[:80]}", flush=True)


def gh_pr(pr_number: int, fields: str) -> dict[str, Any]:
    result = subprocess.run(
        ["gh", "pr", "view", str(pr_number), "--json", fields],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return {}
    try:
        data: dict[str, Any] = json.loads(result.stdout)
        return data
    except json.JSONDecodeError:
        return {}


_FAILING_CONCLUSIONS = {"FAILURE", "TIMED_OUT", "STARTUP_FAILURE", "ACTION_REQUIRED"}
_IN_PROGRESS_STATUSES = {"QUEUED", "IN_PROGRESS", "WAITING", "PENDING"}


def new_activity(pr: dict[str, Any], state: dict[str, Any]) -> bool:
    last_comments = set(state.get("last_comment_ids", []))
    last_reviews = set(state.get("last_submitted_review_ids", []))

    current_comments = {c["id"] for c in pr.get("comments", [])}
    submitted_reviews = [
        r for r in pr.get("reviews", [])
        if r.get("state") not in ("PENDING", "DISMISSED")
    ]
    current_reviews = {r["id"] for r in submitted_reviews}

    return bool(
        (current_comments - last_comments) or (current_reviews - last_reviews)
    )


def _failed_checks(pr: dict[str, Any]) -> list[dict[str, Any]]:
    checks = pr.get("statusCheckRollup", [])
    if any(c.get("status") in _IN_PROGRESS_STATUSES for c in checks):
        return []
    return [
        c for c in checks
        if c.get("status") == "COMPLETED" and c.get("conclusion") in _FAILING_CONCLUSIONS
    ]


def new_check_failures(pr: dict[str, Any], state: dict[str, Any]) -> list[dict[str, Any]]:
    seen = set(state.get("last_failed_check_ids", []))
    return [
        c for c in _failed_checks(pr)
        if f"{c['name']}:{c.get('completedAt', '')}" not in seen
    ]


def update_seen(state: dict[str, Any], pr: dict[str, Any], state_file: Path) -> None:
    state["last_comment_ids"] = [c["id"] for c in pr.get("comments", [])]
    state["last_submitted_review_ids"] = [
        r["id"] for r in pr.get("reviews", [])
        if r.get("state") not in ("PENDING", "DISMISSED")
    ]
    state["last_failed_check_ids"] = [
        f"{c['name']}:{c.get('completedAt', '')}" for c in _failed_checks(pr)
    ]
    state_file.write_text(json.dumps(state, indent=2))


def wait_for_phase_done(state_file: Path, timeout: int) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if json.loads(state_file.read_text()).get("phase") == "done":
                return
        except (json.JSONDecodeError, OSError):
            return  # file gone = agent cleaned up already
        time.sleep(5)


def cleanup(state: dict[str, Any], state_file: Path, *, delete_remote: bool = False) -> None:
    session = state.get("tmux_session", "")
    worktree = state.get("worktree_path", "")
    branch = state.get("local_branch", "")
    remote_branch = state.get("remote_branch", "")
    task_id = state.get("task_id", "?")

    if session:
        subprocess.run(["tmux", "kill-session", "-t", session], check=False)
        print(f"[watcher] killed tmux session {session}", flush=True)

    if worktree:
        subprocess.run(["git", "worktree", "remove", "--force", worktree], check=False)
        print(f"[watcher] removed worktree {worktree}", flush=True)

    if branch:
        subprocess.run(["git", "branch", "-D", branch], capture_output=True, check=False)

    if delete_remote and remote_branch:
        subprocess.run(
            ["git", "push", "origin", "--delete", remote_branch],
            capture_output=True, check=False,
        )
        print(f"[watcher] deleted remote branch {remote_branch}", flush=True)

    state_file.unlink(missing_ok=True)
    print(f"[watcher] cleanup complete for {task_id}", flush=True)


def check_task(state: dict[str, Any], tasks_dir: Path) -> None:
    task_id = state["task_id"]
    pr_number = state["pr_number"]
    session = state["tmux_session"]
    state_file = tasks_dir / f"{task_id}.json"

    pr = gh_pr(pr_number, "state,reviews,comments,statusCheckRollup")
    if not pr:
        return

    pr_state = pr.get("state", "")

    if pr_state == "MERGED":
        print(f"[watcher] {task_id}: PR #{pr_number} merged", flush=True)
        send_to_session(
            session,
            f"PR #{pr_number} has been merged! "
            f"Please set Linear task {task_id} to Done using mcp__linear-server__save_issue, "
            f'then update {state_file} setting phase to "done".',
        )
        wait_for_phase_done(state_file, CLEANUP_GRACE)
        try:
            final_state = json.loads(state_file.read_text())
        except (json.JSONDecodeError, OSError):
            final_state = state
        cleanup(final_state, state_file)
        return

    if pr_state == "CLOSED":
        print(f"[watcher] {task_id}: PR #{pr_number} closed without merging", flush=True)
        send_to_session(
            session,
            f"PR #{pr_number} was closed without merging. "
            f"Please set Linear task {task_id} to Backlog using mcp__linear-server__save_issue, "
            f'then update {state_file} setting phase to "done".',
        )
        wait_for_phase_done(state_file, CLEANUP_GRACE)
        try:
            final_state = json.loads(state_file.read_text())
        except (json.JSONDecodeError, OSError):
            final_state = state
        cleanup(final_state, state_file, delete_remote=True)
        return

    failures = new_check_failures(pr, state)
    if failures:
        names = ", ".join(c["name"] for c in failures)
        print(f"[watcher] {task_id}: failing checks on PR #{pr_number}: {names}", flush=True)
        send_to_session(
            session,
            f"PR #{pr_number} has failing CI checks: {names}. "
            f"Run `gh pr checks {pr_number}` to see details, fix the failures, "
            f"then commit and push.",
        )
        update_seen(state, pr, state_file)
    elif new_activity(pr, state):
        print(f"[watcher] {task_id}: new activity on PR #{pr_number}", flush=True)
        send_to_session(
            session,
            f"PR #{pr_number} has new review feedback. "
            f"Check it with `gh pr view {pr_number} --json reviews,comments` "
            f"and address all feedback. Commit and push when done.",
        )
        update_seen(state, pr, state_file)
    else:
        print(f"[watcher] {task_id}: no new activity", flush=True)


def main() -> None:
    root = project_root()
    tasks_dir = root / ".claude" / "tasks"

    print(f"[watcher] started (PID {os.getpid()}), watching {tasks_dir}", flush=True)

    while True:
        tasks = active_tasks(tasks_dir)

        if not tasks:
            print("[watcher] no active tasks with a PR. sleeping.", flush=True)
        else:
            for state in tasks:
                try:
                    check_task(state, tasks_dir)
                except Exception as e:
                    print(f"[watcher] error on {state.get('task_id', '?')}: {e}", flush=True)

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
