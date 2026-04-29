"""PreToolUse guard: blocks edits to protected files.

Protected:
  - Existing alembic migrations (create new ones via `just migration "desc"`)
  - uv.lock (managed by `uv add/remove`)
  - .env* secrets (except .env.example)
  - Hook scripts themselves

Reads hook JSON from stdin. Exits 2 to block.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

FORBIDDEN = [
    r"^backend/infra/database/alembic/migrations/versions/.+\.py$",
    r"^uv\.lock$",
    r"^\.env(\..*)?$",
    r"^\.claude/hooks/.+\.py$",
]

ALLOWLIST = [
    r"^\.env\.(example|sample|template)$",
]


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    tool_input = payload.get("tool_input") or {}
    file_path = tool_input.get("file_path") or tool_input.get("path") or ""
    if not file_path:
        return 0

    cwd = payload.get("cwd") or ""
    try:
        rel = str(Path(file_path).resolve().relative_to(Path(cwd).resolve()))
    except (ValueError, OSError):
        rel = file_path

    for pattern in ALLOWLIST:
        if re.search(pattern, rel):
            return 0

    for pattern in FORBIDDEN:
        if re.search(pattern, rel):
            sys.stderr.write(
                f"[guard_paths] blocked edit to {rel}\n"
                f"  matched pattern: {pattern}\n"
                f'  hint: migrations -> `just migration "desc"`; '
                f"deps -> `uv add <pkg>`; secrets -> edit by hand outside Claude; "
                f"hooks -> protected from self-modification.\n"
            )
            return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
