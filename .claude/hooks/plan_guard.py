"""PostToolUse guard: reminds to run plan-reviewer after a plan file is written."""

from __future__ import annotations

import json
import sys

REMINDER = (
    "[plan-guard] Plan file written. "
    "Run plan-reviewer before implementing: "
    "the plan must pass plan-reviewer review before any code is written."
)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    tool_input = payload.get("tool_input") or {}
    file_path = str(tool_input.get("file_path") or tool_input.get("path") or "")

    if ".claude/plans/" in file_path:
        print(REMINDER)

    return 0


if __name__ == "__main__":
    sys.exit(main())
